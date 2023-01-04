from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config import Config
from googleapiclient.discovery import build
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config.from_object(Config)
CSRFProtect(app)
CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
youtube = build(API_SERVICE_NAME, API_VERSION, developerKey=app.config['API_KEY'])

from app import routes