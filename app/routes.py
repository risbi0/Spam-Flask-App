from flask import render_template, jsonify
from app import app
from app.input import InputForm, YoutubeVideo

@app.route('/', methods=['GET', 'POST'])
def index():
    form = InputForm()
    if form.validate_on_submit():
        yt = YoutubeVideo(form.yt_id.data)
        # display error
        if not yt.valid_id():
            return jsonify({'output': None, 'error': 'Invalid ID.'})
        elif yt.too_many_comments():
            return jsonify({'output': None, 'error': 'Video has too many comments (>18000). Please pick another video.'})
        elif yt.no_comments():
            return jsonify({'output': None, 'error': 'Video has no comments. Please pick another video.'})
        # get details
        else:
            thumbnail_src, ch_name, vid_title, comment_count = yt.get_details()
            return jsonify({'output': [thumbnail_src, ch_name, vid_title, comment_count], 'error': None})

    return render_template('index.html', form=form)