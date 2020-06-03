import os
import random

DATA_DIR_PATH = os.getcwd() + "/data"

# CONSTANTS
NUM_STUDENTS = 100 # Total students being allocated
INTL_RATIO = 0.4   # Ratio of International Student (Local student ratio = 1 - INTL_RATIO)

LOCAL_SCHOOLS = ['AJC', 'BJC', 'CJC', 'DJC', 'EJC', 'FJC', 'GJC', 'HJC']
LOCAL_SCHOOLS_WEIGHTS = [5,5,4,2,2,1,1]
INTL_COUNTRIES = ['ZLand', 'YLand', 'XLand', 'WLand', 'VLand', 'Uland', 'Tland', 'Sland', 'Rland', 'Qland']
INTL_COUNTRIES_WEIGHTS = [10,10,8,5,5,4,3,1,1,1]


# Utility Functions
def genMatrics(n):
    """
    Generates a list of n matric numbers
    """
    letters = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'U', 'V', 'W', 'X', 'Y', 'Z']
    return ['A{0:07d}{1}'.format(random.randint(1,999999), random.sample(letters,1)[0]) for _ in range(n)]

