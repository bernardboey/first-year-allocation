"""A script used to clean the housing survey results data.

This script cleans the housing preference survery results prior to putting it
through the matching algorithm. Main goal is to compress the column names and to
map the raw preference answers (str) onto a scale (int).

The script takes 1 argument, which is the name of the data file to be cleaned.
The data file should be located in the data/ directory.

Typical usage example (in command line):

python data_cleaning.py raw_data
"""

import os
import sys
import csv
import pandas as pd

# Get path of raw data, defaulting to raw_uncleaned.csv if left blank.
if len(sys.argv) == 1:  # no arg provided, defaulting
    raw_path = "raw_uncleaned.csv"
else:
    if len(sys.argv) >= 3:  # too many args, warn + take first argument
        print("Too many arguments. Taking the first arguement as path.")
    raw_path = sys.argv[1]
print("Extracting raw data from {}.".format(raw_path))

# Import data
try:
    raw_data = pd.read_csv(os.getcwd() + '/data/' + raw_path)
    raw_data.columns = ["ID", "sex", "school", "country", "sleep",
                        "suite_pref", "cleanliness", "alcohol",
                        "siblings", "gender_pref"]
except Exception as inst:
    print("ERROR: {} does not exist in data/. Please try again.".format(raw_path))
    exit(1)

# Dictionaries for mapping answers to numbers
# NOTE: These need to be changed if the questions or answers change

sleep_dict ={"Before 10 PM" : 1,
             "10PM to 12AM" : 2,
             "12AM to 2AM" : 3,
             "After 2AM" : 4}

suite_dict = {"A quiet zone used primarily for studying, resting, and sleeping." : 1,
              "A calm environment where human traffic is limited during peak study hours, but more social and busy on weekends." : 2,
              "A spontaneous social space; neither a study hall nor a regular site of activity." : 3,
              "A vibrant, busy social hub where friends frequently visit; studying takes place outside the suite." : 4}

cleanliness_dict = {"Cleanliness is a top priority, and every member of the suite plays their part in sharing that responsibility." : 1,
               "A small amount of mess is tolerable, but everyone should make the effort to clean up after themselves." : 2,
               "I don't prioritize cleanliness, unless it is getting out of hand." : 3,
               "As long as there exists a path from the door to our rooms, and there is space to sit in the common area, we're good." : 4}

sibs_dict = {"Yes" : "Yes",
              "No (Proceed to Question 6)" : "No"}

yes_no_dict = {"Yes" : 1, "No" : 0}

# Clean data
raw_data["sex"] = [s[0] for s in raw_data["sex"]]
raw_data["sleep"] = raw_data["sleep"].map(sleep_dict)
raw_data["suite_pref"] = raw_data["suite_pref"].map(suite_dict)
raw_data["cleanliness"] = raw_data["cleanliness"].map(cleanliness_dict)
raw_data["siblings"] = raw_data["siblings"].map(sibs_dict)
raw_data["alcohol"] = raw_data["alcohol"].map(yes_no_dict)

# Export data
PATH_TO_CLEANED = os.getcwd() + "/cleaned"
try:  # Safety check to ensure that data folder exists, and makes it otherwise.
    os.mkdir(PATH_TO_CLEANED)
except FileExistsError:
    pass
raw_data.to_csv(PATH_TO_CLEANED + "/" + raw_path, index=False)
