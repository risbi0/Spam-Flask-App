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
    if match == None:
        return ''
    else:
        return match.group()

class YoutubeVideo:
    def __init__(self, id):
        self.id = extract_id(id)
        request = YOUTUBE.videos().list(part='id,snippet,statistics', id=self.id)
        self.response = request.execute()

    def valid_id(self):
        return self.response['items']

    def comments_disabled(self):
        return 'commentCount' not in self.response['items'][0]['statistics']

    def no_comments(self):
        return int(self.response['items'][0]['statistics']['commentCount']) == 0
    
    def too_many_comments(self):
        return int(self.response['items'][0]['statistics']['commentCount']) > 18000    

    def get_details(self):
        # old video thumbnail fallback
        if 'maxres' not in self.response['items'][0]['snippet']['thumbnails']:
            thumbnail_url = self.response['items'][0]['snippet']['thumbnails']['high']['url']
        else:
            thumbnail_url = self.response['items'][0]['snippet']['thumbnails']['maxres']['url']
        # thumbnail url, channel name, video title, comment count
        return (thumbnail_url,
                self.response['items'][0]['snippet']['channelTitle'],
                self.response['items'][0]['snippet']['title'],
                self.response['items'][0]['statistics']['commentCount'])