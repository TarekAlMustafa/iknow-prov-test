import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import numpy as np
import pandas as pd
import colorcet as cc
from dash import dash
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash

from .read_data import data_frames, continuous_columns, cat_columns, get_valid_third_column, get_valid_second_column, \
    get_valid_fourth_column, dataframe_options

app = DjangoDash('scatter_3D_cat')


def create_scatter_plot(name_of_data_frame, x, y, z, color, show_nan):
    """

    :param name_of_data_frame:
    :param x: Name of column for x-coordinate
    :param y: Name of column for y-coordinate
    :param z: Name of column for z-coordinate
    :param color: Name of categorical column for coloring the points (or 'None' if no coloring is desired)
    :param show_nan: Also show points for which the category is unknown (in case color!='None')
    :return:
    """
    # We need to do it this complicated way because the naive plotly-ways is too slow for datasets of this size.
    # So we do the preprocessing ourselves using fast libraries like pandas.
    df = data_frames[name_of_data_frame]
    # key-word-arguements will be used to tell plotly how to format the plot
    kwargs = {}
    # Request the needed data according to parameters
    if color == 'None':
        helper_df = df[[x, y, z, 'AccSpeciesName', ]].dropna(subset=[x, y, z])
    else:
        if show_nan:
            helper_df = df[[x, y, z, color, 'AccSpeciesName', ]].dropna(subset=[x, y, z])
        else:
            helper_df = df[[x, y, z, color, 'AccSpeciesName', ]].replace('unknown', np.nan).dropna()
        # do the coloring, gray for 'unknown'
        categories = helper_df[color].dropna().drop_duplicates()
        categories = [c for c in categories if c != 'unknown']
        cmap_list = zip(categories, cc.glasbey)
        cmap_dict = {n: k for n, k in cmap_list}
        cmap_dict['unknown'] = 'gray'
        kwargs['color'] = color
        kwargs['color_discrete_map'] = cmap_dict
    # Tell the user how many points there are (and whether there were too many/zero...)
    size = len(helper_df)
    kwargs['title'] = f'Scatterplot ({size} datapoints): {x} vs. {y} vs.{z}'
    if size > 20000:
        helper_df = helper_df.sample(n=20000)
        kwargs['title'] = f'Too many points to show in a browser. You only see a sample of 20000 out of {size} points'
    if len(helper_df) == 0:
        # This is unlikely to happen thanks to callbacks
        kwargs['title'] = 'No datapoints for the requested combination of x- y- and z-axis. Maybe checking "Show ' \
                          'unknown values" will help '
    return px.scatter_3d(helper_df, x=x, y=y, z=z, hover_name='AccSpeciesName', **kwargs)


app.layout = html.Div(children=[
   #html.H1(children=[
   #     'Number of values: ',
   #     html.Div(id='ticker_header', style={'display': 'inline'}),
   #
   # ]),
    html.Div([
        "Choose dataset:",
        dcc.RadioItems(
            id='dataframe',
            options=dataframe_options,
            value='TRY',
        )
    ]),
    html.Div([
        html.Div([
            "x-axis:",
            dcc.Dropdown(
                id='x-axis',

            ),
        ]),
        html.Div([
            "y-axis:",
            dcc.Dropdown(
                id='y-axis',

            ),
        ]),
        html.Div([
            "z-axis:",
            dcc.Dropdown(
                id='z-axis',

            ),
        ]),

        html.Div([
            "color:",
            dcc.Dropdown(
                id='color-column',

            ),
        ]),
        html.Div([
            dcc.Checklist(
                id='show_nan',
                options=[
                    {'label': "Show plants for which the value of the chosen color-column is not known",
                     'value': 'show_nan'},
                ],
                value=[]
            )
        ]),
    ],

    ),
    dcc.Loading(
        dcc.Graph(
            id='scatter_plot',
            figure=px.scatter_3d().add_annotation(text="Plot is being computed. This can take some seconds.",
                                                  showarrow=False, font={"size": 20})

        ),
        debug=True,
        type='cube',
    )

])


@app.callback(
    Output('x-axis', 'options'),
    Output('x-axis', 'value'),
    Input('dataframe', 'value'),
    State('x-axis', 'value'),
)
def update_possible_densities(name_of_data_frame, old_value):
    cols = [{'label': i, 'value': i} for i in continuous_columns[name_of_data_frame]]
    # In case the original x-value is still allowed, we keep it, else we just take any arbitrary allowed value
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('y-axis', 'options'),
    Output('y-axis', 'value'),
    Input('dataframe', 'value'),
    Input('x-axis', 'value'),
    State('y-axis', 'value')
)
def filter_y_values(name_of_dataframe, x_col, old_value):
    cols = [{'label': i, 'value': i} for i in
            get_valid_second_column(name_of_dataframe, x_col) if i in continuous_columns[name_of_dataframe]]

    # In case the original y-value is still allowed, we keep it, else we just take any arbitrary allowed value
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('z-axis', 'options'),
    Output('z-axis', 'value'),
    Input('dataframe', 'value'),
    Input('y-axis', 'value'),
    Input('x-axis', 'value'),
    State('z-axis', 'value'),
)
def filter_z_values(name_of_dataframe, y_col, x_col, old_value):
    # I also allow categorical values for the z-axis. If you think this is bad, feel free to change that
    cols = [{'label': i, 'value': i} for i in get_valid_third_column(name_of_dataframe, x_col, y_col)]
    # In case the original z-value is still allowed, we keep it, else we just take any arbitrary allowed value
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('color-column', 'options'),
    Output('color-column', 'value'),
    Input('dataframe', 'value'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
    Input('z-axis', 'value'),
    State('color-column', 'value'),
)
def filter_color_cats(name_of_dataframe, x_col, y_col, z_col, old_value):
    color_col_option = [{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in
                                                               cat_columns[name_of_dataframe] if i in
                                                               get_valid_fourth_column(name_of_dataframe, x_col,
                                                                                       y_col, z_col) and
                                                               i != 'AccSpeciesName']
    # In case the original color-value is still allowed, we keep it, else we just take None
    if old_value in [i['value'] for i in color_col_option]:
        new_value = old_value
    else:
        new_value = 'None'
    return color_col_option, new_value


@app.callback(
    Output('scatter_plot', 'figure'),
    Input('dataframe', 'value'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
    Input('z-axis', 'value'),
    Input('color-column', 'value'),
    Input('show_nan', 'value'),
)
def update_graph(name_of_data_frame, xaxis_column_name, yaxis_column_name, zaxis_column_name,
                 color_column_name, show_nan):
    if show_nan == []:
        nan = False
    if show_nan == ['show_nan']:
        nan = True
    return create_scatter_plot(name_of_data_frame, xaxis_column_name, yaxis_column_name, zaxis_column_name,
                               color_column_name, nan)
