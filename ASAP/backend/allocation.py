import math
import random
import itertools

import numpy as np

from ASAP.backend import match
from ASAP.backend import scoring
from ASAP.backend.student import Citizenship


class SuiteAllocation:
    class SuiteData:
        def __init__(self, suite_num, capacity):
            self.suite_num = suite_num
            self._capacity = capacity
            self.vacancies = capacity
            self.students = []
            self.rc = None
            self.rca = None

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

    def __init__(self, students, name):
        self.students = students.copy()
        self.student_results = []
        self.total_students = len(students)
        self.batch_size = math.ceil(self.total_students/6)
        self.suites = [SuiteAllocation.SuiteData(f"FY {name} Suite {i:02d}", 6) for i in range(1, self.batch_size + 1)]
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
        student_results = match.SuiteRound.first_round(students, self.suites)
        self.student_results.extend(student_results)

    def allocate_remaining_batches(self, suite_propose=True):
        """


        TODO: Can refactor this to calculating the scores for every suite-student pairing first.
            Then, generate the ranking for both students and suites.
        """
        for i in range(5):
            students = self.batches.pop(0)
            student_results = match.SuiteRound(students, self.suites, suite_propose).run_match()
            self.student_results.extend(student_results)

    def global_score(self):
        scores = []
        for suite in self.suites:
            # scores.append(scoring.calculate_score(suite, student=None))
            scores.append(scoring.calculate_success(suite.students))
        return np.mean(scores)

    def get_allocation(self):
        return self.suites.copy()

    def allocate_randomly(self):
        suites_cycle = itertools.cycle(self.suites)
        for student in self.students:
            suite = next(suites_cycle)
            suite.add_student(student)
