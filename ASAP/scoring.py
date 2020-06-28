import math
import itertools

from ASAP.student import Citizenship


def calculate_score(suite, student):
    # TODO: Replace math.inf with a large increase that changes depending on the severity of imbalance
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
    # Magic numbers are 2 2 1.5 0.5 for np.std and 1.73 1.73 1.41 1 for pairwise_root_diff
    sleep_prefs = get_score([student.sleep_pref for student in students], MaxScores.get("sleep_pref"))
    suite_prefs = get_score([student.suite_pref for student in students], MaxScores.get("suite_pref"))
    cleanliness_prefs = get_score([student.cleanliness_pref for student in students], MaxScores.get("cleanliness_pref"))
    alcohol_prefs = get_score([student.alcohol_pref for student in students], MaxScores.get("alcohol_pref"))
    score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    return score


def get_max_score(unique_options):
    combinations = list(itertools.combinations_with_replacement(unique_options, 5))
    scores = [pairwise_root_diff(combination) for combination in combinations]
    return max(scores)


def get_score(values, max_score, higher_better=False):
    score = pairwise_root_diff(values) / max_score
    if higher_better:
        return 1 - score
    return score


def pairwise_root_diff(given_list):
    length = len(given_list)
    sum_of_diffs = sum(math.sqrt(abs(item - given_list[i]))
                       for n, item in enumerate(given_list)
                       for i in range(n + 1, length))
    average = sum_of_diffs / math.comb(length, 2)
    return average


def calculate_success(students):
    citizenship = citizenship_diversity_score(students)
    school_diversity = school_diversity_score(students)
    sleep_prefs = sleep_pref_score(students)
    suite_prefs = suite_pref_score(students)
    cleanliness_prefs = cleanliness_pref_score(students)
    alcohol_prefs = alcohol_pref_score(students)
    demographic_score = 0.6 * citizenship + 0.4 * school_diversity
    pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    score = 0.4 * demographic_score + 0.6 * pref_score
    return score


def citizenship_diversity_score(students):
    citizenships = [student.citizenship for student in students]
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


def country_diversity_score(students):
    overseas_countries = [student.country for student in students if student.country != "Singapore"]
    if len(overseas_countries) == len(set(overseas_countries)):
        return 1
    elif len(overseas_countries) - len(set(overseas_countries)) == 1:
        return 0.5
    else:
        return 0


def school_diversity_score(students):
    overseas_countries = [student.school for student in students]
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


def sleep_pref_score(students):
    return get_score([student.sleep_pref for student in students], MaxScores.get("sleep_pref"), higher_better=True)


def suite_pref_score(students):
    return get_score([student.suite_pref for student in students], MaxScores.get("suite_pref"), higher_better=True)


def cleanliness_pref_score(students):
    return get_score([student.cleanliness_pref for student in students], MaxScores.get("cleanliness_pref"), higher_better=True)


def alcohol_pref_score(students):
    return get_score([student.alcohol_pref for student in students], MaxScores.get("alcohol_pref"), higher_better=True)


class MaxScores:
    max_scores = {}

    @staticmethod
    def set_max_scores(living_pref_unique_options):
        for living_pref, unique_options in living_pref_unique_options.items():
            MaxScores.max_scores[living_pref] = get_max_score(unique_options)

    @staticmethod
    def get(living_pref):
        try:
            return MaxScores.max_scores[living_pref]
        except KeyError:
            raise RuntimeError(f"Max score has not yet been set for {living_pref}.")
