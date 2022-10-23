from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config import Config
from googleapiclient.discovery import build

app = Flask(__name__)
app.config.from_object(Config)
CSRFProtect(app)
YOUTUBE = build('youtube', 'v3', developerKey=app.config['API_KEY'])

from app import routes