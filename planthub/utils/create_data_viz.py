import os

import pandas as pd
import numpy as np
import scipy
from scipy.stats import mode
import copy
import numpy as np
import xarray as xr
import itertools
import time
from pathlib import Path

key_col = 'AccSpeciesName'
output_name = "Phenobs"
path = data_path = os.path.join(Path(__file__).resolve(strict=True).parent.parent, 'data', 'viz')
# df_TRY=pd.read_csv('TRY data_2021-12-10.csv', encoding='unicode_escape',low_memory=False)
#df_data = pd.read_csv('TRY_2022-05-09', encoding='unicode_escape', low_memory=False)
df_data = pd.read_csv(os.path.join(data_path, 'PhenObs_2022-02-28 (1).csv'), encoding='unicode_escape', low_memory=False)
df_genera = pd.read_csv(os.path.join(data_path,'PlantHub genera_2022-05-13_v3.csv'), encoding='UTF-8', low_memory=False, encoding_errors="replace")
df_family = pd.read_csv(os.path.join(data_path,'PlantHub families_2022-05-10.csv'), encoding='UTF-8', low_memory=False, encoding_errors="replace")
df_order = pd.read_csv(os.path.join(data_path,'PlantHub orders_2022-05-10.csv'), encoding='UTF-8', low_memory=False, encoding_errors="replace")


def mode_on_cols(df, key_col, value_cols):
    # First find all keys so we can the modes later
    result = copy.copy(df[key_col])
    result = result.to_frame(key_col)
    result.drop_duplicates(inplace=True)
    for col in value_cols:
        col_data_to_be_merged = df.groupby([key_col, col]).size() \
            .to_frame('count').reset_index() \
            .sort_values('count', ascending=False) \
            .drop_duplicates(subset=key_col) \
            [[key_col, col]]
        result = result.merge(
            col_data_to_be_merged,
            on=key_col, how='outer',
        )
    return result


def aggregate_dataframe_on_species(df):
    # First we just declare some columns as categories/numerical. Nothing of importance is happening here
    columns = sorted(df.columns)
    discrete = [x for x in columns if df[x].dtype.name in ['object', 'category']]
    continuous = [x for x in columns if x not in discrete]
    cat_cols = [i for i in discrete if i != 'AccSpeciesName']
    numcols = [x for x in continuous if x != 'ObservationID']

    # Now we aggregate the categories
    species_df_cat = mode_on_cols(df, 'AccSpeciesName', cat_cols)
    # Now we aggregate the numerical data
    species_df_non_cat = df[['AccSpeciesName'] + numcols].groupby('AccSpeciesName').agg('mean')
    # Now we count, how many items each species has (stored in a columnt called 'count')
    count_df = df.groupby('AccSpeciesName').agg(count=('ObservationID', 'count'))
    # Now we merge the results together (first the categorical and non-categorical and then also the count)
    df_new = species_df_cat.merge(species_df_non_cat, on='AccSpeciesName', how='outer')
    df_new = df_new.merge(count_df, on='AccSpeciesName', how='outer')
    return df_new


def compute_number_of_crossings_xy(df: pd.DataFrame, name_of_df):
    cols = df.columns
    n = len(cols)
    da = xr.DataArray(
        np.zeros((n, n), dtype=int),
        [
            ("x-col", cols),
            ("y-col", cols),
        ]
    )

    for i, x in enumerate(cols):
        for j, y in enumerate(cols):
            if i < j:
                size = len(df[[x, y]].dropna())
                da.data[i, j] = da.data[j, i] = size

    da.to_netcdf(f'{name_of_df}_xy.nc')
    return da


def compute_number_of_crossings_xyz(df: pd.DataFrame, name_of_df: str):
    cols = df.columns
    n = len(cols)
    print(n)
    da = xr.DataArray(
        np.zeros((n, n, n), dtype=int),
        [
            ("x-col", cols),
            ("y-col", cols),
            ("z-col", cols),
        ]
    )
    with xr.open_dataarray(f'{name_of_df}_xy.nc') as da_stored:
        da_stored.load()

    for i, x in enumerate(cols):
        for j, y in enumerate(cols):
            # The computation is very costly, so let's check whether there is at least the chance to find any plants.
            # They have to have values at least for x and y.
            if da_stored.data[i, j] > 0:
                for k, z in enumerate(cols):
                    if i < j < k:
                        size = len(df[[x, y, z]].dropna())
                        # Every possible order of x,y,z has the same size. Let's store it in every possible order
                        for order in list(itertools.permutations([i, j, k])):
                            da.data[order] = size

    da.to_netcdf(f'{name_of_df}_xyz.nc')
    return da


def compute_number_of_crossings_xyzw(df: pd.DataFrame, name_of_df: str):
    cols = df.columns
    n = len(cols)
    da = xr.DataArray(
        np.zeros((n, n, n, n), dtype=int),
        [
            ("x-col", cols),
            ("y-col", cols),
            ("z-col", cols),
            ("w-col", cols),
        ]
    )

    with xr.open_dataarray(f'{name_of_df}_xyz.nc') as da_stored:
        da_stored.load()

    for i, x in enumerate(cols):
        print(i, n)
        for j, y in enumerate(cols):
            for k, z in enumerate(cols):
                # The computation is very costly, so let's check whether there is at least the chance to find any plants.
                # They have to have values at least for x, y and z. Also the order does not matter, so only check in case i<j<k
                # So we do not repeat unnecessary requests to da_stored
                if i < j < k and da_stored.data[i, j, k] > 0:
                    for l, w in enumerate(cols):
                        if i < j < k < l:
                            size = len(df[[x, y, z, w]].dropna())
                            # Every possible order of x,y,z,w has the same size. Let's store it in every possible order
                            for order in list(itertools.permutations([i, j, k, l])):
                                da.data[order] = size

    da.to_netcdf(f'{name_of_df}_xyzw.nc')
    return da


def prepare_dataframe_for_plotting_and_save_to_disk(df, name_of_dataframe):
    columns = sorted(df.columns)
    discrete = [x for x in columns if df[x].dtype.name in ['object', 'category']]
    continuous = [x for x in columns if x not in discrete]

    # If you tell pandas to treat categorical columns as categories, some operations will be faster in the website
    for c in discrete:
        df[c] = pd.Categorical(df[c])

    for row in discrete:
        df[row] = df[row].cat.add_categories(['unknown'])
    df[discrete] = df[discrete].fillna('unknown')

    df.to_pickle(f'{name_of_dataframe}.pickle')
    return df


def add_family(df):
    print(df_genera.head(40))
    # df_genera['EnglishName'].replace('"ë"','"ë"',inplace=True)
    # df_genera['GermanName'].replace('"ë"','"ë"',inplace=True)
    result = pd.merge(df, df_genera, on='AccGenus', how='left')
    return result

def add_order(df):
    result = pd.merge(df, df_family, on='Family', how='left')
    return result


def add_superorder(df):
    result = pd.merge(df, df_order, on='Order', how='left')
    return result

def drop_lang_cols(df):
    df.drop(columns=['EnglishName', 'GermanName'], inplace=True)
    return df


def add_hierachry(df):
    df_data = drop_lang_cols(df)

    df_family = add_family(df_data)
    df_family = drop_lang_cols(df_family)

    df_order = add_order(df_family)
    df_order = drop_lang_cols(df_order)

    df_superorder = add_superorder(df_order)
    df_superorder = drop_lang_cols(df_superorder)

    return df_superorder

def prepare_for_viz():
    df_data_species = aggregate_dataframe_on_species(df_data)

    df_data_all = add_hierachry(df_data)
    df_data_all_species = add_hierachry(df_data_species)

    compute_number_of_crossings_xy(df_data_all, output_name)
    compute_number_of_crossings_xyz(df_data_all, output_name)
    compute_number_of_crossings_xyzw(df_data_all, output_name)
    prepare_dataframe_for_plotting_and_save_to_disk(df_data_all, output_name)

    compute_number_of_crossings_xy(df_data_all_species, output_name + "_Species")
    compute_number_of_crossings_xyz(df_data_all_species, output_name + "_Species")
    compute_number_of_crossings_xyzw(df_data_all_species, output_name + "_Species")
    prepare_dataframe_for_plotting_and_save_to_disk(df_data_all_species, output_name + "_Species")

# prepare_for_viz()
