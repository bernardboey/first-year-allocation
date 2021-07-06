"""This module provides the StudentData class.

    Typical usage example:

    new_student = StudentData(...)
"""

import enum
from typing import Dict, List, Any


class Citizenship(enum.Enum):
    INTERNATIONAL = "International"
    LOCAL = "Local"


class Sex(enum.Enum):
    FEMALE = "F"
    MALE = "M"


class StudentData:
    """Contains information about a student's demographic and preferences

    Attributes:
        name: A string representing the student's Matric/ID
        sex: A Sex enumeration representing the student's sex (either M or F)
        country: A string representing the student's country
        school: A string representing the student's school
        gender_pref: A string representing the student's gender preference
        sleep_pref: An integer representing the student's sleep preference
        suite_pref: An integer representing the student's suite preference
        cleanliness_pref: An integer representing the student's cleanliness preference
        alcohol_pref: An integer representing the student's alcohol preference
        citizenship: An Citizenship enumeration representing whether a student is LOCAL or INTERNATIONAL
    """

    def __init__(self, *, index, matric, sex, country, school, living_prefs, others, available_rcs,
                 accessibility=False):
        """Initialises a StudentData object"""
        self.index = index
        self.matric = matric
        self.sex = Sex(sex)
        self.school = school
        self.country: List[str] = country
        self.available_rcs: List[str] = available_rcs
        self.accessibility: bool = accessibility
        self.living_prefs: Dict[str, int] = living_prefs
        self.others: Dict[str, Any] = others
        self.citizenship = Citizenship.LOCAL if "Singapore" in self.country else Citizenship.INTERNATIONAL

    def __repr__(self):
        return self.matric

    def __str__(self):
        return self.matric

    def full_information(self):
        """Returns a string containing detailed information about a student.

        Use this to print information about a student, when the string representation of the object is not sufficient.
        """
        attributes = str([self.sex, self.country, self.citizenship, self.school,
                          "Accessibility" if self.accessibility else "Non-accessibility",
                          self.available_rcs, self.living_prefs, self.others])
        return f"{self.matric}: {attributes}"
