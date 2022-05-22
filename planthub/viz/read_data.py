import os
import pandas as pd
import xarray as xr
from django.conf import settings
from pathlib import Path

# path = str(settings.APPS_DIR) + "/viz/"
path = data_path = os.path.join(Path(__file__).resolve(strict=True).parent.parent, 'data', 'viz')
print(path)
# TODO: This list should come in the future from the database
datasets = ['TRY', 'TRY_Species']  # 'PhenObs', 'PhenObs_Species'
# datasets = ['TRY', 'PhenObs', 'TRY_Species', 'PhenObs_Species', 'Phenobs_Test2_Species']
active_datasets = []

data_frames = {}
for item in datasets:
    try:
        data_frames[item] = pd.read_pickle(os.path.join(path, item + '.pickle'))
        active_datasets.append(item)
    except FileNotFoundError:
        print(item + " not found.")

dataframe_options = [{'label': i.replace("_", " "), 'value': i} for i in data_frames]

xy_crossings = {}
for df in data_frames:
    with xr.open_dataarray(os.path.join(path, df + '_xy.nc')) as da:
        da.load()
    xy_crossings[df] = da

xyz_crossings = {}
for df in data_frames:
    with xr.open_dataarray(os.path.join(path, df + '_xyz.nc')) as da:
        da.load()
    xyz_crossings[df] = da

xyzw_crossings = {}
for df in data_frames:
    with xr.open_dataarray(os.path.join(path, df + '_xyzw.nc')) as da:
        da.load()
    xyzw_crossings[df] = da

# discrete_columns is a dictionary of the form
# {'TRY': all columns of this dataset that are categories, 'PhenObs': all cats of Phenobs, ...}
cat_columns = {}
for name_of_data_frame in data_frames:
    df = data_frames[name_of_data_frame]
    columns = sorted(df.columns)
    cats = [x for x in columns if df[x].dtype.name in ['object', 'category']]
    cat_columns[name_of_data_frame] = cats

# continuous_columns is a dictionary of the form
# {'TRY': all columns of this dataset that contain real numbers, 'PhenObs': all continous columns of Phenobs, ...}
continuous_columns = {}
for name_of_data_frame in data_frames:
    df = data_frames[name_of_data_frame]
    columns = sorted(df.columns)
    cats = [x for x in columns if df[x].dtype.name in ['object', 'category']]
    continuous = [x for x in columns if x not in cats]
    continuous = [i for i in continuous if i != 'ObservationID']
    continuous_columns[name_of_data_frame] = continuous


def get_valid_second_column(name_of_dataframe, col):
    return [col2 for col2 in xy_crossings[name_of_dataframe].get_index('x-col') if
            xy_crossings[name_of_dataframe].loc[col, col2].item() > 0]


def get_valid_third_column(name_of_dataframe, x_col, y_col):
    return [col3 for col3 in xyz_crossings[name_of_dataframe].get_index('x-col') if
            xyz_crossings[name_of_dataframe].loc[x_col, y_col, col3].item() > 0]


def get_valid_fourth_column(name_of_dataframe, x_col, y_col, z_col):
    return [col4 for col4 in xyzw_crossings[name_of_dataframe].get_index('x-col') if
            xyzw_crossings[name_of_dataframe].loc[x_col, y_col, z_col, col4].item() > 0]


def get_active_dataset():
    return active_datasets
