from flask import render_template, jsonify, Response, url_for, redirect, request, session
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app import app, CLIENT_SECRETS_FILE, SCOPES, API_SERVICE_NAME, API_VERSION
from app.input import InputForm, YoutubeVideo
import app as init
import time

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

yt = None
@app.route('/', methods=['GET', 'POST'])
def index():
    global yt

    form = InputForm()
    if form.validate_on_submit():
        time.sleep(1) # delay so the loading animation is shown long enough
        yt = YoutubeVideo(form.yt_id.data)
        # display error
        if not yt.valid_id():
            return jsonify({'error': 'Invalid YouTube video URL. Please enter a valid one.'})
        elif yt.comments_disabled():
            return jsonify({'error': 'Video has comments disabled. Please pick another video.'})
        elif yt.no_comments():
            return jsonify({'error': 'Video has no comments. Please pick another video.'})
        elif yt.too_many_comments():
            return jsonify({'error': 'Video has too many comments (>18000). Please pick another video.'})
        # get details
        else:
            thumbnail_src, ch_name, vid_title, comment_count = yt.get_details()
            return jsonify({'output': [thumbnail_src, ch_name, vid_title, comment_count]})

    return render_template('index.html', form=form)

@app.route('/process', methods=['GET','POST'])
def process():
    global yt

    credentials = Credentials(**session['credentials'])
    session['credentials'] = credentials_to_dict(credentials)
    init.youtube = build(
        API_SERVICE_NAME,
        API_VERSION,
        developerKey=app.config['API_KEY'],
        credentials=credentials
    )

    return Response(yt.comment_threads(), mimetype='text/event-stream')

@app.route('/authorize')
def authorize():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES, 
        state=state
    )
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    flow.fetch_token(authorization_response=request.url)
    session['credentials'] = credentials_to_dict(flow.credentials)

    return redirect(url_for('index'))

@app.route('/clear')
def clear_credentials():
    if 'credentials' in session:
        del session['credentials']
    
    return redirect(url_for('index'))