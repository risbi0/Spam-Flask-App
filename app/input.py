from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired
from tensorflow.keras.models import load_model
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from app import YOUTUBE
from time import time
import regex as re
import pandas as pd

yt_vid_id = re.compile(r'(?<=watch\?v=|&v=|youtu.be/|/embed/|/[v|e]/|Fv%3D)([A-Za-z0-9-_]){11}')
wordnet_lemmatizer = WordNetLemmatizer()
model = load_model('spam_detector')

class InputForm(FlaskForm):
    yt_id = StringField('Youtube ID', validators=[InputRequired()])
    submit = SubmitField('Submit')

def extract_id(s):
    match = re.search(yt_vid_id, s.split()[0])
    return '' if match == None else match.group()
    
def check_time(start):
    return time() - start > 20

class YoutubeVideo:
    def __init__(self, id):
        self.id = extract_id(id)
        request = YOUTUBE.videos().list(part='id,snippet,statistics', id=self.id)
        requested = request.execute()
        try:
            self.response = requested['items'][0]
        except IndexError:
            self.response = None
        self.once = True
        self.comments = []
        self.comment_response = self.last_token = None

    def valid_id(self):
        return self.response

    def comments_disabled(self):
        return 'commentCount' not in self.response['statistics']

    def no_comments(self):
        return int(self.response['statistics']['commentCount']) == 0
    
    def too_many_comments(self):
        return int(self.response['statistics']['commentCount']) > 18000    

    def get_details(self):
        # old video thumbnail fallback
        if 'maxres' not in self.response['snippet']['thumbnails']:
            thumbnail_url = self.response['snippet']['thumbnails']['high']['url']
        else:
            thumbnail_url = self.response['snippet']['thumbnails']['maxres']['url']
        # thumbnail url, channel name, video title, comment count
        return (thumbnail_url,
                self.response['snippet']['channelTitle'],
                self.response['snippet']['title'],
                self.response['statistics']['commentCount'])

    def process_replies(self, response_items):
        for response in response_items:
            comment = {}
            comment['id'] = response['id']
            comment['comment'] = response['snippet']['textOriginal']
            self.comments.append(comment)
            yield f"data: {{'desc': 'Extracting comments...', \
                            'progress': '{len(self.comments)}', \
                            'repeat': 'False'}}\n\n"

    def process_comments(self, response_items):
        for response in response_items:
            # top level comment
            comment = {}
            comment['id'] = response['snippet']['topLevelComment']['id']
            comment['comment'] = response['snippet']['topLevelComment']['snippet']['textOriginal']
            self.comments.append(comment)
            # check for replies
            if 'replies' in response.keys():
                parent_id = response['snippet']['topLevelComment']['id']
                request = YOUTUBE.comments().list(
                    part='snippet',
                    parentId=parent_id,
                    maxResults=100
                )
                response = request.execute()
                yield from self.process_replies(response['items'])

                # get the rest of the replies (for >100 replies)
                while response.get('nextPageToken', None):
                    request = YOUTUBE.comments().list(
                        part='snippet',
                        parentId=parent_id,
                        maxResults=100,
                        pageToken=response['nextPageToken']
                    )
                    response = request.execute()
                    yield from self.process_replies(response['items'])

    def comment_threads(self):
        start = time()
        if self.once:
            self.once = False
            # get comments
            request = YOUTUBE.commentThreads().list(
                part='snippet,replies',
                videoId=self.id,
                maxResults=100
            )
            self.comment_response = request.execute()
            yield from self.process_comments(self.comment_response['items'])

        # get the rest of the comments
        while self.comment_response.get('nextPageToken', None):
            self.last_token = self.comment_response['nextPageToken']
            if check_time(start): break

            request = YOUTUBE.commentThreads().list(
                part='snippet,replies',
                videoId=self.id,
                maxResults=100,
                pageToken=self.last_token
            )
            self.comment_response = request.execute()
            yield from self.process_comments(self.comment_response['items'])
            
        yield f"data: {{'desc': 'Extracting comments...', \
                        'progress': '{len(self.comments)}', \
                        'repeat': '{check_time(start)}'}}\n\n"

        if self.comment_response.get('nextPageToken') == None:
            pc = ProcessComments(self.comments)
            yield from pc.identifySpam()

class ProcessComments:
    def __init__(self, comments):
        self.df = pd.DataFrame.from_records(comments)
        #self.df=self.df.reset_index(drop=True)
        self.progress = 0
        #self.start = time()

    def removeEmojis(self, text):
        pattern = re.compile(
            pattern = "["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags = re.UNICODE)
        return pattern.sub(r'', str(text))

    def hasOnlyLatinCharsOrArabicNumerals(self, text):
        try:
            text.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return ''
        else:
            return text

    def analyze(self):
        self.df['score'] = ''
        for _ in range(len(self.df)):
            '''
            Preprocessing:
            - transform to lowercase
            - remove links and mentions
            - remove all characters except whitespaces and latin characters
            - word tokenization
            - lemmatization
            '''
            removed_mentions = re.sub(r'\s?@(\s)*(\S*)\s?', ' ', self.df['comment'][self.progress])
            removed_links = re.sub(r'((http|watch\?v=|[wW]{3})\S+)', ' ', removed_mentions)
            normalized = re.sub(r'[^A-Za-z]+', ' ', removed_links)
            tokens = word_tokenize(normalized)
            tokens = [word for word in tokens if not word in stopwords.words('english')]
            final = ' '.join(tokens).lower()
            # score outputs using model
            score = round(model.predict([final], verbose=0)[0][0] * 100, 2)

            self.df['score'][self.progress] = score
            self.progress += 1
            
            yield f"data: {{'desc': '{len(self.df)} applicable comments found. Preprocessing and scoring...', \
                            'progress': '{self.progress}', \
                            'display_total_num': '', \
                            'total_num': '{len(self.df)}'}}\n\n"

    def identifySpam(self):
        yield f"data: {{'desc': 'Extracting applicable comments...', \
                        'progress': '{len(self.df)}'}}\n\n"
        # remove emojis
        self.df['comment'] = self.df['comment'].apply(lambda s: self.removeEmojis(s))
        # remove comments with non-latin alphabets or arabic numerals
        self.df['comment'] = self.df['comment'].apply(lambda s: self.hasOnlyLatinCharsOrArabicNumerals(s))
        # remove empty comments
        self.df = self.df.replace('', float('NaN')).dropna()
        self.df.reset_index(drop=True, inplace=True)

        yield from self.analyze()

        # convert dataframe that can be read as an object by javascript
        #spam = self.df[self.df['score'] >= 90]
        #dict_list = f'{spam.to_dict()}'.split(' ')
        dict_list = f'{self.df.to_dict()}'.split(' ')
        for index, item in enumerate(dict_list):
            if item[-1] == ':':
                if item[0] == '{':
                    dict_list[index] = '{' + "\"{0}\":".format(item[1:-1].replace("'", ''))
                else:
                    dict_list[index] = "\"{0}\":".format(item[:-1].replace("'", ''))

        output = ' '.join(dict_list)

        yield f"data: {{'desc': 'Done.', \
                        'progress': '{len(self.df)}', \
                        'output' : {output}, \
                        'done': 'True'}}\n\n"
        self.df.to_csv('z.csv',index=False)
        
        # todo: serve console in browser
        '''
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', ["https://www.googleapis.com/auth/youtube.force-ssl"])
        credentials = flow.run_console()
        youtube = build('youtube', 'v3', credentials=credentials)
        '''

        for id in self.df[self.df['score'] >= 90]['id']:
            #request = youtube.comments().markAsSpam(id=id)
            #request.execute()
            pass