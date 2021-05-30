import collections
import random

from ASAP.backend import scoring
from ASAP.backend.student import StudentData


class SuiteRound:
    class StudentMatchee:
        """
            scores: A dictionary mapping suite objects to the score given to that suite combined with the student
            ranking: A list that contains suite objects. The order represents the student's preference
        """
        def __init__(self, student_data: StudentData):
            self.data = student_data
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        # def __getattr__(self, attr):
        #     return getattr(self.data, attr)

        @property
        def suite(self):
            return self.current_choice

        def generate_score(self, suite_matchee):
            """Returns a score that indicates how good of a fit a suite is for the student.

            This score is identical for the suite. Therefore, if the score has already been calculated

            Stores the score in a dictionary so that the suite object does not need to

            Args:
                suite_matchee: A SuiteMatchee object.
            """
            if suite_matchee in self.scores:
                return self.scores[suite_matchee]
            else:
                score = scoring.calculate_score(suite_matchee.data, self)
                suite_matchee.scores[self] = score
                return score

        def generate_ranking(self, suites):
            self.ranking = collections.deque(sorted(suites, key=self.generate_score))

    class SuiteMatchee:
        def __init__(self, suite):
            self.data = suite
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        def add_student(self, student):
            if student:
                self.data.add_student(student)

        def generate_score(self, student_matchee):
            if student_matchee in self.scores:
                return self.scores[student_matchee]
            else:
                score = scoring.calculate_score(self.data, student_matchee)
                student_matchee.scores[self] = score
                return score

        def generate_ranking(self, students):
            self.ranking = collections.deque(sorted(students, key=self.generate_score))

    def __init__(self, students, suites, suite_propose=True):
        self.students = [SuiteRound.StudentMatchee(student) for student in students]
        self.suites = [SuiteRound.SuiteMatchee(suite) for suite in suites if suite.vacancies > 0]
        self.suite_propose = suite_propose
        self.proposers = None

    @staticmethod
    def first_round(batch, suites):
        students = [SuiteRound.StudentMatchee(student) for student in batch]
        suites = [SuiteRound.SuiteMatchee(suite) for suite in suites if suite.vacancies > 0]
        for i, student in enumerate(students):
            suite = suites[i]
            student.current_choice = suite
            suite.add_student(student)
        return students

    def run_match(self):
        for student in self.students:
            student.generate_ranking(self.suites)
        for suite in self.suites:
            suite.generate_ranking(self.students)
        if self.suite_propose:
            self.proposers = self.suites
        else:
            self.proposers = self.students
        gale_shapley(self.proposers)
        for suite in self.suites:
            suite.add_student(suite.current_choice)
        return self.students


class RCAMatch:
    def __init__(self, female_suites, male_suites, saga, elm, cendana, female_suites_propose=True):
        self.female_suites = [RCAMatch.Matchee(suite) for suite in female_suites]
        self.male_suites = [RCAMatch.Matchee(suite) for suite in male_suites]
        self.female_suites_propose = female_suites_propose
        self.proposers = None
        self.saga = saga
        self.elm = elm
        self.cendana = cendana
        if saga + elm + cendana < len(self.female_suites) + len(self.male_suites):
            raise ValueError("Not enough suites.")


    class Matchee:
        def __init__(self, suite):
            self.data = suite
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        def generate_score(self, suite_matchee):
            if suite_matchee in self.scores:
                return self.scores[suite_matchee]
            else:
                score = scoring.calculate_rca_score(self.data, suite_matchee.data)
                suite_matchee.scores[self] = score
                return score

        def generate_ranking(self, suite):
            self.ranking = collections.deque(sorted(suite, key=self.generate_score))

    def run_match(self):  # NEED TO PREVENT 4-2 suites from being paired with 3-2 suites (Citizenship)
        for female_suite in self.female_suites:
            female_suite.generate_ranking(self.male_suites)
        for male_suite in self.male_suites:
            male_suite.generate_ranking(self.female_suites)
        if self.female_suites_propose:
            self.proposers = self.female_suites
        else:
            self.proposers = self.male_suites
        gale_shapley(self.proposers)
        suites = self.female_suites if len(self.female_suites) > len(self.male_suites) else self.male_suites
        random.shuffle(suites)
        i = 1
        for suite in suites:
            if not suite.current_choice:
                suite.data.rca = "Unallocated"
                suite.data.rc = "Unallocated"
            else:
                rc = self.get_rc()
                suite.data.rc = rc
                suite.current_choice.data.rc = rc
                suite.current_choice.data.rca = f"RCA {i:02d}"
                suite.data.rca = f"RCA {i:02d}"
                i += 1

    def get_rc(self):
        i = random.randint(1, 3)
        if i == 1:
            if self.saga >= 2:
                self.saga -= 2
                return "Saga"
        elif i == 2:
            if self.elm >= 2:
                self.elm -= 2
                return "Elm"
        elif i == 3:
            if self.cendana >= 2:
                self.cendana -= 2
                return "Cendana"
        return self.get_rc()


def gale_shapley(proposers):
    def unmatch(old_proposer, current_acceptor):
        old_proposer.current_choice = None
        unallocated.append(old_proposer)
        current_acceptor.current_choice = None

    def match(current_proposer, current_acceptor):
        current_acceptor.current_choice = current_proposer
        current_proposer.current_choice = current_acceptor

    unallocated = collections.deque(proposers)
    while unallocated:
        proposer = unallocated.popleft()
        if proposer.ranking:
            acceptor = proposer.ranking.popleft()
            if acceptor.current_choice is None:
                match(proposer, acceptor)
            elif acceptor.ranking.index(proposer) < acceptor.ranking.index(acceptor.current_choice):
                unmatch(acceptor.current_choice, acceptor)
                match(proposer, acceptor)
            else:
                unallocated.append(proposer)
