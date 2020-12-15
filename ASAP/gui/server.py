import json
import os
from functools import wraps

from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import webview

# NOT USING CSRF TOKENS FOR SIMPLICITY
# REFERENCES
# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
# https://github.com/r0x0r/pywebview/tree/master/examples/flask_app

app = Flask(__name__, static_folder='./assets', template_folder='./templates')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching
UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Render index.html. Initialization is performed asynchronously in initialize() function
    """
    error_msg = None
    if request.method == 'POST':
        file = request.files['csv_file']
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return select_column_type(file, file.filename)
        else:
            error_msg = "Only .csv files accepted"
    return render_template('index.html', error_msg=error_msg)


# @app.route('/select_column_type', methods=['POST', 'GET'])
def select_column_type(file, filename):
    print(file)
    return render_template('select_column_type.html',
                           csv_filename=filename,
                           colnames=["col1", "col2", "col3"])


webview.create_window('ASAP: Automated Suite Allocation Program for Yale-NUS First-Years', app)
webview.start(debug=True)
