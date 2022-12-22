import colorcet as cc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output, State
from django.conf import settings
from django_plotly_dash import DjangoDash

from planthub.utils.cat_cont_cols import CAT_COLS, CONT_COLS, get_all_cols

from .format import format_labels, format_z_values, get_cat_name, get_z_cat_name
from .read_data import (
    data_frames,
    dataframe_options,
    get_valid_fourth_column,
    get_valid_second_column,
    get_valid_third_column,
)

app = DjangoDash('scatter_3D_cat')
app.css.append_css({"external_url": settings.STATIC_URL_PREFIX + "/static/css/dashstyle.css"})


def create_scatter_plot(name_of_data_frame, x, y, z, color, show_nan, log_x, log_y, log_z):
    """

    :param name_of_data_frame:
    :param x: Name of column for x-coordinate
    :param y: Name of column for y-coordinate
    :param z: Name of column for z-coordinate
    :param color: Name of categorical column for coloring the points (or 'None' if no coloring is desired)
    :param show_nan: Also show points for which the category is unknown (in case color!='None')
    :param log_x: Log scale for x-coordinate
    :param log_y: Log scale for y-coordinate
    :param log_z: Log scale for z-coordinate
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
        print(helper_df)
        helper_df.columns = [
            get_cat_name(name_of_data_frame, x, CONT_COLS),
            get_cat_name(name_of_data_frame, y, CONT_COLS),
            get_z_cat_name(get_all_cols(), z),
            "AccSpeciesName"
        ]
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
        kwargs['color'] = get_cat_name(name_of_data_frame, color, CAT_COLS)
        kwargs['color_discrete_map'] = cmap_dict

        helper_df.columns = [
            get_cat_name(name_of_data_frame, x, CONT_COLS),
            get_cat_name(name_of_data_frame, y, CONT_COLS),
            get_z_cat_name(get_all_cols(), z),
            get_cat_name(name_of_data_frame, color, CAT_COLS),
            "AccSpeciesName"
        ]

    # Tell the user how many points there are (and whether there were too many/zero...)
    size = len(helper_df)
    kwargs['title'] = f'Scatterplot ({size} datapoints): {get_cat_name(name_of_data_frame, x, CONT_COLS)} ' \
                      f'vs. {get_cat_name(name_of_data_frame, y, CONT_COLS)} ' \
                      f'vs.{get_z_cat_name(get_all_cols(), z)}'

    if size > 20000:
        helper_df = helper_df.sample(n=20000)
        kwargs['title'] = f'Too many points to show in a browser. You only see a sample of 20000 out of {size} points'
    if len(helper_df) == 0:
        # This is unlikely to happen thanks to callbacks
        kwargs['title'] = 'No data points for the requested combination of x- y- and z-axis. Maybe checking "Show ' \
                          'unknown values" will help '

    return px.scatter_3d(
        helper_df,
        x=get_cat_name(name_of_data_frame, x, CONT_COLS),
        y=get_cat_name(name_of_data_frame, y, CONT_COLS),
        z=get_z_cat_name(get_all_cols(), z),
        hover_name='AccSpeciesName',
        log_z=log_z,
        log_y=log_y,
        log_x=log_x,
        **kwargs
    )


app.layout = html.Div(children=[
    html.H1(children='3D Scatter plot (coloring according to categories)', className="header-title"),
    html.Div([
        "Dataset",

        dcc.RadioItems(
            id='dataframe',
            options=dataframe_options,
            value='TRY',
            className="radio-items",
            labelClassName="radio-label"
        ),

    ], className="radio"),
    html.Div([
        html.Div([
            "X-axis",
            dcc.Dropdown(
                id='x-axis',
                searchable=True,
                className="dropdown-list"
            ),
        ],
            className="dropdown"),
        html.Div([
            dcc.Checklist(
                id='show_log_x',
                options=[
                    {'label': "Log scale",
                     'value': 'show_log_x'},
                ],
                value=[],
                inputClassName="checklist-input"
            )
        ],
            className="checklist-log"
        ),
        html.Div([
            "Y-axis",
            dcc.Dropdown(
                id='y-axis',
                searchable=True,
                className="dropdown-list"
            ),
        ],
            className="dropdown"),
        html.Div([
            dcc.Checklist(
                id='show_log_y',
                options=[
                    {'label': "Log scale",
                     'value': 'show_log_y'},
                ],
                value=[],
                inputClassName="checklist-input"
            )
        ],
            className="checklist-log"
        ),
        html.Div([
            "Z-axis",
            dcc.Dropdown(
                id='z-axis',
                searchable=True,
                className="dropdown-list"
            ),
        ],
            className="dropdown"),
        html.Div([
            dcc.Checklist(
                id='show_log_z',
                options=[
                    {'label': "Log scale",
                     'value': 'show_log_z'},
                ],
                value=[],
                inputClassName="checklist-input"
            )
        ],
            className="checklist-log"
        ),
        html.Div([
            "Color",
            dcc.Dropdown(
                id='color-column',
                searchable=True,
                className="dropdown-list"
            ),
        ],
            className="dropdown"),
        html.Div([
            dcc.Checklist(
                id='show_nan',
                options=[
                    {'label': "Show value of the chosen color-column is not known",
                     'value': 'show_nan'},
                ],
                value=[],
                inputClassName="checklist-input"
            )
        ],
            className="checklist-log"
        ),
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

], className="container"
)


@app.callback(
    Output('x-axis', 'options'),
    Output('x-axis', 'value'),
    Input('dataframe', 'value'),
    State('x-axis', 'value'),
)
def update_possible_densities(name_of_data_frame, old_value):
    cols = format_labels(name_of_data_frame, CONT_COLS)
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
    cols = format_labels(name_of_dataframe, CONT_COLS, valid_cols=get_valid_second_column(name_of_dataframe, x_col))

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
    # TODO: Switch y_col and x_col parameters ?
    # I also allow categorical values for the z-axis. If you think this is bad, feel free to change that
    cols = format_z_values(valid_cols=get_valid_third_column(name_of_dataframe, x_col, y_col))
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
    color_col_option = [
        i for i in format_labels(
            name_of_dataframe,
            CAT_COLS,
            valid_cols=get_valid_fourth_column(name_of_dataframe, x_col, y_col, z_col))
        if i != "AccSpeciesName"
    ]

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
    Input('show_log_x', 'value'),
    Input('show_log_y', 'value'),
    Input('show_log_z', 'value'),
)
def update_graph(name_of_data_frame, xaxis_column_name, yaxis_column_name, zaxis_column_name,
                 color_column_name, show_nan, show_log_x, show_log_y, show_log_z):
    if show_nan == []:
        nan = False
    if show_nan == ['show_nan']:
        nan = True

    if show_log_x == []:
        log_x = False
    if show_log_x == ['show_log_x']:
        log_x = True

    if show_log_y == []:
        log_y = False
    if show_log_y == ['show_log_y']:
        log_y = True

    if show_log_z == []:
        log_z = False
    if show_log_z == ['show_log_z']:
        log_z = True

    return create_scatter_plot(name_of_data_frame, xaxis_column_name, yaxis_column_name, zaxis_column_name,
                               color_column_name, nan, log_x, log_y, log_z)
