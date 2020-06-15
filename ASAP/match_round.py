import collections

from ASAP import scoring


class Match:
    class StudentMatchee:
        def __init__(self, student_data):
            self.data = student_data
            self.scores = {}
            self.ranking = None
            self.current_choice = None

        @property
        def suite(self):
            return self.current_choice

        def generate_score(self, suite_matchee):
            """Returns a score that indicates how good of a fit a suite is for the student.

            This score is identical for the suite. Therefore, if the score has already been calculated

            Stores the score in a dictionary so that the suite object does not need to

            Args:
                suite: A SuiteMatchee object.
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
        """
        Initialises GaleShapley object

        Args:
            proposer_rankings: A dict mapping proposers to their ranking of acceptors.
                               The proposers must consist of unique objects
                               The rankings must consist of unique acceptor objects
            acceptor_rankings: A dict mapping acceptors to their ranking of proposers
                               The acceptors must consist of unique objects
                               The rankings must consist of unique proposer objects
        """
        self.students = [Match.StudentMatchee(student) for student in students]
        self.suites = [Match.SuiteMatchee(suite) for suite in suites if suite.vacancies > 0]
        self.suite_propose = suite_propose
        self.proposers = None

    @staticmethod
    def first_round(batch, suites):
        students = [Match.StudentMatchee(student) for student in batch]
        suites = [Match.SuiteMatchee(suite) for suite in suites if suite.vacancies > 0]
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
        self.gale_shapley()
        for suite in self.suites:
            suite.add_student(suite.current_choice)
        return self.students

    def gale_shapley(self):
        def unmatch(old_proposer, current_acceptor):
            old_proposer.current_choice = None
            unallocated.append(old_proposer)
            current_acceptor.current_choice = None

        def match(current_proposer, current_acceptor):
            current_acceptor.current_choice = current_proposer
            current_proposer.current_choice = current_acceptor

        unallocated = collections.deque(self.proposers)
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
