"""
This module is used for reading the category and continuous column dictionaries
from the .pickle files. It also contains a function which returns all the columns
bundled in a list, which is necessary for the z-category within the 3D scatter plot.

Attributes:
    CAT_COLS: contains all read category columns
    CONT_COLS: contains all read continuous columns
"""

__author__ = "Yannick Brenning"
__email__ = "yb63tadu@studserv.uni-leipzig.de"

import os
from pathlib import Path

import pandas as pd

PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent.parent,
    "data", "viz", "variable_table"
)

CAT_COLS: dict[str, list[pd.Series]] = pd.read_pickle(PATH + "/cat_cols.pickle")
CONT_COLS: dict[str, list[pd.Series]] = pd.read_pickle(PATH + "/cont_cols.pickle")


def get_all_cols() -> list[pd.Series]:
    """
    Create a list containing cat and cont columns, not grouped by dataset.

    :return: all columns within `CAT_COLS` and `CONT_COLS`
    """
    all_cols = []
    for df in CAT_COLS.values():
        for col in df:
            if col.variable not in [series.variable for series in all_cols]:
                all_cols.append(col)

    for df in CONT_COLS.values():
        for col in df:
            if col.variable not in [series.variable for series in all_cols]:
                all_cols.append(col)

    return all_cols
