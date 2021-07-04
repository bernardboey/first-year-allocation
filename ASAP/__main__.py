"""First Year Allocation

This script allows the user to allocate first-year students to suites according to preferences.

This script accepts the student data in a .csv file, which must be processed such that it has the following columns:
    * matric
    * sex
    * school
    * country
    * sleep_pref (values must be numeric e.g. 1 - 4)
    * suite_pref (values must be numeric e.g. 1 - 4)
    * cleanliness_pref (values must be numeric e.g. 1 - 4)
    * alcohol_pref (values must be numeric e.g. 0 - 1)
    * gender_pref

It is recommended that the .csv file be processed using data_cleaning.py which is packaged together with this script.
It is also recommended that a virtual environment be set up, and packages installed using requirements.txt

This file contains the following classes:
    * Student
    * Suite
    * SuiteAllocation

This file contains the following functions:
    * calculate_score - Takes in a suite and an optional student and returns a score that indicates how good a fit
        the students in the suite + the new student are for each other. A lower score is better.
    * add_students - Parses data from the student dataframe and returns a list of Student objects
    * main - The main function of the script that allocates suites, taking data from a .csv file

TODO: Check correctness of code (.copy()?)
"""

import sys
import os
import inspect
import collections
import datetime
import math
import random
from typing import Dict, List, Tuple

import pandas as pd

from ASAP.backend import match
from ASAP.backend import parser
from ASAP.backend.allocation import SuiteAllocation
from ASAP.backend import scoring
from ASAP.backend.student import StudentData


class ColumnType:
    def __init__(self, desc, mandatory: bool):
        self.desc = desc
        self.mandatory = mandatory


class ExclusiveColumnType(ColumnType):
    exclusive = True

    def __init__(self, *args, **kwargs):
        self.col = None
        self.index = None
        super().__init__(*args, **kwargs)

    @property
    def defined(self):
        return self.col and self.index is not None

    def reset(self):
        self.col = None
        self.index = None


class NonExclusiveColumnType(ColumnType):
    exclusive = False

    def __init__(self, *args, **kwargs):
        self.cols: List[str] = []
        self.indexes: List[int] = []
        super().__init__(*args, **kwargs)

    @property
    def defined(self):
        return self.cols and self.indexes

    def reset(self):
        self.cols = []
        self.indexes = []


class LivingPrefColumnType(NonExclusiveColumnType):

    def __init__(self, *args, **kwargs):
        self.text_to_num: List[Dict[str, int]] = []
        self.num_to_text: List[Dict[int, str]] = []
        self.weights: Dict[str, float] = {}
        self.selected_order: List[List[str]] = []
        super().__init__(*args, **kwargs)


class ASAP:
    RC_LIST = ("Saga", "Elm", "Cendana")
    RC_LIST_WITH_UNALLOCATED = (*RC_LIST, "Unallocated")

    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.students_df = pd.read_csv(filepath)
        self.verify_csv()

        self.total_students = len(self.students_df)
        self.colnames = list(self.students_df.columns)
        self.col_to_type: Dict[str, ColumnType] = {}

        self.ID = ExclusiveColumnType("Student ID", mandatory=True)
        self.SCHOOL = ExclusiveColumnType("School", mandatory=True)
        self.SEX = ExclusiveColumnType("Sex", mandatory=True)
        self.COUNTRY = NonExclusiveColumnType("Country", mandatory=True)
        self.LIVING_PREF = LivingPrefColumnType("Living Preference", mandatory=True)
        self.ACCESSIBILITY = ExclusiveColumnType("Accessibility", mandatory=True)
        self.AVAILABLE_RCS = ExclusiveColumnType("Available RCs", mandatory=True)
        self.OTHERS = NonExclusiveColumnType("Others", mandatory=False)
        self.COL_TYPES = [self.ID, self.SCHOOL, self.SEX, self.COUNTRY, self.ACCESSIBILITY, self.AVAILABLE_RCS,
                          self.LIVING_PREF, self.OTHERS]

        self.avail_suites_saga = 0
        self.avail_suites_elm = 0
        self.avail_suites_cendana = 0
        self.total_suites = 0
        self.required_suites = 0
        self.required_suites_male = 0
        self.required_suites_female = 0
        self.num_males = 0
        self.num_females = 0

        self.female_suites = None
        self.male_suites = None
        self.suites = None
        self.female_stats = {}
        self.male_stats = {}
        self.datetime = None

        self.col_types_defined = False
        self.living_pref_order_defined = False
        self.weights_defined = False
        self.options_defined = False
        self.allocation_completed = False

    def __str__(self):
        return f"<ASAP object>"

    def __repr__(self):
        return f"ASAP({self.filename})"

    def verify_csv(self):
        if self.students_df.isnull().values.any():
            raise ValueError(f"Number of missing values: {self.students_df.isnull().sum().sum()}. "
                             f"Please ensure there are no missing values.")

    def get_colnames_and_unique_values(self) -> Tuple[List[str], List[List[str]], List[List[str]]]:
        unique_values: List[List[str]] = [self.students_df[col].value_counts().index.tolist() for col in self.colnames]
        head_values: List[List[str]] = [self.students_df.loc[i, :].values.tolist() for i in range(5)]
        return self.colnames, unique_values, head_values

    def set_column_types(self, col_type_assoc: List[Tuple[str, str]]):
        if self.col_types_defined:
            for _type in self.COL_TYPES:
                _type.reset()
            self.col_to_type = {}
            self.col_types_defined = False

        # Shouldn't have duplicate colnames because pandas automatically renames, but just check to be sure.
        duplicate_colnames = [k for k, freq in collections.Counter(self.colnames).items() if freq > 1]
        if duplicate_colnames:
            raise ValueError(f"""There are duplicate column names: "{'", "'.join(duplicate_colnames)}". """
                             f"""Please close the program and change the column names before trying again.""")

        for col, type_desc in col_type_assoc:
            for _type in self.COL_TYPES:
                if type_desc == _type.desc:
                    if isinstance(_type, ExclusiveColumnType):
                        # Check that only one column for each exclusive type
                        if _type.col:
                            raise ValueError(f"You selected more than one column for '{_type.desc}'. "
                                             f"Please select only one column.")
                        _type.col = col
                        _type.index = self.colnames.index(col)
                    else:
                        _type.cols.append(col)
                        _type.indexes.append(self.colnames.index(col))
                    self.col_to_type[col] = _type

        # Check that all mandatory types have corresponding columns
        for _type in self.COL_TYPES:
            if _type.mandatory and not _type.defined:
                raise ValueError(f"You did not select any column for '{_type.desc}'. Please try again.")

        # Check that Sex is just M and F
        self.students_df[self.SEX.col] = self.students_df[self.SEX.col].str.upper()
        for value in self.students_df[self.SEX.col].unique():
            if value not in ("M", "F"):
                raise ValueError(f"Column that represents '{self.SEX.desc}' should only contain 'M' and 'F'. "
                                 f"Currently it contains '{value}' as well.")
        self.num_males = len(self.students_df[self.students_df[self.SEX.col] == 'M'])
        self.num_females = len(self.students_df[self.students_df[self.SEX.col] == 'F'])

        # Check that Singapore is present in the country column
        if "Singapore" not in self.students_df[self.COUNTRY.cols[0]].unique():
            raise ValueError(f"The value 'Singapore' cannot be found in the column you selected for "
                             f"'{self.COUNTRY.desc}' (column '{self.COUNTRY.cols[0]}'). "
                             f"Did you identify the columns correctly?")

        # Check that ID column in unique
        if not self.students_df[self.ID.col].is_unique:
            raise ValueError(f"The column that you selected for '{self.ID.desc}' (column '{self.ID.col}') "
                             f"contains duplicate values. Did you identify the columns correctly?")

        # Check that Accessibility is just Yes and No
        for value in self.students_df[self.ACCESSIBILITY.col].unique():
            if value not in ("Yes", "No"):
                raise ValueError(f"Column that represents '{self.ACCESSIBILITY.desc}' should only contain 'Yes' and "
                                 f"'No'. Currently it contains '{value}' as well.")

        # Check that Available RCs is just Saga, Elm, Cendana (separated by ", ")
        for rc_list in self.students_df[self.AVAILABLE_RCS.col].unique():
            for value in rc_list.split(", "):
                if value not in self.RC_LIST:
                    raise ValueError(f"Column that represents '{self.AVAILABLE_RCS.desc}' should only contain the "
                                     f"following possible values: {', '.join(self.RC_LIST)}. If a student can be "
                                     f"allocated to more than one RC, the RCs should be separated by a comma "
                                     f"(e.g. 'Saga, Cendana'). "
                                     f"Currently you have the following illegal value: '{rc_list}'.")

        self.col_types_defined = True

    def set_living_pref_order(self, selected_order: List[List[str]]):
        if self.living_pref_order_defined:
            pass
        if not self.col_types_defined:
            raise ValueError("self.set_column_types(col_type_assoc) MUST be called first")

        self.LIVING_PREF.selected_order = selected_order
        self.LIVING_PREF.text_to_num = [{value: i for i, value in enumerate(col)} for col in selected_order]
        self.LIVING_PREF.num_to_text = [{i: value for i, value in enumerate(col)} for col in selected_order]
        self.set_max_scores()

        # for col, text_to_num in zip(self.LIVING_PREF.cols, self.LIVING_PREF.text_to_num):
        #     self.students_df[col] = self.students_df[col].map(text_to_num)

        self.living_pref_order_defined = True

    def set_weights(self, weights):
        if not self.living_pref_order_defined:
            raise ValueError("self.living_pref_order(selected_order) MUST be called first")

        total = sum(weights.values())
        if total != 100:
            raise ValueError(f"Sum of weights should be exactly 100%. Currently it is {total}%.")

        self.LIVING_PREF.weights = weights
        scoring.Scores.set_weights({col: weight / 100 for col, weight in weights.items()})

        self.weights_defined = True

    def set_options(self, saga, elm, cendana):
        if not self.weights_defined:
            raise ValueError("self.set_weights(weights) MUST be called first")

        self.avail_suites_saga = saga
        self.avail_suites_elm = elm
        self.avail_suites_cendana = cendana

        self.total_suites = self.avail_suites_saga + self.avail_suites_elm + self.avail_suites_cendana
        self.required_suites_male = math.ceil(self.num_males / 6)
        self.required_suites_female = math.ceil(self.num_females / 6)
        self.required_suites = self.required_suites_male + self.required_suites_female
        if self.total_suites < self.required_suites:
            raise ValueError(f"Not enough suites. {self.required_suites} suites are required to house "
                             f"{self.num_females} females and {self.num_males} males but only {self.total_suites} are "
                             f"available. Did you enter the correct number of available suites? "
                             f"Have you removed the gender neutral students from the CSV file?")

        self.options_defined = True

    def run_allocation(self):
        female_students, male_students = self.add_students()
        self.female_suites = self.allocate_suites(female_students, "Female")
        self.male_suites = self.allocate_suites(male_students, "Male")
        rca_match = match.RCAMatch(self.female_suites, self.male_suites,
                                   saga=self.avail_suites_saga,
                                   elm=self.avail_suites_elm,
                                   cendana=self.avail_suites_cendana)
        rca_match.run_match()
        self.suites = self.male_suites + self.female_suites
        self.calculate_statistics()
        self.allocation_completed = True

    def set_max_scores(self):
        unique_options = {col: list(val_dict)
                          for col, val_dict in zip(self.LIVING_PREF.cols, self.LIVING_PREF.num_to_text)}
        scoring.Scores.set_max_scores(unique_options)

    def add_students(self):
        """Creates StudentData objects based on student data from a Pandas DataFrame.

        Args:
            students_df: A Pandas DataFrame containing student data.

        Returns:
            Two lists containing StudentData objects, one list for female students and one list for male students.
        """
        female_students = []
        male_students = []
        for i in range(len(self.students_df)):
            # Gathers data for one student in a dictionary that maps variable names to the values
            new_student = StudentData(index=i,
                                      matric=self.students_df.loc[i, self.ID.col],
                                      sex=self.students_df.loc[i, self.SEX.col],
                                      school=self.students_df.loc[i, self.SCHOOL.col],
                                      country=[self.students_df.loc[i, col] for col in self.COUNTRY.cols if col],
                                      living_prefs={col: self.LIVING_PREF.text_to_num[j][self.students_df.loc[i, col]]
                                                    for j, col in enumerate(self.LIVING_PREF.cols)},
                                      others={col: self.students_df.loc[i, col] for col in self.OTHERS.cols})
            sex = self.students_df.loc[i, self.SEX.col]
            if sex == "F":
                female_students.append(new_student)
            elif sex == "M":
                male_students.append(new_student)
            else:
                raise ValueError(f"Unrecognised sex: {sex}")
        return female_students, male_students

    def calculate_statistics(self):
        self.female_stats = {rc: (0, 0) for rc in self.RC_LIST_WITH_UNALLOCATED}
        self.male_stats = {rc: (0, 0) for rc in self.RC_LIST_WITH_UNALLOCATED}
        for suite in self.female_suites:
            num_students, num_suites = self.female_stats[suite.rc]
            self.female_stats[suite.rc] = (len(suite.students) + num_students, 1 + num_suites)
        for suite in self.male_suites:
            num_students, num_suites = self.male_stats[suite.rc]
            self.male_stats[suite.rc] = (len(suite.students) + num_students, 1 + num_suites)
        self.datetime = datetime.datetime.now().strftime("%d %b %Y %H:%M")

    def allocate_suites(self, students, name):
        allocations = {}
        for i in range(100):
            suite_allocation = SuiteAllocation(students, name)
            suite_allocation.match()
            global_score = suite_allocation.global_score()
            allocated_suites = suite_allocation.get_allocation()
            print(f"Global score: {global_score}")
            allocations[global_score] = allocated_suites
        final_score = max(allocations)
        allocated_suites = allocations[final_score]
        print(f"\nFinal score: {final_score}\n")
        return allocated_suites

    def export_files(self, folder_path):
        if not self.allocation_completed:
            raise ValueError("self.run_allocation() MUST be called first")

        def filepath(filename):
            return os.path.join(folder_path, filename)

        self.generate_suite_results(self.female_suites, filepath("female_suites.csv"))
        self.generate_suite_results(self.male_suites, filepath("male_suites.csv"))
        self.generate_suite_results(self.suites, filepath("rca_groups.csv"))
        self.generate_masterlist(self.suites, filepath("masterlist.csv"))

    def generate_suite_results(self, suites, csv_path):
        """
        Temporary function to generate results for an allocation

        Args:
            suites:
            csv_path:
        """
        suite_living_prefs = {
            k: v
            for i, living_pref in enumerate(self.LIVING_PREF.cols)
            for k, v in {
                f"Living Pref: {living_pref}": [[self.LIVING_PREF.num_to_text[i][student.data.living_prefs[living_pref]]
                                                 for student in suite.students]
                                                for suite in suites],
                living_pref: [[student.data.living_prefs[living_pref]
                               for student in suite.students]
                              for suite in suites],
                f"Score: {living_pref}": [scoring.living_pref_score(suite.students, living_pref, higher_better=True)
                                          for suite in suites]
            }.items()
        }
        suite_data = {
            "Suite": [repr(suite) for suite in suites],
            "RC": [suite.rc for suite in suites],
            "RCA": [suite.rca for suite in suites],
            "Num_students": [len(suite.students) for suite in suites],
            "Countries": [[student.data.country for student in suite.students] for suite in suites],
            "Citizenship Diversity": [scoring.citizenship_diversity_score(suite.students) for suite in suites],
            "Country Diversity": [scoring.country_diversity_score(suite.students) for suite in suites],
            "Schools": [[student.data.school for student in suite.students] for suite in suites],
            "School Diversity": [scoring.school_diversity_score(suite.students) for suite in suites],
            **suite_living_prefs,
            "Demographic Score": [scoring.demographic_scores(suite.students) for suite in suites],
            "Living Pref Score": [scoring.living_pref_scores(suite.students, higher_better=True) for suite in suites],
            "Final Score": [scoring.calculate_success(suite.students) for suite in suites]
        }
        suites_df = pd.DataFrame(suite_data, columns=list(suite_data.keys()))
        suites_df.sort_values(by=['RCA', 'Suite'], inplace=True, kind="mergesort")
        suites_df.to_csv(csv_path, index=False)

    def generate_masterlist(self, suites, csv_path):
        # The algorithm always allocates locals first followed by internationals so they are ordered in that way
        # [local, local, local, intl, intl, intl]
        # random.sample ensures that the local and international students are mixed together
        students = [student for suite in suites for student in random.sample(suite.students, len(suite.students))]
        df = self.students_df.reindex(student.data.index for student in students)
        CURRENT_YEAR = datetime.datetime.now().year
        num_students = len(students)
        df = df.assign(Suite=[student.current_choice.data.suite_num for student in students],
                       Room=["TBC" for _ in range(num_students)],
                       RC=[student.current_choice.data.rc for student in students],
                       RCA=[student.current_choice.data.rca for student in students],
                       Admit=[CURRENT_YEAR for _ in range(num_students)],
                       Class=[CURRENT_YEAR + 4 for _ in range(num_students)],
                       Student_Type=["First-Year" for _ in range(num_students)],
                       Unofficial_Residency=[student.data.citizenship.value for student in students], )
        df.sort_values(by=['RCA', 'Suite'], inplace=True, kind="mergesort")
        df.to_csv(csv_path, index=False)


def main():
    if len(sys.argv) != 2:
        print("Wrong format! Please type 'python -m ASAP [csv_file]'")
        return
    csv_path = sys.argv[1]
    female_students, male_students = parser.parse_student_data(csv_path)
    female_suites = allocate_suites(female_students, "Female")
    allocate_randomly(female_students, "Female")
    male_suites = allocate_suites(male_students, "Male")
    allocate_randomly(male_students, "Male")

    rca_match = match.RCAMatch(female_suites, male_suites, saga=16, elm=16, cendana=16)
    rca_match.run_match()

    parser.generate_masterlist(female_suites + male_suites, f"output/first_year_masterlist_by_algorithm.csv")


def allocate_suites(students, name):
    allocations = {}
    for i in range(20):
        suite_allocation = SuiteAllocation(students, name)
        suite_allocation.match()
        global_score = suite_allocation.global_score()
        allocated_suites = suite_allocation.get_allocation()
        print(f"Global score: {global_score}")
        allocations[global_score] = allocated_suites
    final_score = max(allocations)
    allocated_suites = allocations[final_score]
    print(f"\nFinal score: {final_score}\n")
    parser.generate_temp_results(allocated_suites, f"output/{name}_suites.csv")
    return allocated_suites


def allocate_randomly(students, name):
    suite_allocation = SuiteAllocation(students, name)
    suite_allocation.allocate_randomly()
    global_score = suite_allocation.global_score()
    allocated_suites = suite_allocation.get_allocation()
    print(f"\nRandom allocation score: {global_score}\n")
    parser.generate_temp_results(allocated_suites, f"output/{name}_random.csv")


if __name__ == "__main__":
    main()
