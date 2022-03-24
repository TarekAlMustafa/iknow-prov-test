import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
from django.conf import settings

from .read_data import data_frames, continuous_columns, cat_columns, get_valid_second_column, dataframe_options

app = DjangoDash('violin')
app.css.append_css({"external_url": settings.STATIC_URL_PREFIX + "/static/css/dashstyle.css"})

def create_violin(name_of_dataframe, density, category, show_range):
    """Creates a plotly violin_view plot

    :param name_of_dataframe:
    :param density: Name of the column where to create a violin_view
    :param category: Name of the column to use split data into categories: one violin_view plot per category will be plotted (if 'None' data will not be split)

    :param show_range: Only show data within this range. Usefull to cut off outliers
    :return:
    """
    df = data_frames[name_of_dataframe]
    # In order to have a column with no NA's or other unexpected things, we introduce a new columns of 1
    # This enables plotly to count the number of items for the violin plots
    df['ones'] = 1
    if show_range is None:
        show_range = [-np.inf, np.inf]
    if category == 'None':
        helper_df = df[['ones', density]].loc[(df[density] <= show_range[1]) & (df[density] >= show_range[0])]
        return px.violin(helper_df, y=density, box=True, title=f'Showing {len(helper_df)} points')
    else:
        helper_df = df[['ones', density, category, ]].loc[
            (df[density] <= show_range[1]) & (df[density] >= show_range[0])]
        return px.violin(helper_df, x=category, y=density, box=True, title=f'Showing {len(helper_df)} points')


app.layout = html.Div([
    html.H1(children='Violin Plot', className="header-title"),
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
        "Density of:",
        dcc.Dropdown(
            id='density',
            # Possible options and value are determined in first callback update_possible_densities
            # instead of being hardcoded
            # options=[{'label': i, 'value': i} for i in continuous],
            # value='TRY_Leaf carbon (C) isotope signature (delta 13C)',
            searchable=True,
            className="dropdown-list"
        ),
    ],
        className="dropdown"),
    html.Div([
        "Category",
        dcc.Dropdown(
            id='cat',
            # Possible options and value are determined in first callback update_possible_densities
            # instead of being hardcoded
            # options=[{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in discrete],
            # value='None',
            searchable=True,
            className="dropdown-list"
        ),
    ],
        className="dropdown"),
    html.Div([
        "Show only range of",
        dcc.RangeSlider(
            id='show_range',
            allowCross=False,
            tooltip={"placement": "bottom", 'always_visible': True},
            step=.01
        )
    ]),
    dcc.Loading(
        dcc.Graph(
            id='violin_plot',
            # final plot is created in a callback
            figure=px.violin().add_annotation(text="Plot is being computed. This can take some seconds.",
                                              showarrow=False, font={"size": 20})
        ),
        debug=True,
        type='cube',
    )
], className="container"
)


@app.callback(
    Output('show_range', 'value'),
    Output('show_range', 'min'),
    Output('show_range', 'max'),
    Input('dataframe', 'value'),
    Input('density', 'value'),
)
def update_range_slider(name_of_data_frame, density):
    mini = data_frames[name_of_data_frame][density].min()
    maxi = data_frames[name_of_data_frame][density].max()
    return [[mini, maxi], mini, maxi]


@app.callback(
    Output('density', 'options'),
    Output('density', 'value'),
    Input('dataframe', 'value'),
    State('density', 'value'),
)
def update_possible_densities(name_of_dataframe, old_value):
    cols = [{'label': i, 'value': i} for i in continuous_columns[name_of_dataframe]]
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('cat', 'options'),
    Output('cat', 'value'),
    Input('dataframe', 'value'),
    Input('density', 'value'),
    State('cat', 'value'),
)
def update_possible_categories(name_of_dataframe, density, old_value):
    cols = [{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in
                                                   cat_columns[name_of_dataframe] if
                                                   i in get_valid_second_column(name_of_dataframe, density)]
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = 'None'
    return cols, new_value


@app.callback(
    Output('violin_plot', 'figure'),
    Input('dataframe', 'value'),
    Input('density', 'value'),
    Input('cat', 'value'),
    Input('show_range', 'value'),
)
def update_graph(name_of_data_frame, density, cat, show_range):
    return create_violin(name_of_data_frame, density, cat, show_range)
