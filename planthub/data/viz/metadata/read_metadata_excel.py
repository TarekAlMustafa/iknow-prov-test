#!usr/bin/env python3

"""
This script transforms an Excel file (.xlsx) into a .pickle file within the same directory.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

Note:
    The Excel file containing the metadata must be in the same directory as this script.
"""

__author__ = "Yannick Brenning"

import os
import traceback
from pathlib import Path

import pandas as pd

EXCEL_FILE_PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent,
    "PlantHub variable information_2023-01-04.xlsx"  # Set this to current name of excel file
)

PICKLE_SAVE_PATH = os.path.join(
    Path(__file__).resolve(strict=True).parent,
    "metadata.pickle"
)


def generate_pickle() -> None:
    df = pd.read_excel(EXCEL_FILE_PATH)
    df.to_pickle(PICKLE_SAVE_PATH)


def show_pickle() -> None:
    df = pd.read_pickle(PICKLE_SAVE_PATH)
    print(df)


def main() -> None:
    try:
        generate_pickle()
        show_pickle()
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
