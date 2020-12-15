import math
import itertools

from ASAP.backend.student import Citizenship


def calculate_score(suite, student):
    if student is None:
        students = suite.students
    else:
        students = suite.students + [student]

    overseas_countries = [student.country for student in students if student.citizenship == Citizenship.INTERNATIONAL]
    duplicate_overseas_countries_score = len(overseas_countries) - len(set(overseas_countries)) * 120

    schools = [student.school for student in students]
    duplicate_schools_score = len(schools) - len(set(schools)) * 100

    # Magic numbers are 2 2 1.5 0.5 for np.std and 1.73 1.73 1.41 1 for pairwise_root_diff
    sleep_prefs = get_score([student.sleep_pref for student in students], MaxScores.get("sleep_pref"))
    suite_prefs = get_score([student.suite_pref for student in students], MaxScores.get("suite_pref"))
    cleanliness_prefs = get_score([student.cleanliness_pref for student in students], MaxScores.get("cleanliness_pref"))
    alcohol_prefs = get_score([student.alcohol_pref for student in students], MaxScores.get("alcohol_pref"))

    score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    score += duplicate_overseas_countries_score + duplicate_schools_score

    citizenships = [student.citizenship for student in students]
    if citizenships.count(Citizenship.LOCAL) == 4 and citizenships.count(Citizenship.INTERNATIONAL) == 2:
        score -= 1000
    return score


def calculate_rca_score(suite1, suite2):
    sleep_prefs = abs(sum(student.sleep_pref for student in suite1.students) / len(suite1.students)
                      - sum(student.sleep_pref for student in suite2.students) / len(suite2.students))
    suite_prefs = abs(sum(student.suite_pref for student in suite1.students) / len(suite1.students)
                      - sum(student.suite_pref for student in suite2.students) / len(suite2.students))
    cleanliness_prefs = abs(sum(student.cleanliness_pref for student in suite1.students) / len(suite1.students)
                            - sum(student.cleanliness_pref for student in suite2.students) / len(suite2.students))
    alcohol_prefs = abs(sum(student.alcohol_pref for student in suite1.students) / len(suite1.students)
                        - sum(student.alcohol_pref for student in suite2.students) / len(suite2.students))

    overseas_countries = ([student.country for student in suite1.students if student.country != "Singapore"]
                          + [student.country for student in suite2.students if student.country != "Singapore"])
    country_diversity = len(overseas_countries) - len(set(overseas_countries)) / 3

    schools = [student.school for student in suite1.students] + [student.school for student in suite2.students]
    school_diversity = len(schools) - len(set(schools)) / 3

    pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    demographic_score = 0.6 * country_diversity + 0.4 * school_diversity
    score = 0.6 * demographic_score + 0.4 * pref_score
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


def calculate_success(students, demographic_weight=0.4):
    citizenship = citizenship_diversity_score(students)
    school_diversity = school_diversity_score(students)
    sleep_prefs = sleep_pref_score(students)
    suite_prefs = suite_pref_score(students)
    cleanliness_prefs = cleanliness_pref_score(students)
    alcohol_prefs = alcohol_pref_score(students)
    demographic_score = 0.6 * citizenship + 0.4 * school_diversity
    pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    score = demographic_weight * demographic_score + (1 - demographic_weight) * pref_score
    return score


def get_suite_score(citizenship, school_diversity, sleep_prefs, suite_prefs, cleanliness_prefs, alcohol_prefs, demographic_weight=0.4):
    demographic_score = 0.6 * citizenship + 0.4 * school_diversity
    pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    score = demographic_weight * demographic_score + (1 - demographic_weight) * pref_score
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
    schools = [student.school for student in students]
    if len(schools) == len(set(schools)):
        return 1
    elif len(schools) - len(set(schools)) == 1:
        return 0.5
    elif len(schools) - len(set(schools)) == 2:
        return 0.3
    elif len(schools) - len(set(schools)) == 3:
        return 0.2
    elif len(schools) - len(set(schools)) == 4:
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
