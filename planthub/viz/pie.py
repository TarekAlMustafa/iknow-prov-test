import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.express as px
import colorcet as cc
from dash.dependencies import Input, Output, State
from .read_data import data_frames, cat_columns, continuous_columns, dataframe_options
from django_plotly_dash import DjangoDash

app = DjangoDash('pie')
app.css.append_css({"external_url": "/static/css/dashstyle.css"})

def create_pie_chart(name_of_data_frame, cat, show_unknown):
    """

    :param name_of_data_frame:
    :param cat: Name of column that should provide the categories whose proportions are shown in the pie plot
    :param show_unknown: Whether to take items of which category is unknown into account
    :return:
    """
    # In theory you could just write one line of code: Tell plotly how to do everything
    # But then it is much too slow, so instead we do the processing using fast
    # libraries such as pandas. That's the reason why we write these thirty lines of code
    df = data_frames[name_of_data_frame]
    # Here we create a condensed datafile that will be plotted later. It contains the name of all
    # categories and how often they occur
    # In order count how often each
    df['ones'] = 1
    if show_unknown:
        data = df[['ones', cat]].groupby(
            cat).agg(np.sum).rename(columns={'ones': 'frequency'})
    else:
        data = df[['ones', cat]].replace('unknown', np.nan) \
            .groupby(cat).agg(np.sum).rename(columns={'ones': 'frequency'})
    data = data.sort_values('frequency', ascending=False)
    # Now we take care in case we have too many categories: We do not want to have more than thirty, otherwise
    # the plot is too crowded
    if len(data) > 30:
        # We collapse all items belonging to rare categories into a new category called 'other'
        # We only want to show categories that make up at least .5% of the whole dataset but more than 5
        data['proportion'] = data['frequency'] / data['frequency'].sum()
        threshold = data.iloc[30]['proportion']
        threshold = max(threshold, .005)
        threshold = min(threshold, data.iloc[5]['proportion'])
        rest_sum = data[data['proportion'] < threshold]['frequency'].sum()
        data = data[~(data['proportion'] < threshold)]
        data.loc['other'] = {'frequency': rest_sum}
        # Make sure we have <200 categories now
        if len(data) > 200:
            data.sort_values('frequency', ascending=False)
            threshold = data.iloc[200]['frequency']
            rest_sum = data[data['proportion'] <= threshold]['frequency'].sum()
            data = data[~(data['proportion'] <= threshold)]
            data.loc['other', 'frequency'] += rest_sum

    # Now we assign a color to each category. 'Unknown' shall be gray. The way I assign the colors is a bit
    # complicated because I want that the colors to be same regardless if we filtered out 'unknown' or not
    temp = 0
    for c in data.index:
        if c == 'unknown':
            data.loc[c, 'color'] = 'gray'
            print(data.loc[c])
        else:
            data.loc[c, 'color'] = cc.glasbey[temp]
            temp += 1
    color_dict = {k: v for (k, v) in zip(data.index, data['color'])}
    return px.pie(data, values='frequency', names=data.index, title='Pie chart', color=data.index,
                  color_discrete_map=color_dict)


app.layout = html.Div(children=[
    html.H1(children='Pie chart', className="header-title"),

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
        "Category",
        dcc.Dropdown(
            id='cat',
            # Possible options and value are determined in first callback update_possible_categories
            # instead of being hardcoded
            # options=[{'label': i, 'value': i} for i in discrete],
            # value='TRY_Growth form 2',
            searchable=True,
            className="dropdown-list"
        ),
    ],
        className="dropdown"),
    html.Div([
        dcc.Checklist(
            id='show_nan',
            options=[
                {'label': "Also take into account unknown (null) values", 'value': 'show_nan'},
            ],
            value=[],
            inputClassName="checklist-input"

        )
    ],
        className="checklist"
    ),
    dcc.Loading(
        dcc.Graph(
            id='bar_chart',
            # Final graph is computed in callbacks
            figure=px.pie().add_annotation(text="Plot is being computed. This can take some seconds.",
                                           showarrow=False, font={"size": 20})
        ),
        debug=True,
        type='default',
    )

], className="container"
)


@app.callback(
    Output('cat', 'options'),
    Output('cat', 'value'),
    Input('dataframe', 'value'),
    State('cat', 'value'),
)
def update_possible_categories(name_of_dataframe, old_value):
    cols = [{'label': i, 'value': i} for i in cat_columns[name_of_dataframe]]
    if old_value in [i['value'] for i in cols]:
        new_value = old_value
    else:
        new_value = cols[-1]['value']
    return cols, new_value


@app.callback(
    Output('bar_chart', 'figure'),
    Input('dataframe', 'value'),
    Input('cat', 'value'),
    Input('show_nan', 'value'),
)
def update_graph(name_of_data_frame, cat, show_nan):
    if show_nan == []:
        nan = False
    else:
        nan = True
    return create_pie_chart(name_of_data_frame, cat, nan)
