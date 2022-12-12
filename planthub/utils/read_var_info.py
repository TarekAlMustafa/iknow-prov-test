"""
The updated variable information is located in the data/viz/variable_table directory.
For now, the dataset names to be used are a global hardcoded constant, like in `read_data.py`.
"""

from collections import defaultdict
from pathlib import Path

import pandas as pd
import os

DATASETS = ["TRY", "TRY_Species", "PhenObs", "PhenObs_Species"]
PATH = os.path.join(Path(__file__).resolve(strict=True).parent.parent, "data", "viz")
NEW_PATH = os.path.join(Path(__file__).resolve(strict=True).parent.parent, "data", "viz", "variable_table", "varinfo.pickle")

# Original table of data
data_frames: dict[str, pd.DataFrame] = {}
for dataset in DATASETS:
    try:
        data_frames[dataset] = pd.read_pickle(os.path.join(PATH, dataset + '.pickle'))
    except FileNotFoundError:
        print(dataset, "not found.")

# Updated table of metadata
df = pd.read_pickle(NEW_PATH)

def create_var_info() -> dict[str, list[pd.Series]]:
    """
    Read and process the variable information from a .pickle file.

    All variable information is processed from a dataframe into a dictionary `var_infos`,
    which maps the name of each dataset to a list of all rows belonging to the dataset.
    The rows are Series objects from the pandas library and have the columns as attributes,
    which can be accessed by indexing or by the dot operator.

    For instance, we can access the tenth element from the TRY dataset (which is TRY_Leaf area) like this:
    >>> try_leaf_area = var_infos["TRY"][9]
    dataset                                         TRY
    variable                              TRY_Leaf area
    variableUnit                                   cm^2
    variableProvenance                              NaN
    preprocessingCode                               NaN
    variableLong_eng                          Leaf area
    variableLong_de                         Blattfläche
    variableShort_eng                         Leaf area
    variableShort_de                        Blattfläche
    variableText_eng                The area of a leaf.
    variableText_de                                 NaN
    variableType_eng             plant functional trait
    variableType_de       funktionelles Pflanzenmerkmal
    Name: 9, dtype: object
    >>> type(try_leaf_area)
    <class 'pandas.core.series.Series'>
    >>> try_leaf_area.variable
    TRY_Leaf area (in case of compond leaves: leaflet, petiole and rachis excluded)
    >>> try_leaf_area.variableLong_eng
    Leaf area

    :return: dictionary mapping names of datasets to list of rows from dataset
    """

    var_infos = {}
    for ds in DATASETS:
        var_infos[ds] = [row[1] for row in df.iterrows() if row[1].dataset == ds]

    return var_infos

def create_all_cols(var_infos: dict[str, list[pd.Series]]) -> dict[str, list[pd.Series]]:
    """
    Parses table of data and updated table of metadata and checks whether variable IDs are missing.

    In the case of a missing ID in either direction an `IndexError` is raised.

    :param var_infos: new variable information (metadata)
    :return: dict of variables contained in both tables
    """
    
    # TODO: Make the "variable not found" checks raise exceptions instead of printing

    columns = defaultdict(list)

    for ds in DATASETS:
        # Compare original tables to new metadata table
        for variable_id in data_frames[ds].columns.values:
            # If it's not in the list of values, raise an exception
            if not any(item == variable_id for item in df["variable"].values):
                print(variable_id, "of dataset", ds, "was not found")
                # raise IndexError(variable_id, "of dataset", ds, "was not found")
            
            # Otherwise, get the corresponding column from the data table
            for i in range(0, len(df["variable"].values)):
                if df.loc[i].dataset != ds:
                    continue
                if variable_id == df["variable"][i]:
                    columns[ds].append(df.loc[i])
                    break

    # Compare new metadata table to original tables
    for ds in DATASETS:
        for var_info in var_infos[ds]:
            # List of columns from the current dataframe
            curr_columns = data_frames[ds].columns.values
            
            # If the variable is missing from the current columns, raise an exception
            if not any(item == var_info.variable for item in curr_columns):
                print(var_info.variable, "of dataset", ds, "was not found")
                # raise IndexError(var_info.variable, "of dataset", ds, "was not found")
            
            # Otherwise, get the corresponding item from 
            for i in range(0, len(curr_columns)):
                # Check whether the variable is already in the current list
                if not any(series.variable == var_info.variable for series in columns[ds]):
                    columns[ds].append(var_info)
                    break

    return columns

def create_cat_cont(columns: dict[str, list[pd.Series]]) -> tuple[dict[str, list[pd.Series]], dict[str, list[pd.Series]]]:
    """
    Creates dict of category columns and continuous columns (previously done in `read_data.py`)

    These are returned as a tuple and are meant to be unpacked directly when making the function call.

    :param columns: dictionary of columns from which to filter cats and conts
    :return: tuple of category columns and continuous columns
    """

    cat_cols, cont_cols = defaultdict(list), defaultdict(list)

    # Category columns consist of all columns which contain data of the type `object` or `category`
    for ds in DATASETS:
        cat_cols[ds] = [
            col for col in columns[ds]
            if data_frames[ds][col.variable].dtype.name in ["object", "category"]
        ]


    # The continuous columns consist of all columns which are not in `cat_cols` and in addition,
    # must not contain the variable `ObservationID`
    for ds in DATASETS:
        for col in columns[ds]:
            if col.variable != "ObservationID":
                if not any(col.variable == series.variable for series in cat_cols[ds]):
                    if not any(col.variable == series.variable for series in cont_cols[ds]):
                        cont_cols[ds].append(col)

    return cat_cols, cont_cols


def main() -> None:
    """
    Example usage of `read_var_info.py`
    
    For actual usage, see `cols.py`
    """
    
    var_infos = create_var_info()

    try:
        columns = create_all_cols(var_infos)
        cat_cols, cont_cols = create_cat_cont(columns)
    except IndexError as ie:
        print(ie)


if __name__ == "__main__":
    main()
