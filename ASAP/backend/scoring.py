import math
import itertools

from ASAP.backend.student import Citizenship

SOUTH_ASIAN_COUNTRIES = {"India", "Pakistan", "Sri Lanka", "Bangladesh", "Nepal"}
ASIAN_COUNTRIES = {"Philippines", "Pakistan", "India", "Indonesia", "Japan", "China", "Taiwan", "Malaysia", "Thailand",
                   "Hong Kong", "South Korea", "Vietnam", "Bhutan", "Macau"}
NON_ASIAN_COUNTRIES = {"Ethiopia", "Kenya", "Tanzania", "Rwanda", "Cote D'Ivoire", "United States", "Canada", "Brazil",
                       "Paraguay", "New Zealand", "Germany", "Austria", "Netherlands", "Azerbaijan", "Sweden",
                       "United Kingdom", "Turkey", "Poland", "Mongolia", "Jordan"}


def calculate_score(suite, student):
    """
    Lower score is better

    Args:
        suite: SuiteAllocation.SuiteData
        student: SuiteRound.StudentMatchee

    Returns:

    """
    if student is None:
        students = suite.students
    else:
        students = suite.students + [student]

    overseas_countries = [country for student in students for country in student.data.country if country != "Singapore"]
    duplicate_overseas_countries_score = len(overseas_countries) - len(set(overseas_countries)) * 120

    schools = [student.data.school for student in students]
    duplicate_schools_score = len(schools) - len(set(schools)) * 120

    score = living_pref_scores(students)

    # Magic numbers are 2 2 1.5 0.5 for np.std and 1.73 1.73 1.41 1 for pairwise_root_diff
    # sleep_prefs = get_score([student.sleep_pref for student in students], Scores.get_max("sleep_pref"))
    # suite_prefs = get_score([student.suite_pref for student in students], Scores.get_max("suite_pref"))
    # cleanliness_prefs = get_score([student.cleanliness_pref for student in students], Scores.get_max("cleanliness_pref"))
    # alcohol_prefs = get_score([student.alcohol_pref for student in students], Scores.get_max("alcohol_pref"))

    # score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    score += duplicate_overseas_countries_score + duplicate_schools_score

    # Prevent 4 : 1 ratio as much as possible for non-accessibility suites
    citizenships = [student.data.citizenship for student in students]
    if citizenships.count(Citizenship.LOCAL) == 4 and citizenships.count(Citizenship.INTERNATIONAL) == 2:
        score -= 1000

    # Prevent 4 : 1 ratio or 3 intl : 2 local ratio for accessibility
    if ((suite.accessibility or student.data.accessibility) and citizenships.count(Citizenship.LOCAL) == 3
            and citizenships.count(Citizenship.INTERNATIONAL) == 1):
        score -= 2000

    # Prevent more than one accessibility student fom being allocated to the same suite
    if student.data.accessibility and suite.accessibility:
        score += 2000

    # Check allowable RCs
    for rc in student.data.available_rcs:
        if rc in suite.allowable_rcs:
            break
    else:
        score += 2000

    # TEMPORARY FIXES FOR 2021 ALLOCATION (CLASS OF 2025) #
    # Prevent South Asian countries from being in the same suite
    if len(SOUTH_ASIAN_COUNTRIES.intersection(set(overseas_countries))) > 1:
        score += 2000

    # Prevent non-asian countries from being in the same suite
    if len(NON_ASIAN_COUNTRIES.intersection(set(overseas_countries))) > 1:
        score += 2000

    # Prevent duplicate countries
    if len(overseas_countries) - len(set(overseas_countries)) > 0:
        score += 2000

    # Prevent duplicate schools
    if len(schools) - len(set(schools)) > 0:
        score += 2000

    return score


def living_pref_score(students, living_pref, higher_better=False):
    return get_score([student.data.living_prefs[living_pref] for student in students],
                     Scores.get_max(living_pref),
                     higher_better)


def living_pref_scores(students, higher_better=False):
    return sum(living_pref_score(students, living_pref, higher_better) * weight
               for living_pref, weight in Scores.weights.items())


def rca_demographic_scores(suite1, suite2):
    citizenships = ([student.data.citizenship for student in suite1.students]
                    + [student.data.citizenship for student in suite2.students])
    num_locals = citizenships.count(Citizenship.LOCAL)
    num_intls = citizenships.count(Citizenship.INTERNATIONAL)

    citizenship_diversity = abs(num_locals - num_intls) / 2

    overseas_countries = ([country for student in suite1.students
                           for country in student.data.country if country != "Singapore"]
                          + [country for student in suite2.students
                             for country in student.data.country if country != "Singapore"])
    country_diversity = len(overseas_countries) - len(set(overseas_countries)) / 3

    schools = ([student.data.school for student in suite1.students]
               + [student.data.school for student in suite2.students])
    school_diversity = len(schools) - len(set(schools)) / 3

    score = 0.4 * citizenship_diversity + 0.3 * country_diversity + 0.3 * school_diversity

    # Prevent 3 : 2 + 4 : 2 and 4 : 2 + 4 : 2 ratio
    if (num_locals == 7 and num_intls == 4) or (num_locals == 8 and num_intls == 4):
        score += 2000

    # TEMPORARY FIXES FOR 2021 ALLOCATION (CLASS OF 2025) #
    # Prevent South Asian countries from being in the same RCA
    if len(SOUTH_ASIAN_COUNTRIES.intersection(set(overseas_countries))) > 1:
        score += 2000
    # Make sure RCA groupings have one student from China, to prevent leftover female suites from having too many
    # students from China
    if "China" not in overseas_countries:
        score += 2000

    return score


def calculate_rca_score(suite1, suite2, demographic_weight=0.8):
    # sleep_prefs = abs(sum(student.sleep_pref for student in suite1.students) / len(suite1.students)
    #                   - sum(student.sleep_pref for student in suite2.students) / len(suite2.students))
    # suite_prefs = abs(sum(student.suite_pref for student in suite1.students) / len(suite1.students)
    #                   - sum(student.suite_pref for student in suite2.students) / len(suite2.students))
    # cleanliness_prefs = abs(sum(student.cleanliness_pref for student in suite1.students) / len(suite1.students)
    #                         - sum(student.cleanliness_pref for student in suite2.students) / len(suite2.students))
    # alcohol_prefs = abs(sum(student.alcohol_pref for student in suite1.students) / len(suite1.students)
    #                     - sum(student.alcohol_pref for student in suite2.students) / len(suite2.students))
    # pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    pref_score = living_pref_scores(suite1.students + suite2.students)
    demographic_score = rca_demographic_scores(suite1, suite2)
    score = demographic_weight * demographic_score + (1 - demographic_weight) * pref_score

    # Check allowable RCs
    allowable_rcs = suite1.allowable_rcs.intersection(suite2.allowable_rcs)
    if not allowable_rcs:
        score += 2000

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


def demographic_scores(students):
    citizenship_diversity = citizenship_diversity_score(students)
    country_diversity = country_diversity_score(students)
    school_diversity = school_diversity_score(students)
    return 0.4 * citizenship_diversity + 0.3 * country_diversity + 0.3 * school_diversity


def calculate_success(students, demographic_weight=0.4):
    # sleep_prefs = sleep_pref_score(students)
    # suite_prefs = suite_pref_score(students)
    # cleanliness_prefs = cleanliness_pref_score(students)
    # alcohol_prefs = alcohol_pref_score(students)
    demographic_score = demographic_scores(students)
    # pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
    pref_score = living_pref_scores(students, higher_better=True)
    score = demographic_weight * demographic_score + (1 - demographic_weight) * pref_score
    return score


# def get_suite_score(citizenship, school_diversity, sleep_prefs, suite_prefs, cleanliness_prefs, alcohol_prefs, demographic_weight=0.4):
#     demographic_score = 0.6 * citizenship + 0.4 * school_diversity
#     pref_score = 0.2 * sleep_prefs + 0.4 * suite_prefs + 0.2 * cleanliness_prefs + 0.2 * alcohol_prefs
#     score = demographic_weight * demographic_score + (1 - demographic_weight) * pref_score
#     return score


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
    overseas_countries = [country for student in students for country in student.data.country if country != "Singapore"]
    if len(overseas_countries) == len(set(overseas_countries)):
        return 1
    elif len(overseas_countries) - len(set(overseas_countries)) == 1:
        return 0.5
    else:
        return 0


def school_diversity_score(students):
    schools = [student.data.school for student in students]
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


# def sleep_pref_score(students):
#     return get_score([student.sleep_pref for student in students], Scores.get_max("sleep_pref"), higher_better=True)
#
#
# def suite_pref_score(students):
#     return get_score([student.suite_pref for student in students], Scores.get_max("suite_pref"), higher_better=True)
#
#
# def cleanliness_pref_score(students):
#     return get_score([student.cleanliness_pref for student in students], Scores.get_max("cleanliness_pref"), higher_better=True)
#
#
# def alcohol_pref_score(students):
#     return get_score([student.alcohol_pref for student in students], Scores.get_max("alcohol_pref"), higher_better=True)


class Scores:
    max_scores = {}
    weights = {}

    @staticmethod
    def set_max_scores(living_pref_unique_options):
        for living_pref, unique_options in living_pref_unique_options.items():
            Scores.max_scores[living_pref] = get_max_score(unique_options)

    @staticmethod
    def set_weights(weights):
        Scores.weights = weights

    @staticmethod
    def get_max(living_pref):
        try:
            return Scores.max_scores[living_pref]
        except KeyError:
            raise RuntimeError(f"Max score has not yet been set for {living_pref}.")
