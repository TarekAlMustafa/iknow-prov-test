import colorcet as cc
import numpy as np
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output, State
from django.conf import settings
from django_plotly_dash import DjangoDash

from planthub.utils.cat_cont_cols import CAT_COLS

from .format import format_labels, get_cat_name
from .read_data import data_frames, dataframe_options, get_valid_second_column

app = DjangoDash('bar')
app.css.append_css({"external_url": settings.STATIC_URL_PREFIX + "/static/css/dashstyle.css"})


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
        data.index.name = get_cat_name(name_of_data_frame, category, CAT_COLS)
        return px.bar(data, data.index, 'count')
    else:
        data = helper_df.groupby([category, category2]).agg(np.sum).rename(
            columns={'ones': 'count'}).reset_index()

        data.columns = [
            get_cat_name(name_of_data_frame, category, CAT_COLS),
            get_cat_name(name_of_data_frame, category2, CAT_COLS),
            "count"
        ]

        cmap_list = zip(data[get_cat_name(name_of_data_frame, category2, CAT_COLS)].drop_duplicates(), cc.glasbey)
        cmap_dict = {n: ('gray' if n == 'unknown' else k) for n, k in cmap_list}

        return px.bar(
            data,
            x=get_cat_name(name_of_data_frame, category, CAT_COLS),
            y='count',
            color=get_cat_name(name_of_data_frame, category2, CAT_COLS),
            color_discrete_map=cmap_dict
        )


app.layout = html.Div(children=[
    html.H1(children='Bar chart',
            className="header-title"
            ),

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
            "Second category (stacked bar chart)",
            dcc.Dropdown(
                id='cat2',
                # Possible options and value are determined in first callback update_possible_categories
                # instead of being hardcoded
                # options=[{'label': 'None', 'value': 'None'}] + [{'label': i, 'value': i} for i in discrete],
                # value='None',
                searchable=True,
                className="dropdown-list"
            ),
        ],
            className="dropdown"
        ),

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
        )

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

], className="container"
)


# Whenever the chosen dataframe is changed, the possible categories have to be updated
@app.callback(
    Output('cat', 'options'),
    Output('cat', 'value'),
    Input('dataframe', 'value'),
    State('cat', 'value')
)
def update_col(name_of_dataframe, old_value):
    cols = format_labels(name_of_dataframe, CAT_COLS)
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
    cols = format_labels(
        name_of_dataframe,
        CAT_COLS,
        valid_cols=get_valid_second_column(name_of_dataframe, cat)
    )

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
