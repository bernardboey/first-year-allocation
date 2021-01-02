import os
import inspect
import pickle
import shutil
import json

from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import webview

from ASAP.__main__ import ASAP, LivingPrefColumnType

# NOT USING CSRF TOKENS FOR SIMPLICITY
# REFERENCES
# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
# https://github.com/r0x0r/pywebview/tree/master/examples/flask_app

app = Flask(__name__, static_folder='./static', template_folder='./templates')
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
    colnames, unique_values, head_values = asap_obj.get_colnames_and_unique_values()
    if request.method == 'POST':
        col_type_assoc = [(col, request.form[f"column{i}"]) for i, col in enumerate(colnames)]
        try:
            asap_obj.set_column_types(col_type_assoc)
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("verify_living_preferences"))
    elif request.method == 'GET':
        if asap_obj.col_types_defined:
            for i, (_, _type) in enumerate(asap_obj.col_to_type.items()):
                selected_values[f"column{i}"] = _type.desc

        # TEMPORARILY HERE TO SPEED UP DEVELOPMENT #
        for i, _type in enumerate((asap_obj.NAME, asap_obj.SCHOOL, asap_obj.SEX, asap_obj.COUNTRY, asap_obj.LIVING_PREF,
                                   asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.OTHERS)):
            selected_values[f"column{i}"] = _type.desc
        # END OF BLOCK #

    return render_template('select_column_type.html',
                           csv_filename=asap_obj.filename,
                           coltypes=[e.desc for e in asap_obj.COL_TYPES],
                           colnames=colnames,
                           unique_values=unique_values,
                           head_values=enumerate(head_values, start=1),
                           selected_values=selected_values,
                           error_msg=error_msg)


@app.route('/verify_living_preferences', methods=['GET', 'POST'])
def verify_living_preferences():
    error_msg = None
    asap_obj = restore_pickle()
    colnames, unique_values, _ = asap_obj.get_colnames_and_unique_values()
    unique_values = [sorted(values) for col, values in zip(colnames, unique_values) if col in asap_obj.LIVING_PREF.cols]
    if asap_obj.living_pref_order_defined:
        unique_values = asap_obj.LIVING_PREF.selected_order
    if request.method == 'POST':
        selected_order = json.loads(request.form["living-pref-data"])
        try:
            asap_obj.set_living_pref_order(selected_order)
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("select_weights"))
    return render_template('verify_living_preferences.html',
                           living_pref_cols=asap_obj.LIVING_PREF.cols,
                           unique_values=unique_values,
                           error_msg=error_msg)


@app.route('/select_weights', methods=['GET', 'POST'])
def select_weights():
    error_msg = None
    asap_obj = restore_pickle()
    if asap_obj.weights_defined:
        weights = asap_obj.LIVING_PREF.weights
    else:
        weights = {col: 100 // len(asap_obj.LIVING_PREF.cols) for i, col in enumerate(asap_obj.LIVING_PREF.cols)}
    if request.method == 'POST':
        weights = {col: int(request.form[f"column{i}"]) for i, col in enumerate(asap_obj.LIVING_PREF.cols)}
        try:
            asap_obj.set_weights(weights)
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("select_options"))
    return render_template('select_weights.html',
                           living_pref_cols=asap_obj.LIVING_PREF.cols,
                           weights=weights,
                           error_msg=error_msg)


@app.route('/select_options', methods=['GET', 'POST'])
def select_options():
    error_msg = None
    asap_obj = restore_pickle()
    if asap_obj.options_defined:
        saga = asap_obj.avail_suites_saga
        elm = asap_obj.avail_suites_elm
        cendana = asap_obj.avail_suites_cendana
    else:
        saga, elm, cendana = 16, 16, 16
    if request.method == 'POST':
        saga = int(request.form["saga-suites"])
        elm = int(request.form["elm-suites"])
        cendana = int(request.form["cendana-suites"])
        try:
            asap_obj.set_options(saga, elm, cendana)
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("review_data"))
    return render_template('select_options.html',
                           saga_suites=saga,
                           elm_suites=elm,
                           cendana_suites=cendana,
                           error_msg=error_msg)


@app.route('/review_data', methods=['GET', 'POST'])
def review_data():
    asap_obj = restore_pickle()
    colnames, _, head_values = asap_obj.get_colnames_and_unique_values()
    colnames = [f"Living Pref: {col}"
                if isinstance(asap_obj.col_to_type[col], LivingPrefColumnType)
                else asap_obj.col_to_type[col].desc
                for col in colnames]

    if request.method == 'POST':
        return redirect(url_for("run_allocation"))

    return render_template('review_data.html',
                           csv_filename=asap_obj.filename,
                           colnames=colnames, head_values=enumerate(head_values, start=1),
                           total_students=asap_obj.total_students,
                           num_males=asap_obj.num_males, num_females=asap_obj.num_females,
                           avail_suites_saga=asap_obj.avail_suites_saga,
                           avail_suites_elm=asap_obj.avail_suites_elm,
                           avail_suites_cendana=asap_obj.avail_suites_cendana,
                           total_suites=asap_obj.total_suites, required_suites=asap_obj.required_suites,
                           required_suites_male=asap_obj.required_suites_male,
                           required_suites_female=asap_obj.required_suites_female,
                           num_living_prefs=len(asap_obj.LIVING_PREF.cols),
                           living_prefs=asap_obj.LIVING_PREF.cols,
                           living_pref_order=asap_obj.LIVING_PREF.selected_order,
                           weights=asap_obj.LIVING_PREF.weights)


@app.route('/run_allocation', methods=['GET', 'POST'])
def run_allocation():
    error_msg = None
    asap_obj = restore_pickle()
    if request.method == 'POST':
        asap_obj.run_allocation()
        save_pickle(asap_obj)
        return redirect(url_for("results"))
        try:
            asap_obj.run_allocation()
        except Exception as e:  # General Exception because various kinds of errors can be thrown by run_allocation()
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("results"))
    return render_template('run_allocation.html', error_msg=error_msg)


@app.route('/results', methods=['GET', 'POST'])
def results():
    error_msg = None
    asap_obj = restore_pickle()
    return render_template('results.html',
                           error_msg=error_msg)


def main():
    webview.create_window('ASAP: Automated Suite Allocation Program for Yale-NUS First-Years', app)
    webview.start(debug=True)


if __name__ == "__main__":
    main()
