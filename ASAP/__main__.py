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

TODO: Can we try to automate the part where we define the preferences or at least make it dynamic?
    Because the questions may differ year by year.
TODO: Check correctness of code (.copy()?)
"""

import sys
import enum
import os
import collections
from typing import Dict, List

import pandas as pd

from ASAP.backend import match
from ASAP.backend import parser
from ASAP.backend.allocation import SuiteAllocation


class ColumnTypes(enum.Enum):
    NAME = "Name/ID"
    SCHOOL = "School"
    SEX = "Sex"
    COUNTRY = "Country"
    LIVING_PREF = "Living Preference"
    OTHERS = "Others"


MANDATORY_TYPES = [ColumnTypes.NAME, ColumnTypes.SCHOOL, ColumnTypes.SEX, ColumnTypes.COUNTRY, ColumnTypes.LIVING_PREF]
UNIQUE_TYPES = [ColumnTypes.NAME, ColumnTypes.SCHOOL, ColumnTypes.SEX]


class ASAP:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.students_df = pd.read_csv(filepath)
        self.colnames = list(self.students_df.columns)
        self.col_to_type: Dict[str, ColumnTypes] = {}
        self.type_to_cols: Dict[ColumnTypes, List[str]] = {}
        self.living_pref_cols = []
        # check_unique_column_names

    def __str__(self):
        return f"<ASAP object>"

    def __repr__(self):
        return f"ASAP({self.filename})"

    def get_colnames_and_unique_values(self):
        unique_values: List[List[str]] = [self.students_df[col].value_counts().index.tolist() for col in self.colnames]
        head_values = [self.students_df.loc[i, :].values.tolist() for i in range(5)]
        return self.colnames, unique_values, head_values

    def set_column_types(self, col_to_type):
        # Shouldn't have duplicate colnames because pandas automatically renames, but just check to be sure.
        duplicate_colnames = [k for k, freq in collections.Counter(self.colnames).items() if freq > 1]
        if duplicate_colnames:
            raise ValueError(f"""There are duplicate column names: "{'", "'.join(duplicate_colnames)}". """
                             f"""Please close the program and change the column names before trying again.""")

        self.col_to_type = {col: ColumnTypes(_type) for col, _type in col_to_type.items()}
        self.type_to_cols = {_type: [col for col, __type in self.col_to_type.items() if _type == __type]
                             for _type in ColumnTypes}
        self.living_pref_cols = [col for col, _type in self.col_to_type.items() if _type is ColumnTypes.LIVING_PREF]

        # Check that all mandatory types have corresponding columns
        types_without_cols = [_type.value for _type in MANDATORY_TYPES if not self.type_to_cols[_type]]
        if types_without_cols:
            raise ValueError(f"""The following types do not have corresponding columns: """ 
                             f""""{'", "'.join(types_without_cols)}". """
                             f"""Please select the correct types again.""")

        # Check that only one column for each type (except country and living preference)
        unique_types_with_multiple_cols = [_type.value for _type in UNIQUE_TYPES if len(self.type_to_cols[_type]) > 1]
        if unique_types_with_multiple_cols:
            raise ValueError(f"""The following types have more than one columns: """ 
                             f""""{'", "'.join(unique_types_with_multiple_cols)}". """
                             f"""Please make sure these types are only selected once.""")

    def set_living_pref_order(self, selected_order):
        # Raise ValueError in case of failed validation
        pass

    def column_types_defined(self):
        return self.col_to_type and self.type_to_cols


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
