"""
Format column labels

This module contains functions used for formatting the names of category and continuous columns
to be displayed within the drop down menus, legends, axis labels and text hovers for the graphs
on the EXPLORE page.
"""

__author__ = "Yannick Brenning"
__email__ = "yb63tadu@studserv.uni-leipzig.de"

import pandas as pd

from planthub.utils.cat_cont_cols import get_all_cols


def format_labels(
    dataframe: str,
    cols: dict[str, list[pd.Series]],
    lang: str = "en",
    valid_cols: list[str] | None = None
) -> list[dict[str, str]]:
    """
    Reformat the labels of a given column dictionary

    :param dataframe: name of the current dataframe
    :param cols: dict containing the dataset
    :param lang: specifies in which language the category names should be displayed
    :param valid_cols: list of valid columns in the case of multiple drop down menus
    :return: list of dicts where each dict contains the col's label and value
    """
    if lang.casefold() == "en":
        if not valid_cols:
            return [{'label': i.variableLong_eng, 'value': i.variable} for i in cols[dataframe]]
        else:
            return [{'label': 'None', 'value': 'None'}] + \
                   [{'label': i.variableLong_eng, 'value': i.variable}
                    for i in cols[dataframe] if i.variable in valid_cols]
    elif lang.casefold() == "de":
        if not valid_cols:
            return [{'label': i.variableLong_de, 'value': i[0]} for i in cols[dataframe]]
        else:
            return [{'label': 'None', 'value': 'None'}] + \
                   [{'label': i.variableLong_de, 'value': i.variable}
                    for i in cols[dataframe] if i.variable in valid_cols]
    else:
        raise ValueError("Invalid language specifier")


def get_cat_name(
    dataframe: str,
    category: str,
    cols: dict[str, list[pd.Series]],
    lang: str = "en"
) -> str:
    """
    Given a category name and a language, get the formatted category name in the correct language.

    :param dataframe: name of the current dataframe
    :param category: name of category
    :param cols: dict containing the dataset
    :param lang: language to be displayed
    :return: category name obtained from the dataset in given language
    """
    for col in cols[dataframe]:
        if category == col.variable:
            if lang.casefold() == "en":
                return col.variableLong_eng
            elif lang.casefold() == "de":
                return col.variableLong_de
            else:
                raise ValueError("Invalid language specifier")

    raise ValueError(category, "is not a valid category")


def get_z_cat_name(cols: list[pd.Series], category: str, lang: str = "en") -> str:
    """
    Finds the correct label for a given z category.

    This must be done using an extra function as the z category
    of the 3D scatter plot contains categories from all dataframes,
    whereas the other implementations use a single dataframe name to
    access the labels.

    :param cols: list of label tuples
    :param category: ID of category
    :param lang: language to be displayed
    :return: category label in the correct language
    """
    for col in cols:
        if category == col.variable:
            if lang.casefold() == "en":
                return col.variableLong_eng
            elif lang.casefold() == "de":
                return col.variableLong_de
            else:
                raise ValueError("Invalid language specifier")

    raise ValueError(category, "is not a valid category")


def format_z_values(
    valid_cols: list[str] | None = None,
    lang: str = "en"
) -> list[dict[str, str]]:
    """
    Reformat the labels of the z category, which contains all types of columns.

    As with `get_z_cat_name()`, this reformatting is not done using the already existent generic
    implementations, as the z category of the 3D scatter plot contains all types of datasets,
    regardless of which dataset has been selected by the user.

    :param valid_cols: list of valid columns in the case of multiple drop down menus
    :param lang: specifies in which language the category names should be displayed
    :return: list of dicts where each dict contains the col's label and value
    """
    all_cols = get_all_cols()

    res: list[dict[str, str]] = []
    for col in all_cols:
        if col.variable in valid_cols:
            if lang.casefold() == "en":
                res.append({"label": col.variableLong_eng, "value": col.variable})
            elif lang.casefold() == "de":
                res.append({"label": col.variableLong_de, "value": col.variable})

    return res
