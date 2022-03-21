import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.express as px
import colorcet as cc
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash

from .read_data import data_frames, continuous_columns, cat_columns, dataframe_options, get_valid_second_column

app = DjangoDash('bar')

colors = {
    'background': '#111111',
    'text': 'rgba(0, 0, 0, .7)'
}


def create_bar_chart(name_of_data_frame, category='TRY_Growth form 2', category2='None', show_nan=True
                     ):
    df = data_frames[name_of_data_frame]
    # In order to count the number of items we have, we introduce a new columns of 1
    df['ones'] = 1

    # We first collect the data we want to display
    if show_nan:
        if category2 == 'None':
            helper_df = df[['ones', category]]
        else:
            helper_df = df[['ones', category, category2]]
    else:
        if category2 == 'None':
            helper_df = df[['ones', category]].replace('unknown', np.nan)
        else:
            helper_df = df[['ones', category, category2]].replace('unknown', np.nan)
    if category2 == 'None':
        data = helper_df.groupby(category).agg(np.sum).rename(columns={'ones': 'count'})
        return px.bar(data, data.index, 'count')
    else:
        data = helper_df.groupby([category, category2]).agg(np.sum).rename(
            columns={'ones': 'count'}).reset_index()
        cmap_list = zip(data[category2].drop_duplicates(), cc.glasbey)
        cmap_dict = {n: ('gray' if n == 'unknown' else k) for n, k in cmap_list}
        return px.bar(data, x=category, y='count', color=category2, color_discrete_map=cmap_dict)


app.layout = html.Div(children=[
    html.H1(children='Bar chart',
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'font-weight': '400',
            'font-familiy': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;',
        }   
    ),

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
            "Category",
            dcc.Dropdown(
                id='cat',
                # Possible options and value are determined in first callback update_possible_categories
                # instead of being hardcoded
                # options=[{'label': i, 'value': i} for i in discrete],
                # value='TRY_Growth form 2',
            ),
        ]),
        html.Div([
            "Second category",
            dcc.Dropdown(
                id='cat2',
                # Possible options and value are determined in first callback update_possible_categories
                # instead of being hardcoded
                # options=[{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in discrete],
                # value='None',
            ),
        ]),

        html.Div([
            dcc.Checklist(
                id='show_nan',
                options=[
                    {'label': "Also take into account those plants where the category is unknown", 'value': 'show_nan'},
                ],
                value=[]
            )
        ])

    ], ),
    dcc.Loading(
        dcc.Graph(
            id='bar_chart',
            # final plot is created in a callback
            figure=px.scatter().add_annotation(text="Plot is being computed. This can take some seconds.",
                                               showarrow=False, font={"size": 20})
        ),
        debug=True,
        type='cube',
    )

])


# Whenever the chosen dataframe is changed, the possible categories have to be updated
@app.callback(
    Output('cat', 'options'),
    Output('cat', 'value'),
    Input('dataframe', 'value'),
    State('cat', 'value')
)
def update_col(name_of_dataframe, old_value):
    cols = [{'label': i, 'value': i} for i in cat_columns[name_of_dataframe]]
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('cat2', 'options'),
    Output('cat2', 'value'),
    Input('dataframe', 'value'),
    Input('cat', 'value'),
    State('cat2', 'value'),
)
def update_second_col(name_of_dataframe, cat, old_value):
    cols = [{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in cat_columns[name_of_dataframe] if
                                                   i in get_valid_second_column(name_of_dataframe, cat)]
    # In case the original second is still allowed, we keep it, else we do not use any color
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = 'None'
    return cols, new_value


# Whenever a new category is chosen, a new plot has to be drawn
@app.callback(
    Output('bar_chart', 'figure'),
    Input('dataframe', 'value'),
    Input('cat', 'value'),
    Input('cat2', 'value'),
    Input('show_nan', 'value'), )
def update_graph(name_of_data_frame, cat, cat2, show_nan):
    if show_nan == []:
        nan = False
    if show_nan == ['show_nan']:
        nan = True
    return create_bar_chart(name_of_data_frame, cat, cat2, nan)
