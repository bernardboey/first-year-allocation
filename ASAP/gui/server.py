import os
import inspect
import pickle
import shutil
import json
import time

from flask import Flask, request, render_template, redirect, url_for
import webview

from ASAP.__main__ import ASAP, LivingPrefColumnType

# NOT USING CSRF TOKENS FOR SIMPLICITY
# REFERENCES
# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
# https://github.com/r0x0r/pywebview/tree/master/examples/flask_app

app = Flask(__name__, static_folder='./static', template_folder='./templates')  # TODO: Change bootstrap to local
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching
UPLOAD_FOLDER = 'tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
CURRENT_FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
CURRENT_PATH = os.path.dirname(os.path.abspath(CURRENT_FILENAME))
UPLOAD_PATH = os.path.join(CURRENT_PATH, UPLOAD_FOLDER)
PICKLE_FILEPATH = os.path.join(UPLOAD_PATH, "asap_temp_storage.pickle")
WINDOW = webview.create_window('ASAP: Automated Suite Allocation Program for Yale-NUS First-Years', app,
                               width=1200, height=800, text_select=True)


def save_pickle(obj):
    if not os.path.exists(UPLOAD_PATH):
        os.makedirs(UPLOAD_PATH)
    with open(PICKLE_FILEPATH, "wb") as f:
        pickle.dump(obj, f)


def restore_pickle() -> ASAP:
    with open(PICKLE_FILEPATH, "rb") as f:
        return pickle.load(f)


@app.route('/', methods=['GET', 'POST'])
def home():
    error_msg = None
    if request.method == 'POST':
        filepath = WINDOW.create_file_dialog(webview.OPEN_DIALOG, directory='/', file_types=('CSV Files (*.csv)',))
        if filepath:
            try:
                save_pickle(ASAP(filepath[0]))
                return redirect(url_for("select_column_type"))
            except ValueError as e:
                error_msg = str(e)
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
        # for i, _type in enumerate((asap_obj.ID, asap_obj.OTHERS, asap_obj.SEX, asap_obj.SCHOOL, asap_obj.COUNTRY,
        #                            asap_obj.ACCESSIBILITY, asap_obj.AVAILABLE_RCS, asap_obj.OTHERS,
        #                            asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.LIVING_PREF,
        #                            asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.LIVING_PREF)):
        #     selected_values[f"column{i}"] = _type.desc
        for i, _type in enumerate((asap_obj.ID, asap_obj.SCHOOL, asap_obj.OTHERS, asap_obj.SEX, asap_obj.LIVING_PREF,
                                   asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.OTHERS,
                                   asap_obj.ACCESSIBILITY, asap_obj.AVAILABLE_RCS, asap_obj.OTHERS, asap_obj.COUNTRY,
                                   asap_obj.LIVING_PREF, asap_obj.LIVING_PREF, asap_obj.OTHERS)):
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
    # Temporarily here to speed up development #
    order_list = [[3, 0, 1, 2], [3, 0, 1, 2], [2, 0, 3, 1], [0, 1, 3, 2], [0, 1], [0, 1]]
    unique_values = [[unique_values[i][j] for j in order] for i, order in enumerate(order_list)]
    # End of block #
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
        # Temporarily here #
        _weights = [10, 10, 10, 30, 10, 30]
        weights = {col: weight for col, weight in zip(asap_obj.LIVING_PREF.cols, _weights)}
        # End of block #
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
        saga_sextets = asap_obj.avail_sextets_saga
        elm_sextets = asap_obj.avail_sextets_elm
        cendana_sextets = asap_obj.avail_sextets_cendana
        saga_a11y_suites = asap_obj.avail_a11y_suites_saga
        elm_a11y_suites = asap_obj.avail_a11y_suites_elm
        cendana_a11y_suites = asap_obj.avail_a11y_suites_cendana
    else:
        saga_sextets, elm_sextets, cendana_sextets = 12, 14, 13  # Usually 14, 14, 14
        saga_a11y_suites, elm_a11y_suites, cendana_a11y_suites = 1, 0, 1  # Usually 0, 0, 0
    if request.method == 'POST':
        saga_sextets = int(request.form["saga-sextets"])
        elm_sextets = int(request.form["elm-sextets"])
        cendana_sextets = int(request.form["cendana-sextets"])
        saga_a11y_suites = int(request.form["saga-a11y-suites"])
        elm_a11y_suites = int(request.form["elm-a11y-suites"])
        cendana_a11y_suites = int(request.form["cendana-a11y-suites"])
        try:
            asap_obj.set_options(saga_sextets, elm_sextets, cendana_sextets,
                                 saga_a11y_suites, elm_a11y_suites, cendana_a11y_suites)
        except ValueError as e:
            error_msg = str(e)
        else:
            save_pickle(asap_obj)
            return redirect(url_for("review_data"))
    return render_template('select_options.html',
                           saga_sextets=saga_sextets,
                           elm_sextets=elm_sextets,
                           cendana_sextets=cendana_sextets,
                           saga_a11y_suites=saga_a11y_suites,
                           elm_a11y_suites=elm_a11y_suites,
                           cendana_a11y_suites=cendana_a11y_suites,
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
                           num_a11y_males=asap_obj.num_a11y_males, num_a11y_females=asap_obj.num_a11y_females,
                           avail_sextets_saga=asap_obj.avail_sextets_saga,
                           avail_sextets_elm=asap_obj.avail_sextets_elm,
                           avail_sextets_cendana=asap_obj.avail_sextets_cendana,
                           avail_a11y_suites_saga=asap_obj.avail_a11y_suites_saga,
                           avail_a11y_suites_elm=asap_obj.avail_a11y_suites_elm,
                           avail_a11y_suites_cendana=asap_obj.avail_a11y_suites_cendana,
                           total_suites=asap_obj.total_suites, required_suites=asap_obj.required_suites,
                           required_suites_male=asap_obj.required_suites_male,
                           required_suites_female=asap_obj.required_suites_female,
                           required_a11y_suites_male=asap_obj.required_a11y_suites_male,
                           required_a11y_suites_female=asap_obj.required_a11y_suites_female,
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
    context = {
        "datetime": asap_obj.datetime,
        "csv_filename": asap_obj.filename,
        "total_students": asap_obj.total_students,
        "num_males": asap_obj.num_males,
        "num_females": asap_obj.num_females,
        "num_a11y_males": asap_obj.num_a11y_males,
        "num_a11y_females": asap_obj.num_a11y_females,
        "avail_sextets_saga": asap_obj.avail_sextets_saga,
        "avail_sextets_elm": asap_obj.avail_sextets_elm,
        "avail_sextets_cendana": asap_obj.avail_sextets_cendana,
        "avail_a11y_suites_saga": asap_obj.avail_a11y_suites_saga,
        "avail_a11y_suites_elm": asap_obj.avail_a11y_suites_elm,
        "avail_a11y_suites_cendana": asap_obj.avail_a11y_suites_cendana,
        "total_suites": asap_obj.total_suites,
        "used_suites": len(asap_obj.suites),
        "rc_list": asap_obj.RC_LIST_WITH_UNALLOCATED,
        "female_stats": asap_obj.female_stats,
        "male_stats": asap_obj.male_stats,
        "num_living_prefs": len(asap_obj.LIVING_PREF.cols),
        "living_prefs": asap_obj.LIVING_PREF.cols,
        "living_pref_order": asap_obj.LIVING_PREF.selected_order,
        "weights": asap_obj.LIVING_PREF.weights,
    }
    if request.method == 'POST':
        folder_path = WINDOW.create_file_dialog(webview.FOLDER_DIALOG, directory='/')
        if folder_path:
            try:
                asap_obj.export_files(folder_path[0])
                save_pickle(asap_obj)
                with open(os.path.join(folder_path[0], "allocation_report.html"), 'w') as f:
                    f.write(render_template('results.html', **context))
                return redirect(url_for("completed"))
            except PermissionError as e:
                error_msg = f"Please close the following files as the program will need to overwrite them:\n{e}"
    return render_template('results.html', error_msg=error_msg, **context)


@app.route('/completed', methods=['GET'])
def completed():
    return render_template('completed.html')


def main():
    webview.start(debug=True)


if __name__ == "__main__":
    main()
