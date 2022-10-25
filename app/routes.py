from flask import render_template, jsonify, Response
from app import app
from app.input import InputForm, YoutubeVideo
import time

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
    return Response(yt.comment_threads(), mimetype='text/event-stream')