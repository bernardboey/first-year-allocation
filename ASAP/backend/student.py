"""This module provides the StudentData class.

    Typical usage example:

    new_student = StudentData(...)
"""

import enum


class Citizenship(enum.Enum):
    INTERNATIONAL = "International"
    LOCAL = "Local"


class Sex(enum.Enum):
    FEMALE = "F"
    MALE = "M"


class StudentData:
    """Contains information about a student's demographic and preferences

    Attributes:
        matric: A string representing the student's Matric/ID
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

    def __init__(self, *, matric, sex, country, school, gender_pref,
                 sleep_pref, suite_pref, cleanliness_pref, alcohol_pref):
        """Initialises a StudentData object"""
        self.matric = matric
        self.sex = Sex(sex)
        self.country = country
        self.school = school
        self.gender_pref = gender_pref
        self.sleep_pref = sleep_pref
        self.suite_pref = suite_pref
        self.cleanliness_pref = cleanliness_pref
        self.alcohol_pref = alcohol_pref
        if self.country == "Singapore":
            self.citizenship = Citizenship.LOCAL
        else:
            self.citizenship = Citizenship.INTERNATIONAL

    def __repr__(self):
        return self.matric

    def __str__(self):
        return self.matric

    def full_information(self):
        """Returns a string containing detailed information about a student.

        Use this to print information about a student, when the string representation of the object is not sufficient.
        """
        attributes = str([self.sex, self.country, self.citizenship, self.school, self.gender_pref,
                          self.sleep_pref, self.suite_pref, self.cleanliness_pref, self.alcohol_pref])
        return f"{self.matric}: {attributes}"
