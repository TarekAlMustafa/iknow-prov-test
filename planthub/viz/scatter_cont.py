import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash

from .read_data import data_frames, continuous_columns, cat_columns, get_valid_second_column, get_valid_third_column, \
    dataframe_options

app = DjangoDash('scatter_cont')


def create_scatter_plot(name_of_data_frame, x, y, color, show_nan=True):
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
    else:
        if show_nan:
            helper_df = df[[x, y, color, 'AccSpeciesName', ]].dropna(subset=[x, y])
        else:
            helper_df = df[[x, y, color, 'AccSpeciesName', ]].dropna()
        kwargs['color'] = color
        kwargs['labels'] = {color: 'colorbar'}
    # Tell the user how many points there are (and whether there were too many/zero...)
    size = len(helper_df)
    kwargs['title'] = f'{size} datapoints: Scatterplot {x} vs. {y}'
    if size > 20000:
        helper_df = helper_df.sample(n=20000)
        kwargs['title'] = f'Too many points to show in a browser. You only see a sample of 20000 out of {size} points'
    if len(helper_df) == 0:
        # This cannot happen thanks to callbacks. But let's be sure
        kwargs['title'] = 'No datapoints for the requested combination of x-axes and y-axes'
    return px.scatter(helper_df, x=x, y=y, hover_name='AccSpeciesName', **kwargs)


app.layout = html.Div(children=[
    html.H1(children='Scatter plot (coloring using continuous quantity)'),
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
            # options=[{'label': i, 'value': i} for i in continuous],
            # value='TRY_Leaf carbon (C) isotope signature (delta 13C)',
        ),
    ]),
    html.Div([
        "y-axis:",
        dcc.Dropdown(
            id='y-axis',
            # options=[{'label': i, 'value': i} for i in continuous],
            # value='TRY_Leaf carbon/nitrogen (C/N) ratio',
        ),
    ]),
    html.Div([
        "color:",
        dcc.Dropdown(
            id='color-column',
            # options will be created by callbacks at runtime instead of being hardcoded
            # options=[{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in continuous],
            value='None',
        ),
    ]),
    html.Div([
        dcc.Checklist(
            id='show_nan',
            options=[
                {'label': "Show plants for which the value of the chosen color-column is not known (will be shown in "
                          "gray)",
                 'value': 'show_nan'},
            ],
            value=[]
        )
    ]),
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

])


@app.callback(
    Output('x-axis', 'options'),
    Output('x-axis', 'value'),
    Input('dataframe', 'value'),
    State('x-axis', 'value')
)
def update_possible_densities(name_of_data_frame, old_value):
    cols = [{'label': i, 'value': i} for i in continuous_columns[name_of_data_frame]]

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
    cols = [{'label': i, 'value': i} for i in get_valid_second_column(name_of_dataframe, x_col) if
            i in continuous_columns[name_of_dataframe]]

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
    cols = [{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for
                                                   i in get_valid_third_column(name_of_dataframe, x_col, y_col) if
                                                   i != 'AccSpeciesName' and i in continuous_columns[name_of_dataframe]]
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
    Input('show_nan', 'value'), )
def update_graph(name_of_data_frame, xaxis_column_name, yaxis_column_name,
                 color_column_name, show_nan):
    if show_nan == []:
        nan = False
    if show_nan == ['show_nan']:
        nan = True
    return create_scatter_plot(name_of_data_frame, xaxis_column_name, yaxis_column_name, color_column_name, nan)
