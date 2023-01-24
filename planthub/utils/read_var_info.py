#!usr/bin/env python3

"""
The updated variable metadata will be located in the data/viz/metadata directory.
For now, the dataset names to be used are a global hardcoded constant, like in `read_data.py`.

Note:
    If the metadata directory does not contain `metadata.pickle`, generate the pickle file using the most
    recent Excel file and the script `read_metadata_excel.py` within the same directory.

TODO: Remove `casefold()` on variable ID comparison once data table gets fixed
"""

__author__ = "Yannick Brenning"

import logging
import os
import pickle
import traceback
from collections import defaultdict
from pathlib import Path

import pandas as pd

DATASETS = [
    "TRY",
    "PhenObs",
    "sPlot",
    "GloNAF"
]

CONST_DATASETS = [
    "PlantHub genera",
    "PlantHub families",
    "PlantHub orders"
]

DATA_PATH = os.path.join(Path(__file__).resolve(strict=True).parent.parent, "data", "viz")

METADATA_PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent.parent,
    "data", "viz", "metadata", "metadata.pickle"
)

SAVE_PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent.parent,
    "data", "viz", "metadata"
)


class VariableNotFoundError(Exception):
    """
    Raise this exception when a variable name mismatch occurs
    during the comparison of the metadata and data tables.
    """
    def __init__(self, variable: str, dataset: str) -> None:
        super().__init__(f"{dataset}: {variable} was not found.")


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

    All variable information is processed from a dataframe into a dictionary `metadata`,
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

    metadata = {}
    for ds in DATASETS + CONST_DATASETS:
        metadata[ds] = [row[1] for row in df.iterrows() if row[1].dataset == ds]

    return metadata


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
    for ds in DATASETS + CONST_DATASETS:
        dds = DATASETS[0] if ds.startswith("PlantHub") else ds
        cds = "PlantHub" if ds.startswith("PlantHub") else ds

        for variable_id in data[dds].columns.values:
            try:
                # Attempt to get the corresponding column from the data table
                for series in metadata[ds]:
                    if variable_id.casefold() == series.variable.casefold():
                        if not any(col.variable.casefold() == series.variable.casefold() for col in columns[cds]):
                            columns[cds].append(series)
                        logging.info(f"{ds}: {variable_id} was found.")
                        break
                else:
                    raise VariableNotFoundError(variable_id, ds)
            except VariableNotFoundError as e:
                traceback.print_exc()
                logging.warning(e)

    # Compare metadata table to data tables
    for ds in DATASETS + CONST_DATASETS:
        dds = DATASETS[0] if ds.startswith("PlantHub") else ds
        cds = "PlantHub" if ds.startswith("PlantHub") else ds

        for series in metadata[ds]:
            try:
                # List of columns from the current dataframe
                curr_columns = data[dds].columns.values

                # Attempt to get the corresponding item
                for col in curr_columns:
                    # Check whether the variable is already in the current list
                    if col.casefold() == series.variable.casefold():
                        if not any(col.variable.casefold() == series.variable.casefold() for col in columns[cds]):
                            columns[cds].append(series)
                        logging.info(f"{ds}: {series.variable} was found.")
                        break
                else:
                    raise VariableNotFoundError(series.variable, ds)
            except VariableNotFoundError as e:
                traceback.print_exc()
                logging.warning(e)

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
    for ds, cols in columns.items():
        for col in cols:
            dds = DATASETS[0] if ds.startswith("PlantHub") else ds
            assert any(variable_id.casefold() == col.variable.casefold()
                       for variable_id in data[dds].columns.values)

    cat_cols, cont_cols = defaultdict(list), defaultdict(list)

    # Category columns consist of all columns which contain data of the type `object` or `category`
    for ds in DATASETS:
        dds = DATASETS[0] if ds.startswith("PlantHub") else ds
        cat_cols[ds] = [
            col for col in columns[ds]
            if data[dds][col.variable].dtype.name in ["object", "category"]
        ]

    # The continuous columns consist of all columns which are not in `cat_cols` and in addition,
    # must not contain the variable `ObservationID`
    for ds in DATASETS:
        for col in columns[ds]:
            if col.variable != "ObservationID":
                if not any(col.variable == series.variable for series in cat_cols[ds]) \
                        and not any(col.variable == series.variable for series in cont_cols[ds]):
                    cont_cols[ds].append(col)

            cat_names = [col.name for col in cat_cols[ds]]
            cont_names = [col.name for col in cont_cols[ds]]
            assert set(cat_names).isdisjoint(cont_names)

    return cat_cols, cont_cols


def save_cat_cont() -> None:
    """
    Uses the functions above to save the category columns and continuous columns
    in two .pickle files within the directory `SAVE_PATH`.

    Note:
        To show data table, metadata table and result of comparison, set logging level to `DEBUG`.
    """
    data = read_data_tables()
    if logging.getLogger().level == logging.DEBUG:
        for ds in DATASETS:
            print(ds, data[ds].columns)
        print("")

    metadata = read_metadata_table()
    if logging.getLogger().level == logging.DEBUG:
        for ds in DATASETS + CONST_DATASETS:
            print(ds, [n.variable for n in metadata[ds]])
            print("")

    columns = compare_tables(data, metadata)
    if logging.getLogger().level == logging.DEBUG:
        for key, value in columns.items():
            print(key + ": ")
            for col in value:
                print(col.variable)
            print("")

    CAT_COLS, CONT_COLS = create_cat_cont(columns, data)

    # Save `CAT_COLS` and `CONT_COLS` as .pickle files within data/viz/metadata
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
    logging.basicConfig(
        filename="read_var_info.log",
        encoding="utf-8",
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s - %(message)s"
    )
    save_cat_cont()


if __name__ == "__main__":
    main()
