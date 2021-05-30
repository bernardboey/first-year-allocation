# first-year-allocation

To run, navigate to the main directory (NOT in the `ASAP` directory) and type the following:
```
python -m ASAP [csv_file_path]
```

## Data Cleaning

If data is not yet clean for use, the script `data_cleaning.py` can be used to
automate the cleaning process. To use the script, it must first be modified to
reflect the correct mappings of answers to integers. This is done through the
various dictionaries in the script.

### Adding a new question option

If a new question is added (as a running example, we assume that `preference` is
the name we assign to this new column`), follow these steps:

1. Edit the line that begins with `raw_data.columns = ...` to include the new column
   name in the correct order.
1. Add a new dictionary (which in this example will be labelled
   `preference_dict` that has an answer string as a key which points to the
   corresponding integer value of the answer. For now, `data_cleaning.py`
   supports both scalar values and binary values.
1. Under the `# Clean data` section, add another line that reads 
   ```
   raw_data["preference"] = raw_data["preference"].map(preference_dict)
   ``` 
   This will use the dictionary generated in step 2 to change all the answer
   strings to their corresponding integer value. The code example above is still
   using our `preference` running example, make sure to change the names
   accordingly.

### Cleaning data

To clean data, make sure the raw file is stored in the `data/` directory. Then,
run the following in command line:
```
python data_cleaning.py [data_file_name]
```

If there is an error, or if the script is not cleaned properly, please check
through `data_cleaning.py` again, and make sure the dictionaries are done up
properly.
