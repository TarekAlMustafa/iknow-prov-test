import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output, State
from django.conf import settings
from django_plotly_dash import DjangoDash

from planthub.utils.cat_cont_cols import CONT_COLS

from .format import format_labels, get_cat_name
from .read_data import (
    data_frames,
    dataframe_options,
    get_valid_second_column,
    get_valid_third_column,
)

app = DjangoDash('scatter_cont')
app.css.append_css({"external_url": settings.STATIC_URL_PREFIX + "/static/css/dashstyle.css"})


def create_scatter_plot(name_of_data_frame, x, y, color, log_x, log_y, show_nan=True):
    """

    :param name_of_data_frame:
    :param x: Name of the column used for x-axis
    :param y:
    :param color: Name of the column used for color scheme. Optimized for continuous color-schemes.
    :param show_nan: Show points for which color-value is unknown.
    :return:
    """
    df = data_frames[name_of_data_frame]
    # kwargs contain the meta-information (like title...) that we will include in the plotly plot
    kwargs = {}
    # We first collect the data we want to display
    if color == 'None':
        helper_df = df[[x, y, 'AccSpeciesName', ]].dropna(subset=[x, y])
        helper_df.columns = [
            get_cat_name(name_of_data_frame, x, CONT_COLS),
            get_cat_name(name_of_data_frame, y, CONT_COLS),
            "AccSpeciesName"
        ]
    else:
        if show_nan:
            helper_df = df[[x, y, color, 'AccSpeciesName', ]].dropna(subset=[x, y])
        else:
            helper_df = df[[x, y, color, 'AccSpeciesName', ]].dropna()
        kwargs['color'] = get_cat_name(name_of_data_frame, color, CONT_COLS)
        kwargs['labels'] = {color: 'colorbar'}

        helper_df.columns = [
            get_cat_name(name_of_data_frame, x, CONT_COLS),
            get_cat_name(name_of_data_frame, y, CONT_COLS),
            get_cat_name(name_of_data_frame, color, CONT_COLS),
            "AccSpeciesName"
        ]
    # Tell the user how many points there are (and whether there were too many/zero...)
    size = len(helper_df)
    kwargs['title'] = f'{size} datapoints: Scatterplot {get_cat_name(name_of_data_frame, x, CONT_COLS)}' \
                      f' vs. {get_cat_name(name_of_data_frame, y, CONT_COLS),}'
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
    html.H1(children='Scatter plot (coloring using continuous quantity)', className="header-title"),
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
        "x-axis:",
        dcc.Dropdown(
            id='x-axis',
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
            # options will be created by callbacks at runtime instead of being hardcoded
            # options=[{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in continuous],
            value='None',
            searchable=True,
            className="dropdown-list"
        ),
    ],
        className="dropdown"),
    html.Div([
        dcc.Checklist(
            id='show_nan',
            options=[
                {'label': "Show plants for which the value of the chosen color-column is not known (will be shown in "
                          "gray)",
                 'value': 'show_nan'},
            ],
            value=[],
            inputClassName="checklist-input"
        )
    ],
        className="checklist-log"
    ),
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
    State('x-axis', 'value')
)
def update_possible_densities(name_of_data_frame, old_value):
    cols = format_labels(name_of_data_frame, CONT_COLS)

    # In case the original x-value is still allowed, we keep it, else we just take any arbitrary allowed value
    # (the last one in this case)
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
    Output('color-column', 'options'),
    Output('color-column', 'value'),
    Input('dataframe', 'value'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
    State('color-column', 'value'),
)
def filter_color_values(name_of_dataframe, x_col, y_col, old_value):
    # We only allow continuous columns as color where there is not only NA for the requested points
    cols = [
        i for i in format_labels(
            name_of_dataframe,
            CONT_COLS,
            valid_cols=get_valid_third_column(name_of_dataframe, x_col, y_col))
        if i != "AccSpeciesName"
    ]

    # In case the original color-value is still allowed, we keep it, else we do not use any color
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = 'None'
    return cols, new_value


@app.callback(
    Output('scatter_plot', 'figure'),
    Input('dataframe', 'value'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
    Input('color-column', 'value'),
    Input('show_nan', 'value'),
    Input('show_log_x', 'value'),
    Input('show_log_y', 'value'), )
def update_graph(name_of_data_frame, xaxis_column_name, yaxis_column_name,
                 color_column_name, show_nan, show_log_x, show_log_y):
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
    return create_scatter_plot(name_of_data_frame, xaxis_column_name, yaxis_column_name,
                               color_column_name, log_x, log_y, nan)
