import colorcet as cc
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output, State
from django.conf import settings
from django_plotly_dash import DjangoDash

from planthub.utils.cat_cont_cols import CAT_COLS, CONT_COLS

from .format import format_labels, get_cat_name
from .read_data import (
    data_frames,
    dataframe_options,
    get_valid_second_column,
    get_valid_third_column,
)

app = DjangoDash('scatter_cat')
app.css.append_css({"external_url": settings.STATIC_URL_PREFIX + "/static/css/dashstyle.css"})


def create_scatter_plot(name_of_data_frame, x, y, color, log_x, log_y):
    """Creates a two-dim scatter-plot

    :param name_of_data_frame: Name of data frame to plot. Will be looked up in a dictionary called data_frames.
    :param x: name of column to use as x-coordinate to plot
    :param y: name of column to use as y-coordinate to plot
    :param color: name of CATEGORICAL column to use as a color-scheme (use 'None' in order not to use any color-scheme)
    :return: plotly-plot
    """
    df = data_frames[name_of_data_frame]
    # We use key-word-arguments to tell plotly how to design the plot
    kwargs = {}
    if color == 'None':
        helper_df = df[[x, y, 'AccSpeciesName', ]].dropna(subset=[x, y])
        helper_df.columns = [
            get_cat_name(name_of_data_frame, x, CONT_COLS),
            get_cat_name(name_of_data_frame, y, CONT_COLS),
            "AccSpeciesName"
        ]
    else:
        helper_df = df[[x, y, color, 'AccSpeciesName', ]].dropna(subset=[x, y])
        # Now we make sure that the category 'unknown' gets colored gray
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
            get_cat_name(name_of_data_frame, color, CAT_COLS),
            "AccSpeciesName"
        ]
    # Tell the user how many points there are (and whether there were too many/zero...)
    size = len(helper_df)
    kwargs['title'] = f'{size} datapoints: Scatterplot {get_cat_name(name_of_data_frame, x, CONT_COLS)} ' \
                      f'vs. {get_cat_name(name_of_data_frame, y, CONT_COLS)}'
    if size > 20000:
        helper_df = helper_df.sample(n=20000)
        kwargs['title'] = f'Too many points to show in a browser. You only see a sample of 20000 out of {size} points'
    if len(helper_df) == 0:
        # This cannot happen thanks to callbacks. But let's be sure
        kwargs['title'] = 'No datapoints for the requested combination of x-axes and y-axes'

    return px.scatter(
        helper_df,
        x=get_cat_name(name_of_data_frame, x, CONT_COLS),
        y=get_cat_name(name_of_data_frame, y, CONT_COLS),
        hover_name='AccSpeciesName',
        log_y=log_y,
        log_x=log_x,
        **kwargs
    )


app.layout = html.Div(children=[
    html.H1(children='Scatter-Plot (coloring according to categories)', className="header-title"),
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
            "x-axis:",
            dcc.Dropdown(
                id='x-axis',
                # Instead of hardcoding options and value, they are constructed at run-time and updated regulary
                # options=[{'label': i, 'value': i} for i in continuous],
                # value='TRY_Leaf carbon (C) isotope signature (delta 13C)',
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
            "y-axis:",
            dcc.Dropdown(
                id='y-axis',
                # Instead of hardcoding options and value, they are constructed at run-time and updated regulary
                # options=[{'label': i, 'value': i} for i in continuous],
                # value='TRY_Leaf carbon/nitrogen (C/N) ratio',
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
            "color:",
            dcc.Dropdown(
                id='color-column',
                # Instead of hardcoding options and value, they are constructed at run-time and updated regulary
                # options=[{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in discrete if
                #                                                i != 'AccSpeciesName'],
                # value='TRY_Growth form 2',
                searchable=True,
                className="dropdown-list"
            ),
        ],
            className="dropdown"),
    ], ),
    dcc.Loading(
        dcc.Graph(
            id='scatter_plot',
            # final plot is created in a callback
            figure=px.scatter().add_annotation(text="Plot is being computed. This can take some seconds.",
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
def update_x_cols(name_of_data_frame, old_value):
    """When the user chooses a new dataframe, this function updates the possible options and values for x
    and color-column

    :param name_of_data_frame:
    :return:
    """
    cols = format_labels(name_of_data_frame, CONT_COLS)

    # Just take any possible option as start value. In our case it is the last of all possible options for x
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
def update_y_cols(name_of_dataframe, x_col, old_value):
    """When the user (or another callback) chooses a new x-column, the y-columns that still allow non-empty plots
    become the new options the user can choose from. If the old y-column is still valid, it is kept, else an arbitrary
    y-column is chosen

    :param name_of_dataframe:
    :param x_col:
    :param old_value:
    :return:
    """
    cols = format_labels(name_of_dataframe, CONT_COLS, valid_cols=get_valid_second_column(name_of_dataframe, x_col))

    # In case the original y-value is still allowed, we keep it, else we just take any arbitrary allowed value
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
    State('color-column', 'value'),
)
def filter_color_cats(name_of_dataframe, x_col, y_col, old_value):
    color_col_option = [
        i for i in format_labels(
            name_of_dataframe,
            CAT_COLS,
            valid_cols=get_valid_third_column(name_of_dataframe, x_col, y_col))
        if i != "AccSpeciesName"
    ]

    # In case the original color-value is still allowed, we keep it, else we just take 'None'
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
    Input('color-column', 'value'),
    Input('show_log_x', 'value'),
    Input('show_log_y', 'value'))
def update_graph(name_of_dataframe, xaxis_column_name, yaxis_column_name,
                 color_column_name, show_log_x, show_log_y):
    """Creates a new plot whenever the user (or a callback) changes any relevant parameter

    :param name_of_dataframe:
    :param xaxis_column_name:
    :param yaxis_column_name:
    :param color_column_name:
    :return:
    """
    if show_log_x == []:
        log_x = False
    if show_log_x == ['show_log_x']:
        log_x = True

    if show_log_y == []:
        log_y = False
    if show_log_y == ['show_log_y']:
        log_y = True

    return create_scatter_plot(name_of_dataframe, xaxis_column_name, yaxis_column_name, color_column_name, log_x, log_y)
