import math
import random
import itertools

import numpy as np
from typing import List

from ASAP.backend import match
from ASAP.backend import scoring
from ASAP.backend.student import Citizenship
from ASAP.backend.student import StudentData


class SuiteAllocation:
    class SuiteData:
        def __init__(self, suite_num, capacity, accessibility=False):
            self.suite_num = suite_num
            self.accessibility = accessibility
            self._capacity = capacity
            self.vacancies = capacity
            self.students = []
            self.rc = None
            self.rca = None
            self.allowable_rcs = {"Saga", "Elm", "Cendana"}

        @property
        def capacity(self):
            return self._capacity

        def add_student(self, student):
            self.students.append(student)
            self.vacancies -= 1
            if student.data.accessibility:
                self._capacity -= 1
                self.vacancies -= 1
                self.accessibility = True
                self.suite_num += " (Accessibility)"
            for rc in self.allowable_rcs.copy():
                if rc not in student.data.available_rcs:
                    self.allowable_rcs.remove(rc)

        def __repr__(self):
            return str(self.suite_num)

        def __str__(self):
            return str(self.suite_num)

    def __init__(self, students, name, num_a11y_students):
        self.students: List[StudentData] = students.copy()
        self.student_results = []
        self.total_students = len(students)
        self.num_a11y_students = num_a11y_students
        self.num_sextets = math.ceil((self.total_students - (self.num_a11y_students * 5)) / 6)
        self.num_a11y_suites = self.num_a11y_students
        self.batch_size = self.num_sextets + self.num_a11y_suites
        # self.batch_size = math.ceil(self.total_students/6)
        self.suites = [SuiteAllocation.SuiteData(f"FY {name} Suite {i:02d}", 6)
                       for i in range(1, self.batch_size + 1)]
        self.batches = self.split_into_batches()

    @staticmethod
    def get_citizenship(student):
        if student.citizenship == Citizenship.LOCAL:
            return 0
        else:
            return 1

    def split_into_batches(self):
        random.shuffle(self.students)
        local_students = [student for student in self.students
                          if student.citizenship == Citizenship.LOCAL and not student.accessibility]
        local_a11y = [student for student in self.students
                      if student.citizenship == Citizenship.LOCAL and student.accessibility]
        intl_students = [student for student in self.students
                         if student.citizenship == Citizenship.INTERNATIONAL and not student.accessibility]
        intl_a11y = [student for student in self.students
                     if student.citizenship == Citizenship.INTERNATIONAL and student.accessibility]

        # sorted_students = sorted(self.students, key=self.get_citizenship)
        sorted_students = local_a11y + local_students + intl_students
        for student in intl_a11y:
            sorted_students.insert(3 * self.batch_size, student)
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
        self.allocate_last_batch()

    def allocate_first_batch(self):
        students = self.batches.pop(0)
        student_results = match.SuiteRound.first_round(students, self.suites)
        self.student_results.extend(student_results)

    def allocate_remaining_batches(self, suite_propose=True):
        """
        TODO: Can refactor this to calculating the scores for every suite-student pairing first.
            Then, generate the ranking for both students and suites.
        """
        for i in range(4):
            students = self.batches.pop(0)
            student_results = match.SuiteRound(students, self.suites, suite_propose).run_match()
            self.student_results.extend(student_results)

    def allocate_last_batch(self, suite_propose=True):
        # In the last batch, only use sextets, because a11y suites would have reached capacity (5 rooms) already.
        students = self.batches.pop(0)
        sextets = [suite for suite in self.suites if not suite.accessibility]
        student_results = match.SuiteRound(students, sextets, suite_propose).run_match()
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
