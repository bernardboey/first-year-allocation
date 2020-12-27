import os
import inspect
import pickle
import shutil

from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import webview

from ASAP.__main__ import ASAP, ColumnTypes

# NOT USING CSRF TOKENS FOR SIMPLICITY
# REFERENCES
# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
# https://github.com/r0x0r/pywebview/tree/master/examples/flask_app

app = Flask(__name__, static_folder='./assets', template_folder='./templates')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching
UPLOAD_FOLDER = 'tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
CURRENT_FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
CURRENT_PATH = os.path.dirname(os.path.abspath(CURRENT_FILENAME))
UPLOAD_PATH = os.path.join(CURRENT_PATH, UPLOAD_FOLDER)
PICKLE_FILEPATH = os.path.join(UPLOAD_PATH, "asap_temp_storage.pickle")


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def remove_and_delete_dir(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    os.makedirs(path)


def save_pickle(obj):
    with open(PICKLE_FILEPATH, "wb") as f:
        pickle.dump(obj, f)


def restore_pickle() -> ASAP:
    with open(PICKLE_FILEPATH, "rb") as f:
        return pickle.load(f)


@app.route('/', methods=['GET', 'POST'])
def home():
    error_msg = None
    if request.method == 'POST':
        file = request.files['csv_file']
        if file and allowed_file(file.filename, {'csv'}):
            filename = secure_filename(file.filename)
            remove_and_delete_dir(UPLOAD_PATH)
            filepath = os.path.join(UPLOAD_PATH, filename)
            file.save(filepath)
            save_pickle(ASAP(filepath))
            return redirect(url_for("select_column_type"))
        else:
            error_msg = "Only .csv files accepted"
    return render_template('index.html', error_msg=error_msg)


@app.route('/select_column_type', methods=['GET', 'POST'])
def select_column_type():
    error_msg = None
    selected_values = {}
    asap_obj = restore_pickle()
    if asap_obj.column_types_defined():
        for i, (col, _type) in enumerate(asap_obj.col_to_type.items()):
            selected_values[f"column{i}"] = _type.value
    colnames, unique_values, head_values = asap_obj.get_colnames_and_unique_values()
    if request.method == 'POST':
        selected_types = [request.form[f"column{i}"] for i in range(len(colnames))]
        col_to_type = {col: _type for col, _type in zip(colnames, selected_types)}
        try:
            asap_obj.set_column_types(col_to_type)
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("verify_living_preferences"))
    return render_template('select_column_type.html',
                           csv_filename=asap_obj.filename,
                           coltypes=[e.value for e in ColumnTypes],
                           colnames=colnames,
                           unique_values=unique_values,
                           head_values=enumerate(head_values, start=1),
                           selected_values=selected_values,
                           error_msg=error_msg)


@app.route('/verify_living_preferences', methods=['GET', 'POST'])
def verify_living_preferences():
    error_msg = None
    selected_values = {}
    asap_obj = restore_pickle()
    colnames, unique_values, _ = asap_obj.get_colnames_and_unique_values()
    unique_values = [values for col, values in zip(colnames, unique_values) if col in asap_obj.living_pref_cols]
    if request.method == 'POST':
        # get data from form.request

        try:
            # asap_obj.set_living_pref_order
            pass
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("home"))
    return render_template('verify_living_preferences.html',
                           living_pref_cols=asap_obj.living_pref_cols,
                           unique_values=unique_values,
                           selected_values=selected_values,
                           error_msg=error_msg)


webview.create_window('ASAP: Automated Suite Allocation Program for Yale-NUS First-Years', app)
webview.start(debug=True)
