from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired

class InputForm(FlaskForm):
    yt_id = StringField('Youtube ID', validators=[InputRequired()])
    submit = SubmitField('Submit')

from app import YOUTUBE


class YoutubeVideo:
    def __init__(self, id):
        self.id = id
        request = YOUTUBE.videos().list(part='id,snippet,statistics', id=self.id)
        self.response = request.execute()

    def valid_id(self):
        return self.response['items']

    def too_many_comments(self):
        return int(self.response['items'][0]['statistics']['commentCount']) > 18000
        
    def no_comments(self):
        return int(self.response['items'][0]['statistics']['commentCount']) == 0

    def get_details(self):
        # thumbnail url, channel name, video title, comment count
        return (self.response['items'][0]['snippet']['thumbnails']['maxres']['url'],
                self.response['items'][0]['snippet']['channelTitle'],
                self.response['items'][0]['snippet']['title'],
                self.response['items'][0]['statistics']['commentCount'])