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
import os
import collections
import time
from typing import Dict, List, Tuple

import pandas as pd

from ASAP.backend import match
from ASAP.backend import parser
from ASAP.backend.allocation import SuiteAllocation


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
        self.selected_order: List[List[str]] = []
        super().__init__(*args, **kwargs)


# class DataType(enum.Enum):
#     NAME = "Name/ID"
#     SCHOOL = "School"
#     SEX = "Sex"
#     COUNTRY = "Country"
#     LIVING_PREF = "Living Preference"
#     OTHERS = "Others"


# MANDATORY_TYPES = [DataType.NAME, DataType.SCHOOL, DataType.SEX, DataType.COUNTRY, DataType.LIVING_PREF]
# EXCLUSIVE_TYPES = [DataType.NAME, DataType.SCHOOL, DataType.SEX]

class ASAP:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.students_df = pd.read_csv(filepath)
        self.colnames = list(self.students_df.columns)
        self.col_to_type: Dict[str, ColumnType] = {}
        # self.type_to_cols: Dict[DataType, List[str]] = {}
        # self.living_pref_cols = []

        self.NAME = ExclusiveColumnType("Name/ID", mandatory=True)
        self.SCHOOL = ExclusiveColumnType("School", mandatory=True)
        self.SEX = ExclusiveColumnType("Sex", mandatory=True)
        self.COUNTRY = NonExclusiveColumnType("Country", mandatory=True)
        self.LIVING_PREF = LivingPrefColumnType("Living Preference", mandatory=True)
        self.OTHERS = NonExclusiveColumnType("Others", mandatory=False)
        self.COL_TYPES = [self.NAME, self.SCHOOL, self.SEX, self.COUNTRY, self.LIVING_PREF, self.OTHERS]

        self.avail_suites_saga = 0
        self.avail_suites_elm = 0
        self.avail_suites_cendana = 0

        self.col_types_defined = False
        self.living_pref_order_defined = False
        self.options_defined = False

    def __str__(self):
        return f"<ASAP object>"

    def __repr__(self):
        return f"ASAP({self.filename})"

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
                raise ValueError(f"You did not select any columns for '{_type.desc}'. Please try again.")
        # self.col_to_type = {col: DataType(_type) for col, _type in col_to_type.items()}
        # self.type_to_cols = {_type: [col for col, __type in self.col_to_type.items() if _type == __type]
        #                      for _type in DataType}
        # self.living_pref_cols = [col for col, _type in self.col_to_type.items() if _type is DataType.LIVING_PREF]

        # Check that all mandatory types have corresponding columns
        # types_without_cols = [_type.value for _type in MANDATORY_TYPES if not self.type_to_cols[_type]]
        # if types_without_cols:
        #     raise ValueError(f"""The following data types do not have corresponding columns: """
        #                      f""""{'", "'.join(types_without_cols)}". """
        #                      f"""Please select the correct types again.""")

        # Check that only one column for each type (except country and living preference)
        # exclusive_types_with_multiple_cols = [_type.value for _type in EXCLUSIVE_TYPES if len(self.type_to_cols[_type]) > 1]
        # if exclusive_types_with_multiple_cols:
        #     raise ValueError(f"""The following data types have more than one columns: """
        #                      f""""{'", "'.join(exclusive_types_with_multiple_cols)}". """
        #                      f"""Please make sure these types are only selected once.""")

        # Check that Sex is just M and F
        self.students_df[self.SEX.col] = self.students_df[self.SEX.col].str.upper()
        for value in self.students_df[self.SEX.col].unique():
            if value not in ("M", "F", "MALE", "FEMALE"):
                raise ValueError(f"Column that represents sex should only contain 'M' and 'F'. "
                                 f"Currently it contains '{value}' as well.")

        if "Singapore" not in self.students_df[self.COUNTRY.cols[0]].unique():
            raise ValueError(f"The value 'Singapore' cannot be found in the column you selected for "
                             f"'Country' (column '{self.COUNTRY.cols[0]}'). Did you identify the columns correctly?")

        if not self.students_df[self.NAME.col].is_unique:
            raise ValueError(f"The column that you selected for 'Name' (column '{self.NAME.col}') contains duplicate "
                             f"values. Did you identify the columns correctly?")
        self.col_types_defined = True

    def set_living_pref_order(self, selected_order: List[List[str]]):
        # selected_order = [["10pm to 12am", "12am to 2am", "after 2am"], [], [], []]
        if self.living_pref_order_defined:
            pass
        if not self.col_types_defined:
            raise ValueError("self.set_column_types(col_type_assoc) MUST be called first")

        self.LIVING_PREF.selected_order = selected_order
        self.LIVING_PREF.text_to_num = [{value: i for i, value in enumerate(col)} for col in selected_order]
        self.LIVING_PREF.num_to_text = [{i: value for i, value in enumerate(col)} for col in selected_order]

        self.living_pref_order_defined = True

    def set_options(self, saga, elm, cendana):
        if not self.living_pref_order_defined:
            raise ValueError("self.living_pref_order(selected_order) MUST be called first")

        self.avail_suites_saga = saga
        self.avail_suites_elm = elm
        self.avail_suites_cendana = cendana

        self.options_defined = True

    def run_allocation(self):
        time.sleep(5)


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
