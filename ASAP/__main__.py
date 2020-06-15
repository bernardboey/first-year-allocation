"""First Year Allocation

This script allows the user to allocate first-year students to suites according to preferences.

This script accepts the student data in a .csv file, which must be processed such that it has the following columns:
    * matric
    * sex
    * country
    * sleep_pref (values must be numeric e.g. 1 - 4)
    * suite_pref (values must be numeric e.g. 1 - 4)
    * cleanliness_pref (values must be numeric e.g. 1 - 4)
    * alcohol_pref (values must be Yes or No)
    * gender_pref

It is recommended that the .csv file be processed using data_cleaning.py which is packaged together with this script.
It is also recommended that a virtual environment be set up, and packages installed using requirements.txt

This file contains the following classes:
    * Student
    * Suite
    * SuiteAllocation

This file contains the following functions:
    * calculate_score - Takes in a suite and an optional student and returns a score that indicates how good a fit
        the students in the suite + the new student are for each other. A lower score is better.
    * add_students - Parses data from the student dataframe and returns a list of Student objects
    * main - The main function of the script that allocates suites, taking data from a .csv file

TODO: Can we try to automate the part where we define the preferences or at least make it dynamic?
    Because the questions may differ year by year.
TODO: Check correctness of code (.copy()?)
"""

import random
import math
import sys

import pandas as pd
import numpy as np

from ASAP import scoring
from ASAP import match_round
from ASAP import parser
from ASAP.student import Citizenship


class SuiteAllocation:
    class SuiteData:
        def __init__(self, suite_num, capacity):
            self.suite_num = suite_num
            self._capacity = capacity
            self.vacancies = capacity
            self.students = []

        @property
        def capacity(self):
            return self._capacity

        def add_student(self, student):
            self.students.append(student)
            self.vacancies -= 1

        def __repr__(self):
            return str(self.suite_num)

        def __str__(self):
            return str(self.suite_num)

    def __init__(self, students):
        self.students = students
        self.student_results = []
        self.total_students = len(students)
        self.batch_size = math.ceil(self.total_students/6)
        self.suites = [SuiteAllocation.SuiteData(f"FY Suite {i:02d}", 6) for i in range(self.batch_size)]
        self.batches = self.split_into_batches()

    @staticmethod
    def get_citizenship(student):
        if student.citizenship == Citizenship.LOCAL:
            return 0
        else:
            return 1

    def split_into_batches(self):
        random.shuffle(self.students)
        sorted_students = sorted(self.students, key=self.get_citizenship)
        batches_of_students = []
        for i in range(6):
            start_id = i * self.batch_size
            if i < 5:
                end_id = start_id + self.batch_size
            else:
                end_id = self.total_students
            batches_of_students.append(sorted_students[start_id:end_id])
        return batches_of_students

    def match(self):
        self.allocate_first_batch()
        self.allocate_remaining_batches()

    def allocate_first_batch(self):
        students = self.batches.pop(0)
        student_results = match_round.Match.first_round(students, self.suites)
        self.student_results.extend(student_results)

    def allocate_remaining_batches(self, suite_propose=True):
        """


        TODO: Can refactor this to calculating the scores for every suite-student pairing first.
            Then, generate the ranking for both students and suites.
        """
        for i in range(5):
            students = self.batches.pop(0)
            student_results = match_round.Match(students, self.suites, suite_propose).run_match()
            self.student_results.extend(student_results)

    def global_score(self):
        scores = []
        for suite in self.suites:
            scores.append(scoring.calculate_score(suite, student=None))
        return np.mean(scores)

    def get_allocation(self):
        return self.suites.copy()


def main():
    if len(sys.argv) != 2:
        print("Wrong format! Please type 'python -m ASAP [csv_file]'")
        return
    csv_path = sys.argv[1]
    students_data = pd.read_csv(csv_path)
    female_students, male_students = parser.add_students(students_data)
    allocate_suites(female_students, "females")
    allocate_suites(male_students, "males")


def allocate_suites(students, name):
    allocations = {}
    for i in range(20):
        suite_allocation = SuiteAllocation(students)
        suite_allocation.match()
        global_score = suite_allocation.global_score()
        allocated_suites = suite_allocation.get_allocation()
        print(f"Global score: {global_score}")
        allocations[global_score] = allocated_suites
    allocated_suites = allocations[min(allocations)]
    scores = []
    for suite in allocated_suites:
        scores.append(scoring.calculate_score(suite, student=None))
    print(f"\nFinal score: {np.mean(scores)}")
    suites_data = {
        "Suite": [repr(suite) for suite in allocated_suites],
        "Num_students": [len(suite.students) for suite in allocated_suites],
        "Countries": [[student.data.country for student in suite.students] for suite in allocated_suites],
        "Citizenship Diversity": [scoring.citizenship_diversity_score(suite.students) for suite in allocated_suites],
        "Country Diversity": [scoring.country_diversity_score(suite.students) for suite in allocated_suites],
        "Schools": [[student.data.school for student in suite.students] for suite in allocated_suites],
        "School Diversity": [scoring.school_diversity_score(suite.students) for suite in allocated_suites],
        "Sleep Prefs": [[student.data.sleep_pref for student in suite.students] for suite in allocated_suites],
        "Sleep Prefs Similarity": [scoring.sleep_pref_score(suite.students) for suite in allocated_suites],
        "Suite Prefs": [[student.data.suite_pref for student in suite.students] for suite in allocated_suites],
        "Suite Prefs Similarity": [scoring.suite_pref_score(suite.students) for suite in allocated_suites],
        "Cleanliness Prefs": [[student.data.cleanliness_pref for student in suite.students] for suite in allocated_suites],
        "Cleanliness Prefs Similarity": [scoring.cleanliness_pref_score(suite.students) for suite in allocated_suites],
        "Alcohol Prefs": [[student.data.alcohol_pref for student in suite.students] for suite in allocated_suites],
        "Alcohol Prefs Similarity": [scoring.alcohol_pref_score(suite.students) for suite in allocated_suites],
    }
    suites_df = pd.DataFrame(suites_data, columns=list(suites_data.keys()))
    suites_df.to_csv(f"output/{name}.csv", index=False)


if __name__ == "__main__":
    main()
