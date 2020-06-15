import math

from ASAP.student import Citizenship


def calculate_score(suite, student):
    if student is None:
        students = [student.data for student in suite.students]
    else:
        students = [student.data for student in suite.students] + [student]
    overseas_countries = [student.country for student in students if student.citizenship == Citizenship.INTERNATIONAL]
    if len(overseas_countries) != len(set(overseas_countries)):  # Check for duplicate overseas countries
        return math.inf
    schools = [student.school for student in students]
    if len(schools) != len(set(schools)):  # Check for duplicate schools
        return math.inf
    # Magic numbers are 2 2 1.5 0.5 for np.std and 1.73 1.73 1.41 1 for pairwise_root_diff
    sleep_prefs = pairwise_root_diff([student.sleep_pref for student in students]) / 1.73
    suite_prefs = pairwise_root_diff([student.suite_pref for student in students]) / 1.73
    cleanliness_prefs = pairwise_root_diff([student.cleanliness_pref for student in students]) / 1.41
    alcohol_prefs = pairwise_root_diff([student.alcohol_pref for student in students]) / 1
    score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    return score


def pairwise_root_diff(given_list):
    length = len(given_list)
    sum_of_diffs = sum(math.sqrt(abs(item - given_list[i]))
                       for n, item in enumerate(given_list)
                       for i in range(n + 1, length))
    average = sum_of_diffs / math.comb(length, 2)
    return average


def calculate_success(suite, student):
    """

    TODO: calculate suite success score
    """
    pass


def citizenship_diversity_score(students):
    citizenships = [student.data.citizenship for student in students]
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
    overseas_countries = [student.data.country for student in students if student.data.country != "Singapore"]
    if len(overseas_countries) == len(set(overseas_countries)):
        return 1
    elif len(overseas_countries) - len(set(overseas_countries)) == 1:
        return 0.5
    else:
        return 0


def school_diversity_score(students):
    overseas_countries = [student.data.school for student in students]
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
    sleep_prefs = pairwise_root_diff([student.data.sleep_pref for student in students]) / 1.73
    return 1 - sleep_prefs


def suite_pref_score(students):
    suite_prefs = pairwise_root_diff([student.data.suite_pref for student in students]) / 1.73
    return 1 - suite_prefs


def cleanliness_pref_score(students):
    cleanliness_prefs = pairwise_root_diff([student.data.cleanliness_pref for student in students]) / 1.41
    return 1 - cleanliness_prefs


def alcohol_pref_score(students):
    alcohol_prefs = pairwise_root_diff([student.data.alcohol_pref for student in students]) / 1
    return 1 - alcohol_prefs