import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import numpy as np
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash

from .read_data import data_frames, cat_columns, continuous_columns, dataframe_options

app = DjangoDash('histogram')


def create_histogram(name_of_dataframe, x, number_of_bins):
    """

    :param name_of_dataframe:
    :param x: Name of column of which histogram is created
    :param number_of_bins:
    :return:
    """
    # In theory you could just write one line of code: Tell plotly how to do everything
    # But then is much too slow, so instead we do the processing using fast
    # libraries such as pandas. That's the reason why we write these few lines of code
    df = data_frames[name_of_dataframe]
    counts, edges = np.histogram(df[x].dropna(), number_of_bins, )
    # Computing the mean of edges in order to plot a single bar
    # Example: If the bin with 40cm<...<60cm contains 48 plants
    # we plot a bar of height 48 at 50cm.
    edges = 0.5 * (edges[:-1] + edges[1:])

    return px.bar(x=edges, y=counts, labels={'x': x, 'y': 'count'})
    # return px.histogram(df, x=x)


app.layout = html.Div([
    html.H1(children='Histogram'),

    html.Div([
        "Choose dataset:",
        dcc.RadioItems(
            id='dataframe',
            options=dataframe_options,
            value='TRY',
        )
    ]),
    html.Div([
        "x-axis:",
        dcc.Dropdown(
            id='x-axis',
            # Possible options and value are determined in first callback update_possible_densities
            # instead of being hardcoded
            # options=[{'label': i, 'value': i} for i in continuous],
            # value='TRY_Leaf carbon (C) isotope signature (delta 13C)',
        ),
    ]),
    html.Div([
        "Number of bins:",
        dcc.Slider(
            id='bin_nr',
            min=10,
            max=200,
            value=30,
            tooltip={"placement": "bottom", "always_visible": True},
        ),

    ],
    ),
    dcc.Loading(
        dcc.Graph(
            id='histogram_plot',
            # final graph is constructed in callback update_graph
            figure=px.histogram(title="Plot is being computed. This can take some seconds."),
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
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('histogram_plot', 'figure'),
    Input('dataframe', 'value'),
    Input('x-axis', 'value'),
    Input('bin_nr', 'value'),
)
def update_graph(name_of_data_frame, x, bins):
    return create_histogram(name_of_data_frame, x, bins)
