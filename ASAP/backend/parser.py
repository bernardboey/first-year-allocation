"""This module provides functionality to parse student data from a CSV file.

    Typical usage example:

    female_students, male_students = parse_student_data(student_df)
"""

import pandas as pd
import numpy as np
import datetime

from ASAP.backend.student import StudentData
from ASAP.backend import scoring
from ASAP.backend import util


def parse_student_data(students_df):
    """Parses student data from a CSV file.

    Args:
        csv_path: A string representing the path of the CSV file.

    Returns:
        Two lists containing StudentData objects, one list for female students and one list for male students.
    """

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
        "RCA": [student.current_choice.rca for student in students],
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
