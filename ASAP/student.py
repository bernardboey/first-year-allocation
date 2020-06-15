import enum


class Citizenship(enum.Enum):
    INTERNATIONAL = "International"
    LOCAL = "Local"


class StudentData:
    """Contains information about a student's demographic and preferences

    Attributes:
        matric
        sex
        country
        school
        gender_pref
        sleep_pref: An integer
        suite_pref: An integer
        cleanliness_pref: An integer
        alcohol_pref: An integer
        citizenship: An enumeration of Citizenship (either LOCAL or INTERNATIONAL)
        suite: A suite object
        scores: A dictionary mapping suite objects to the score given to that suite combined with the student
        ranking: A list that contains suite objects. The order represents the student's preference
    """

    def __init__(self, matric, sex, country, school, gender_pref,
                 sleep_pref, suite_pref, cleanliness_pref, alcohol_pref):
        """Initialises a student object.

        Args:
            matric
            sex
            country
            school
            gender_pref
            sleep_pref: An integer
            suite_pref: An integer
            cleanliness_pref: An integer
            alcohol_pref: An integer
        """
        self.matric = matric
        self.sex = sex
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
        self.suite = None
        self.scores = {}
        self.ranking = []

    def __repr__(self):
        return self.matric

    def __str__(self):
        return self.matric

    def full_information(self):
        """Returns a string containing detailed information about a student.

        Use this to print information about a student, when the string representation of the object is not sufficient.
        """
        attributes = str([self.suite, self.sex, self.country, self.school, self.gender_pref,
                          self.sleep_pref, self.suite_pref, self.cleanliness_pref, self.alcohol_pref])
        return f"{self.matric}: {attributes}"
