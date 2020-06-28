"""This module provides functionality to parse student data from a CSV file.

    Typical usage example:

    female_students, male_students = parse_student_data(student_df)
"""

import pandas as pd
import numpy as np
import datetime

from ASAP.student import StudentData
from ASAP import scoring
import ASAP.util as util

# A dictionary mapping variable names to the corresponding column names, for the demographic columns.
# Change this if the headers of the CSV are different.

DEMOGRAPHIC_COLUMNS = {
    # [variable name]: [column name]
    "matric": "ID",
    "sex": "sex",
    "country": "country",
    "school": "school",
    "gender_pref": "gender_pref",
}
# A dictionary mapping variable names to the corresponding column names, for the living preference columns.
# Change this if the headers of the CSV are different.
LIVING_PREFERENCE_COLUMNS = {
    # [variable name]: [column name]
    "sleep_pref": "sleep",
    "suite_pref": "suite_pref",
    "cleanliness_pref": "cleanliness",
    "alcohol_pref": "alcohol",
}
COLUMN_NAMES = {
    **DEMOGRAPHIC_COLUMNS,
    **LIVING_PREFERENCE_COLUMNS
}


def parse_student_data(csv_path):
    """Parses student data from a CSV file.

    Args:
        csv_path: A string representing the path of the CSV file.

    Returns:
        Two lists containing StudentData objects, one list for female students and one list for male students.
    """
    students_df = pd.read_csv(csv_path)
    validate_student_data(students_df)
    set_max_scores(students_df)
    female_students, male_students = add_students(students_df)
    return female_students, male_students


def validate_student_data(students_df):
    """Validates the data from a CSV file.

    Validates the following:
    1. All required columns are present
    2. Extra columns are detected and the user is asked to confirm that they are not used
    3. Sex column only contains "M" and "F"
    4. Living preference columns contain only integers

    Makes use of the columns as listed above (DEMOGRAPHIC_COLUMNS and LIVING_PREFERENCE_COLUMNS).
    Please edit those constants if the column names change or more columns need to be added.

    Args:
        students_df: A Pandas DataFrame containing student data.
    """
    required_columns = list(COLUMN_NAMES.values())
    df_columns = list(students_df.columns)
    extra_columns = []

    # Checks whether all required columns are present and detects extra columns
    for column in required_columns + df_columns:
        if column not in df_columns:
            raise ValueError(f"Column '{column}' is missing in the csv.")
        if column not in required_columns:
            extra_columns.append(column)
    if extra_columns:
        # Reminds user that extra columns will not be used and verifies that user wants to continue
        proceed = util.input_yes_no(f"The following extra column(s) will not be used: {', '.join(extra_columns)}.\n"
                               f"Do you want to continue?")
        if not proceed:  # User indicates that extra columns should be used.
            print("Okay, please edit the code to incorporate the extra column(s).")
            raise SystemExit

    # Checks whether the sex column only contains "M" and "F"
    for sex in students_df[COLUMN_NAMES["sex"]].unique():
        if sex not in ("M", "F"):
            raise ValueError(f"Column '{COLUMN_NAMES['sex']}' contains unrecognised sex: {sex}.")

    # Checks whether living preference columns contain only integers
    for column in LIVING_PREFERENCE_COLUMNS.values():
        try:
            if not np.array_equal(students_df[column], students_df[column].astype(int)):  # True if only integers
                raise ValueError(f"Column '{column}' needs to contain only integers (e.g. 0, 1, 2, 3, 4).")
        except ValueError:
            raise ValueError(f"Column '{column}' needs to be numeric (e.g. 0, 1, 2, 3, 4).")


def set_max_scores(students_df):
    unique_options = {}
    for living_pref in LIVING_PREFERENCE_COLUMNS:
        unique_options[living_pref] = list(students_df[COLUMN_NAMES[living_pref]].unique())
    scoring.MaxScores.set_max_scores(unique_options)


def add_students(students_df):
    """Creates StudentData objects based on student data from a Pandas DataFrame.

    Makes use of the columns as listed above (DEMOGRAPHIC_COLUMNS and LIVING_PREFERENCE_COLUMNS).
    Please edit those constants if the column names change or more columns need to be added.
    Please also edit the StudentData class if more columns need to be added.

    Args:
        students_df: A Pandas DataFrame containing student data.

    Returns:
        Two lists containing StudentData objects, one list for female students and one list for male students.
    """
    female_students = []
    male_students = []
    for i in range(len(students_df)):
        # Gathers data for one student in a dictionary that maps variable names to the values
        student_data = {var: students_df.loc[i, col_name] for var, col_name in COLUMN_NAMES.items()}
        new_student = StudentData(**student_data)
        sex = students_df.loc[i, COLUMN_NAMES["sex"]]
        if sex == "F":
            female_students.append(new_student)
        elif sex == "M":
            male_students.append(new_student)
        else:
            raise ValueError(f"Unrecognised sex: {sex}")
    return female_students, male_students


def generate_temp_results(suites, csv_path):
    """
    Temporary function to generate results for an allocation

    Args:
        suites:
        csv_path:
    """
    suites_data = {
        "Suite": [repr(suite) for suite in suites],
        "Num_students": [len(suite.students) for suite in suites],
        "Countries": [[student.country for student in suite.students] for suite in suites],
        "Citizenship Diversity": [scoring.citizenship_diversity_score(suite.students) for suite in suites],
        "Country Diversity": [scoring.country_diversity_score(suite.students) for suite in suites],
        "Schools": [[student.school for student in suite.students] for suite in suites],
        "School Diversity": [scoring.school_diversity_score(suite.students) for suite in suites],
        "Sleep Prefs": [[student.sleep_pref for student in suite.students] for suite in suites],
        "Sleep Prefs Similarity": [scoring.sleep_pref_score(suite.students) for suite in suites],
        "Suite Prefs": [[student.suite_pref for student in suite.students] for suite in suites],
        "Suite Prefs Similarity": [scoring.suite_pref_score(suite.students) for suite in suites],
        "Cleanliness Prefs": [[student.cleanliness_pref for student in suite.students] for suite in suites],
        "Cleanliness Prefs Similarity": [scoring.cleanliness_pref_score(suite.students) for suite in suites],
        "Alcohol Prefs": [[student.alcohol_pref for student in suite.students] for suite in suites],
        "Alcohol Prefs Similarity": [scoring.alcohol_pref_score(suite.students) for suite in suites],
        "Final Score": [scoring.calculate_success(suite.students) for suite in suites]
    }
    suites_df = pd.DataFrame(suites_data, columns=list(suites_data.keys()))
    suites_df.to_csv(csv_path, index=False)


def generate_masterlist(suites, csv_path):
    CURRENT_YEAR = datetime.datetime.now().year
    students = [student for suite in suites for student in suite.students]
    num_students = len(students)
    students_data = {
        "Suite": [student.current_choice.suite_num for student in students],
        "Room": ["TBC" for student in students],
        "RC": [student.current_choice.rc for student in students],
        "Matric": [student.matric for student in students],
        "Gender": [student.sex.value for student in students],
        "Admit": [CURRENT_YEAR] * num_students,
        "Class": [CURRENT_YEAR + 4] * num_students,
        "Student Type": ["First-Year"] * num_students,
        "Citizenship Country": [student.country for student in students],
        "Unofficial Residency": [student.citizenship.value for student in students],
        "Gender Preference": [student.gender_pref for student in students]
    }
    students_df = pd.DataFrame(students_data, columns=list(students_data.keys()))
    students_df.to_csv(csv_path, index=False)
