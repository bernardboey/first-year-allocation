import csv
import pandas as pd

raw_data = pd.read_csv("raw_uncleaned.csv")
raw_data.columns = ["ID", "sex", "country", "sleep", "suite_pref", "cleanliness", "alcohol", "siblings", "sibs_sameRC", "gender_pref"]

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

sibs_clean = {"Yes" : "Yes",
              "No (Proceed to Question 6)" : "No"}

raw_data["sleep"] = raw_data["sleep"].map(sleep_dict)
raw_data["suite_pref"] = raw_data["suite_pref"].map(suite_dict)
raw_data["cleanliness"] = raw_data["cleanliness"].map(cleanliness_dict)
raw_data["siblings"] = raw_data["siblings"].map(sibs_clean)
print(raw_data.tail())

