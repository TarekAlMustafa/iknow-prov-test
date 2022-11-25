from .cols import all_cols


def format_labels(dataframe: str,
                  cols: dict[list[tuple[str, str, str, str]]],
                  lang: str = "en",
                  valid_cols: list[str] = None) -> list[dict[str, str]]:
    """
    Reformat the labels of a given column dictionary

    :param dataframe: name of the current dataframe
    :param cols: dict containing the dataset
    :param lang: specifies in which language the category name should be displayed
    :param valid_cols: list of valid columns in the case of multiple drop down menus
    :return:
    """

    if lang.casefold() == "en":
        if not valid_cols:
            return [{'label': i[1], 'value': i[0]} for i in cols[dataframe]]
        else:
            return [{'label': 'None', 'value': 'None'}] + [{'label': i[1], 'value': i[0]} for i in cols[dataframe] if
                                                           i[0] in valid_cols]
    elif lang.casefold() == "de":
        if not valid_cols:
            return [{'label': i[2], 'value': i[0]} for i in cols[dataframe]]
        else:
            return [{'label': 'None', 'value': 'None'}] + [{'label': i[1], 'value': i[0]} for i in cols[dataframe] if
                                                           i[0] in valid_cols]


def get_cat_name(dataframe: str,
                 category: str,
                 cols: dict[list[tuple[str, str, str]]],
                 lang: str = "en") -> str:
    """
    Given a category name and a language, get the formatted category name in the correct language.

    :param dataframe: name of the current dataframe
    :param category: name of category
    :param cols: dict containing the dataset
    :param lang: language to be displayed
    :return: category name obtained from the dataset in given language
    """

    for col in cols[dataframe]:
        if category in col:
            if lang.casefold() == "en":
                return col[1]
            elif lang.casefold() == "de":
                return col[2]


def get_z_cat_name(cols: list[tuple[str, str, str]], category: str, lang: str = "en"):
    for col in cols:
        if category in col:
            if lang.casefold() == "en":
                print(col[1])
                return col[1]
            elif lang.casefold() == "de":
                return col[2]


def format_z_values(valid_cols: list[str] = None, lang: str = "en"):
    allcols = all_cols()

    res: list[dict[str, str]] = []
    for col in allcols:
        if col[0] in valid_cols:
            if lang.casefold() == "en":
                res.append({"label": col[1], "value": col[0]})
            elif lang.casefold() == "de":
                res.append({"label": col[2], "value": col[0]})
    return res
