import collections
import random

from ASAP import scoring


class SuiteRound:
    class StudentMatchee:
        """
            scores: A dictionary mapping suite objects to the score given to that suite combined with the student
            ranking: A list that contains suite objects. The order represents the student's preference
        """
        def __init__(self, student_data):
            self.data = student_data
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        def __getattr__(self, attr):
            return getattr(self.data, attr)

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
                score = scoring.calculate_score(suite_matchee.suite, self.data)
                suite_matchee.scores[self] = score
                return score

        def generate_ranking(self, suites):
            self.ranking = collections.deque(sorted(suites, key=self.generate_score))

    class SuiteMatchee:
        def __init__(self, suite):
            self.suite = suite
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        def __getattr__(self, attr):
            return getattr(self.suite, attr)

        def add_student(self, student):
            if student:
                self.suite.add_student(student)

        def generate_score(self, student_matchee):
            if student_matchee in self.scores:
                return self.scores[student_matchee]
            else:
                score = scoring.calculate_score(self.suite, student_matchee.data)
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

    class Matchee:
        def __init__(self, suite):
            self.data = suite
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        def __getattr__(self, attr):
            return getattr(self.data, attr)

        def generate_score(self, suite_matchee):
            if suite_matchee in self.scores:
                return self.scores[suite_matchee]
            else:
                score = scoring.calculate_rca_score(self.data, suite_matchee.data)
                suite_matchee.scores[self] = score
                return score

        def generate_ranking(self, suite):
            self.ranking = collections.deque(sorted(suite, key=self.generate_score))

    def run_match(self):
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
        for i, suite in enumerate(suites, start=1):
            rc1, rc2 = self.get_rc(suite.current_choice)
            suite.data.rca = "Unallocated RCA"
            suite.data.rc = rc1
            if suite.current_choice:
                if rc2:
                    suite.current_choice.data.rc = rc2
                    suite.current_choice.data.rca = "Unallocated RCA"
                else:
                    suite.current_choice.data.rc = rc1
                    suite.current_choice.data.rca = f"RCA {i:02d}"
                    suite.data.rca = f"RCA {i:02d}"

    def get_rc(self, has_sibling_suite):
        if has_sibling_suite:
            if self.saga >= 2:
                self.saga -= 2
                return "Saga", None
            elif self.elm >= 2:
                self.elm -= 2
                return "Elm", None
            elif self.cendana >= 2:
                self.cendana -= 2
                return "Cendana", None
            else:
                if self.saga >= 1 and self.elm >= 1:
                    return "Saga", "Elm"
                elif self.saga >= 1 and self.cendana >= 1:
                    return "Saga", "Cendana"
                elif self.elm >= 1 and self.cendana >= 1:
                    return "Elm", "Cendana"
                else:
                    raise RuntimeError("Not enough suites.")
        else:
            if self.saga >= 1:
                self.saga -= 1
                return "Saga", None
            elif self.elm >= 1:
                self.elm -= 1
                return "Elm", None
            elif self.cendana >= 1:
                self.cendana -= 1
                return "Cendana", None
            else:
                raise RuntimeError("Not enough suites.")


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
