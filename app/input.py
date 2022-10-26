import sys
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired
from app import YOUTUBE
import regex as re

class InputForm(FlaskForm):
    yt_id = StringField('Youtube ID', validators=[InputRequired()])
    submit = SubmitField('Submit')

def extract_id(s):
    regex_pattern = re.compile(r'(?<=watch\?v=|&v=|youtu.be/|/embed/|/[v|e]/|Fv%3D)([A-Za-z0-9-_]){11}')
    match = re.search(regex_pattern, s.split()[0])
    return '' if match == None else match.group()

class YoutubeVideo:
    def __init__(self, id):
        self.id = extract_id(id)
        request = YOUTUBE.videos().list(part='id,snippet,statistics', id=self.id)
        requested = request.execute()
        try:
            self.response = requested['items'][0]
        except IndexError:
            self.response = None

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
            yield f"data: {{'progress': '{len(self.comments)}', 'done': 'false'}}\n\n"

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
        self.comments = []
        # get comments
        request = YOUTUBE.commentThreads().list(
            part='snippet,replies',
            videoId=self.id,
            maxResults=100
        )
        response = request.execute()
        yield from self.process_comments(response['items'])

        # get the rest of the comments
        while response.get('nextPageToken', None):
            request = YOUTUBE.commentThreads().list(
                part='snippet,replies',
                videoId=self.id,
                maxResults=100,
                pageToken=response['nextPageToken']
            )
            response = request.execute()
            yield from self.process_comments(response['items'])

        yield f"data: {{'progress': '{len(self.comments)}', 'done': 'true'}}\n\n"