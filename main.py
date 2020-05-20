import random
import enum
import math
import statistics


class Citizenship(enum.Enum):
    INTERNATIONAL = "International"
    LOCAL = "Local"


class Student:
    def __init__(self, matric, citizenship, preference1, preference2):
        self.matric = matric
        self.citizenship = citizenship
        self.preference1 = preference1
        self.preference2 = preference2
        self.suite = None
        self.scores = {}
        self.choices = []

    def __repr__(self):
        return f"{self.matric}: {self.citizenship}, {self.preference1}, {self.preference2}"

    def __str__(self):
        return f"{self.matric}: {self.citizenship}, {self.preference1}, {self.preference2}"

    def generate_score(self, suite):
        if suite in self.scores:
            return self.scores[suite]
        else:
            score = calculate_score(suite, self)
            suite.scores[self] = score
            return score

    def generate_preferences(self, suites):
        self.choices = sorted(suites, key=self.generate_score)


class Suite:
    def __init__(self, suite_num, capacity):
        self.suite_num = suite_num
        self.capacity = capacity
        # I am currently not taking capacity into consideration
        self.students = []
        self.scores = {}
        self.choices = []
        self.current_choice = None

    def add_student(self, student):
        self.students.append(student)

    def generate_score(self, student):
        if student in self.scores:
            return self.scores[student]
        else:
            score = calculate_score(self, student)
            student.scores[self] = score
            return score

    def generate_preferences(self, students):
        self.choices = sorted(students, key=self.generate_score)


def calculate_score(suite, student):
    preference1 = [student.preference1]
    preference1.extend(student.preference1 for student in suite.students)
    preference2 = [student.preference2]
    preference2.extend(student.preference2 for student in suite.students)
    sub_scores = (statistics.stdev(preference1), statistics.stdev(preference2))
    score = statistics.mean(sub_scores)
    return score


class SuiteAllocation:
    def __init__(self, students, suites):
        self.students = students
        self.total_students = len(students)
        self.all_suites = suites
        self.suites = []
        self.batch_size = math.ceil(self.total_students/6)
        self.batches = self.split_into_batches()
        self.allocate_first_batch()

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
                student.generate_preferences(self.suites)
            for suite in self.suites:
                suite.generate_preferences(students)
            self.gale_shapley(students)

    def gale_shapley(self, students):
        # Student propose
        unallocated_students = students
        while unallocated_students:
            student = unallocated_students.pop(0)
            suite = student.choices.pop(0)
            if suite.current_choice is None:
                suite.current_choice = student
                student.suite = suite
            elif suite.choices.index(student) < suite.choices.index(suite.current_choice):
                suite.current_choice.suite = None
                unallocated_students.append(suite.current_choice)
                suite.current_choice = student
                student.suite = suite
            elif student.choices:
                # still have other choices
                unallocated_students.append(student)
        for student in students:
            student.scores = {}
            student.choices = []
        for suite in self.suites:
            if suite.current_choice:
                suite.students.append(suite.current_choice)
                suite.current_choice = None
                suite.capacity -= 1
            suite.scores = {}
            suite.choices = []


def mock_student_data(n):
    student_data = []
    for i in range(n):
        matric = i
        citizenship = random.choice(list(Citizenship))
        preference1 = random.randint(1, 4)
        preference2 = random.randint(1, 4)
        student_data.append([matric, citizenship, preference1, preference2])
    return student_data


def add_students(students_data):
    students = []
    for student_data in students_data:
        new_student = Student(*student_data)
        students.append(new_student)
    return students


def main():
    students_data = mock_student_data(120)
    students = add_students(students_data)
    suites = []
    for i in range(math.ceil(len(students)/6)):
        suites.append(Suite(i, 6))
    suite_allocation = SuiteAllocation(students, suites)
    suite_allocation.allocate_remaining_batches()
    for suite in suite_allocation.suites:
        print(suite.students)



if __name__ == "__main__":
    main()
