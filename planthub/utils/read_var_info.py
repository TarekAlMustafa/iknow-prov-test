#!usr/bin/env python3

"""
The updated variable metadata will be located in the data/viz/variable_table directory.
For now, the dataset names to be used are a global hardcoded constant, like in `read_data.py`.
"""

__author__ = "Yannick Brenning"
__email__ = "yb63tadu@studserv.uni-leipzig.de"

import os
import pickle
import traceback
from collections import defaultdict
from pathlib import Path

import pandas as pd

DATASETS = ["TRY", "TRY_Species", "PhenObs", "PhenObs_Species"]

DATA_PATH = os.path.join(Path(__file__).resolve(strict=True).parent.parent, "data", "viz")

SAVE_PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent.parent,
    "data", "viz", "variable_table"
)

METADATA_PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent.parent,
    "data", "viz", "variable_table", "varinfo.pickle"
)


class VariableNotFoundError(Exception):
    """
    Raise this exception when a variable name mismatch occurs
    during the comparison of the metadata and data tables.
    """
    def __init__(self, variable: str, dataset: str) -> None:
        super().__init__(f"Variable <{variable}> of dataset <{dataset}> was not found.")


def read_data_tables() -> dict[str, pd.DataFrame]:
    """
    Read the data from each dataset from .pickle files.

    :return: dictionary mapping dataset names to corresponding dataframe
    """
    data_frames: dict[str, pd.DataFrame] = {}
    for dataset in DATASETS:
        try:
            data_frames[dataset] = pd.read_pickle(os.path.join(DATA_PATH, dataset + '.pickle'))
        except FileNotFoundError:
            print(dataset, "not found.")

    return data_frames


def read_metadata_table() -> dict[str, list[pd.Series]]:
    """
    Read and process the variable information (metadata) from a .pickle file.

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
    df = pd.read_pickle(METADATA_PATH)

    var_infos = {}
    for ds in DATASETS:
        var_infos[ds] = [row[1] for row in df.iterrows() if row[1].dataset == ds]

    return var_infos


def compare_tables(
    data: dict[str, pd.DataFrame],
    metadata: dict[str, list[pd.Series]]
) -> dict[str, list[pd.Series]]:
    """
    Parses table of data and updated table of metadata and checks whether variable IDs are missing.

    Missing IDs in either direction are printed onto the console.
    Note: this should be done using exceptions in the future.

    :param data: dictionary of datasets mapped to their corresponding dataframes
    :param metadata: dictionary of datasets mapped to lists of metadata table rows
    :return: dict of variables contained in both tables
    """
    columns = defaultdict(list)

    # Compare data tables to metadata table
    for ds in DATASETS:
        for variable_id in data[ds].columns.values:
            try:
                # If it's not in the list of values, raise an exception
                if not any(variable == variable_id for variable in
                           [series.variable for series in metadata[ds]]):
                    raise VariableNotFoundError(variable_id, ds)

                # Otherwise, get the corresponding column from the data table
                for i in range(0, len(metadata[ds])):
                    if variable_id == metadata[ds][i].variable:
                        columns[ds].append(metadata[ds][i])
                        break
            except VariableNotFoundError:
                traceback.print_exc()

    # Compare metadata table to data tables
    for ds in DATASETS:
        for var_info in metadata[ds]:
            try:
                # List of columns from the current dataframe
                curr_columns = data[ds].columns.values

                # If the variable is missing from the current columns, raise an exception
                if not any(col == var_info.variable for col in curr_columns):
                    raise VariableNotFoundError(var_info.variable, ds)

                # Otherwise, get the corresponding item
                for i in range(0, len(curr_columns)):
                    # Check whether the variable is already in the current list
                    if not any(series.variable == var_info.variable for series in columns[ds]):
                        columns[ds].append(var_info)
                        break
            except VariableNotFoundError:
                traceback.print_exc()

    return columns


def create_cat_cont(
    columns: dict[str, list[pd.Series]],
    data: dict[str, pd.DataFrame]
) -> tuple[dict[str, list[pd.Series]], dict[str, list[pd.Series]]]:
    """
    Creates dict of category columns and continuous columns (previously done in `read_data.py`).

    These are returned as a tuple and are meant to be unpacked directly when making the function call.

    :param columns: dictionary of columns from which to filter cats and conts
    :param data: dictionary of datasets mapped to their corresponding dataframes
    :return: tuple of category columns and continuous columns
    """
    cat_cols, cont_cols = defaultdict(list), defaultdict(list)

    # Category columns consist of all columns which contain data of the type `object` or `category`
    for ds in DATASETS:
        cat_cols[ds] = [
            col for col in columns[ds]
            if data[ds][col.variable].dtype.name in ["object", "category"]
        ]

    # The continuous columns consist of all columns which are not in `cat_cols` and in addition,
    # must not contain the variable `ObservationID`
    for ds in DATASETS:
        for col in columns[ds]:
            if col.variable != "ObservationID":
                if not any(col.variable == series.variable for series in cat_cols[ds]) \
                        and not any(col.variable == series.variable for series in cont_cols[ds]):
                    cont_cols[ds].append(col)

    return cat_cols, cont_cols


def save_cat_cont() -> None:
    """
    Uses the functions above to save the category columns and continuous columns
    in two .pickle files within the directory `SAVE_PATH`.
    """
    data = read_data_tables()
    metadata = read_metadata_table()
    columns = compare_tables(data, metadata)
    CAT_COLS, CONT_COLS = create_cat_cont(columns, data)

    # Save `CAT_COLS` and `CONT_COPLS` as .pickle files within data/viz/variable_table
    try:
        with open(SAVE_PATH + "/cat_cols.pickle", "wb") as catf:
            pickle.dump(CAT_COLS, catf)

        with open(SAVE_PATH + "/cont_cols.pickle", "wb") as contf:
            pickle.dump(CONT_COLS, contf)
    except IOError as e:
        print(f"I/O error({e.errno}): {e.strerror}")
    except Exception as e:
        print(f"An unexpected exception occurred: {e}")


def main() -> None:
    save_cat_cont()


if __name__ == "__main__":
    main()
