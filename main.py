import random
import enum
import math
import sys

import pandas as pd
import numpy as np

LOCAL_SCHOOLS = ("AJC", "BJC", "CJC", "DJC", "EJC", "FJC", "GJC", "HJC", "IJC", "JJC", "KJC", "LJC", "MJC", "NJC",
                "OJC", "PJC", "QJC", "RJC", "SJC", "TJC", "UJC", "VJC", "WJC", "XJC", "ZJC", "AAJC", "BBJC", "CCJC",
                "DDJC", "EEJC", "FFJC", "GGJC", "HHJC", "IIJC", "JJJC", "KKJC", "LLJC", "MMJC", "NNJC", "OOJC", "PPJC")


class Citizenship(enum.Enum):
    INTERNATIONAL = "International"
    LOCAL = "Local"


class Student:
    def __init__(self, matric, sex, country, school, gender_pref,
                 sleep_pref, suite_pref, cleanliness_pref, alcohol_pref):
        self.matric = matric
        self.sex = sex
        self.country = country
        self.school = school
        self.gender_pref = gender_pref
        self.sleep_pref = sleep_pref
        self.suite_pref = suite_pref
        self.cleanliness_pref = cleanliness_pref
        self.alcohol_pref = alcohol_pref
        if self.country == "Singapore":
            self.citizenship = Citizenship.LOCAL
        else:
            self.citizenship = Citizenship.INTERNATIONAL
        self.suite = None
        self.scores = {}
        self.ranking = []

    def __repr__(self):
        return self.matric

    def __str__(self):
        return self.matric

    def full_information(self):
        attributes = str([self.suite, self.sex, self.country, self.school, self.gender_pref,
                          self.sleep_pref, self.suite_pref, self.cleanliness_pref, self.alcohol_pref])
        return f"{self.matric}: {attributes}"

    def generate_score(self, suite):
        if suite in self.scores:
            return self.scores[suite]
        else:
            score = calculate_score(suite, self)
            suite.scores[self] = score
            return score

    def generate_ranking(self, suites):
        self.ranking = sorted(suites, key=self.generate_score)


class Suite:
    def __init__(self, suite_num, capacity):
        self.suite_num = suite_num
        self.capacity = capacity
        # I am currently not taking capacity into consideration
        self.students = []
        self.scores = {}
        self.ranking = []
        self.current_choice = None

    def __repr__(self):
        return str(self.suite_num)

    def __str__(self):
        return str(self.suite_num)

    def add_student(self, student):
        self.students.append(student)

    def generate_score(self, student):
        if student in self.scores:
            return self.scores[student]
        else:
            score = calculate_score(self, student)
            student.scores[self] = score
            return score

    def generate_ranking(self, students):
        self.ranking = sorted(students, key=self.generate_score)

    def citizenship_diversity_score(self):
        citizenships = [student.citizenship for student in self.students]
        num_locals = citizenships.count(Citizenship.LOCAL)
        num_intls = citizenships.count(Citizenship.INTERNATIONAL)
        try:
            ratio = num_locals / num_intls
        except ZeroDivisionError:
            return 0
        if 2/3 <= ratio <= 3/2:
            return 1
        elif 2/4 <= ratio <= 4/2:
            return 0.5
        elif 1/3 <= ratio <= 3/1:
            return 0.3
        elif 1/4 <= ratio <= 4/1:
            return 0.25
        elif 1/5 <= ratio <= 5/1:
            return 0.2
        else:
            return 0

    def country_diversity_score(self):
        overseas_countries = [student.country for student in self.students if student.country != "Singapore"]
        if len(overseas_countries) == len(set(overseas_countries)):
            return 1
        elif len(overseas_countries) - len(set(overseas_countries)) == 1:
            return 0.5
        else:
            return 0

    def school_diversity_score(self):
        overseas_countries = [student.school for student in self.students]
        if len(overseas_countries) == len(set(overseas_countries)):
            return 1
        elif len(overseas_countries) - len(set(overseas_countries)) == 1:
            return 0.5
        elif len(overseas_countries) - len(set(overseas_countries)) == 2:
            return 0.3
        elif len(overseas_countries) - len(set(overseas_countries)) == 3:
            return 0.2
        elif len(overseas_countries) - len(set(overseas_countries)) == 4:
            return 0.1
        else:
            return 0

    def sleep_pref_score(self):
        sleep_prefs = np.std([student.sleep_pref for student in self.students]) / 2
        return 1 - sleep_prefs

    def suite_pref_score(self):
        suite_prefs = np.std([student.suite_pref for student in self.students]) / 2
        return 1 - suite_prefs

    def cleanliness_pref_score(self):
        cleanliness_prefs = np.std([student.cleanliness_pref for student in self.students]) / 1.5
        return 1 - cleanliness_prefs

    def alcohol_pref_score(self):
        alcohol_prefs = np.std([student.alcohol_pref for student in self.students]) / 0.5
        return 1 - alcohol_prefs


def calculate_score(suite, student):
    if student is None:
        students = suite.students
    else:
        students = suite.students + [student]
    overseas_countries = [student.country for student in students if student.citizenship == Citizenship.INTERNATIONAL]
    if len(overseas_countries) != len(set(overseas_countries)):  # Check for duplicate overseas countries
        return math.inf
    schools = [student.school for student in students]
    if len(schools) != len(set(schools)):  # Check for duplicate schools
        return math.inf
    sleep_prefs = np.std([student.sleep_pref for student in students]) / 2
    suite_prefs = np.std([student.suite_pref for student in students]) / 1.5
    cleanliness_prefs = np.std([student.cleanliness_pref for student in students]) / 1.5
    alcohol_prefs = np.std([student.alcohol_pref for student in students]) / 0.5
    score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    return score


class SuiteAllocation:
    def __init__(self, students, suites):
        self.students = students
        self.total_students = len(students)
        self.all_suites = suites
        self.suites = []
        self.batch_size = math.ceil(self.total_students/6)
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
        batch = self.batches.pop(0)
        if len(self.all_suites) < self.batch_size:
            raise ValueError("Not enough suites for the number of students.")
        self.suites = self.all_suites[:self.batch_size]
        for i, student in enumerate(batch):
            suite = self.suites[i]
            student.suite = suite
            suite.add_student(student)

    def allocate_remaining_batches(self):
        for i in range(5):
            students = self.batches.pop(0)
            for student in students:
                student.generate_ranking(self.suites)
            for suite in self.suites:
                suite.generate_ranking(students)
            self.gale_shapley(students)

    def gale_shapley(self, students):
        # Student propose
        unallocated_students = students
        while unallocated_students:
            student = unallocated_students.pop(0)
            suite = student.ranking.pop(0)
            if suite.current_choice is None:
                suite.current_choice = student
                student.suite = suite
            elif suite.ranking.index(student) < suite.ranking.index(suite.current_choice):
                suite.current_choice.suite = None
                unallocated_students.append(suite.current_choice)
                suite.current_choice = student
                student.suite = suite
            elif student.ranking:
                # still have other choices
                unallocated_students.append(student)
        for student in students:
            student.scores = {}
            student.ranking = []
        for suite in self.suites:
            if suite.current_choice:
                suite.students.append(suite.current_choice)
                suite.current_choice = None
                suite.capacity -= 1
            suite.scores = {}
            suite.ranking = []

    def global_score(self):
        scores = []
        for suite in self.suites:
            scores.append(calculate_score(suite, student=None))
        return np.mean(scores)

    def get_allocation(self):
        return [suite.students for suite in self.suites]

    def clean_up(self):
        for student in self.students:
            student.suite = None
            student.scores = {}
            student.ranking = []
        for suite in self.all_suites:
            suite.students = []
            suite.scores = {}
            suite.ranking = []
            suite.current_choice = None


def add_students(students_data):
    students = []
    for i in range(len(students_data)):
        if students_data.country[i] == "Singapore":
            school = random.choice(LOCAL_SCHOOLS)
        else:
            school = f"School {i}"
        if students_data.alcohol[i] == "Yes":
            alcohol = 1
        else:
            alcohol = 0
        student_data = {
            "matric": students_data.ID[i],
            "sex": students_data.sex[i],
            "country": students_data.country[i],
            "school": school,
            "sleep_pref": students_data.sleep[i],
            "suite_pref": students_data.suite_pref[i],
            "cleanliness_pref": students_data.cleanliness[i],
            "alcohol_pref": alcohol,
            "gender_pref": students_data.gender_pref[i],
        }
        new_student = Student(**student_data)
        students.append(new_student)
    return students


def main():
    if len(sys.argv) != 2:
        print("Wrong format! Please type 'python main.py [csv_file]'")
        return
    csv_path = sys.argv[1]
    with open(csv_path) as csv_file:
        students_data = pd.read_csv(csv_file)
    students = add_students(students_data)
    suites = []
    for i in range(math.ceil(len(students)/6)):
        suites.append(Suite(i, 6))
    allocations = {}
    for i in range(100):
        suite_allocation = SuiteAllocation(students, suites)
        suite_allocation.match()
        global_score = suite_allocation.global_score()
        allocated_suites = suite_allocation.get_allocation().copy()
        print(f"Global score: {global_score}")
        suite_allocation.clean_up()
        allocations[global_score] = allocated_suites
    list_of_suites = allocations[min(allocations)]
    allocated_suites = []
    for i, list_of_students in enumerate(list_of_suites):
        suite = Suite(i, 6)
        suite.students = list_of_students
        allocated_suites.append(suite)
    scores = []
    for suite in allocated_suites:
        scores.append(calculate_score(suite, student=None))
    print(f"\nFinal score: {np.mean(scores)}")
    suites_data = {
        "Suite": [repr(suite) for suite in allocated_suites],
        "Num_students": [len(suite.students) for suite in allocated_suites],
        "Countries": [[student.country for student in suite.students] for suite in allocated_suites],
        "Citizenship Diversity": [suite.citizenship_diversity_score() for suite in allocated_suites],
        "Country Diversity": [suite.country_diversity_score() for suite in allocated_suites],
        "Schools": [[student.school for student in suite.students] for suite in allocated_suites],
        "School Diversity": [suite.school_diversity_score() for suite in allocated_suites],
        "Sleep Prefs": [[student.sleep_pref for student in suite.students] for suite in allocated_suites],
        "Sleep Prefs Similarity": [suite.sleep_pref_score() for suite in allocated_suites],
        "Suite Prefs": [[student.suite_pref for student in suite.students] for suite in allocated_suites],
        "Suite Prefs Similarity": [suite.suite_pref_score() for suite in allocated_suites],
        "Cleanliness Prefs": [[student.cleanliness_pref for student in suite.students] for suite in allocated_suites],
        "Cleanliness Prefs Similarity": [suite.cleanliness_pref_score() for suite in allocated_suites],
        "Alcohol Prefs": [[student.alcohol_pref for student in suite.students] for suite in allocated_suites],
        "Alcohol Prefs Similarity": [suite.alcohol_pref_score() for suite in allocated_suites],
    }
    suites_df = pd.DataFrame(suites_data, columns=suites_data.keys())
    suites_df.to_csv("output.csv", index=False)


if __name__ == "__main__":
    main()
