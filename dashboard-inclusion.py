from ast import literal_eval
import os

import dash
# from dash import dash_table
from dash import dcc
from dash import html
# import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

services_cols = [
    'contact_public',
    'cumulable',
    'formulaire_en_ligne',
    'frais_autres',
    'justificatifs',
    'lien_source',
    'modes_accueil',
    'nom',
    'presentation_resume',
    'presentation_detail',
    'prise_rdv',
    'profils',
    'recurrence',
    'source',
    'thematiques',
    'types',
    'pre_requis',
    'frais',
    '_di_surrogate_id',
    '_di_structure_surrogate_id',
    'longitude',
    'latitude',
    'complement_adresse',
    'commune',
    'adresse',
    'code_postal',
    'code_insee',
    'courriel',
    'telephone',
]

to_map_cols = {
    'contact_public': bool,
    'cumulable': bool,
    'modes_accueil': list,
    'profils': list,
    'thematiques': list,
    'types': list,
    'frais': list,
    'longitude': float,
    'latitude': float,
}


def map_cols(new_type, value):
    if new_type == bool:
        if value == "True":
            return True
        return False
    elif new_type == list:
        try:
            return literal_eval(value)
        except:
            return []
    elif new_type == float:
        return float(value)


services = pd.read_csv(
    'services-inclusion-2023-07-10.csv',
    usecols=services_cols,
    dtype=str
)

for c in to_map_cols.keys():
    services[c] = services[c].apply(lambda x: map_cols(to_map_cols[c], x))

services['full_adresse'] = services.apply(
    lambda d: ' '.join([d['adresse'].title(), d['code_postal'], d['commune'].title()])
    if all([isinstance(c, str) for c in [d['adresse'], d['code_postal'], d['commune']]])
    else '',
    axis=1
)


def build_args(col_name):
    as_text = col_name.replace('_', ' ')
    if to_map_cols[col_name] == list:
        rows = services[col_name].values
        values = set()
        for r in rows:
            values = values | set(r)
        values = list(values)
        labels = [s.replace('-', ' ').capitalize() for s in values]
        options = [
                {'label': l, 'value': v} for (l, v) in zip(labels, values)
        ]
    if to_map_cols[col_name] == bool:
        options = [
            {'label': 'Oui', 'value': True},
            {'label': 'Non', 'value': False},
        ]
    return col_name, as_text, options


base_url_adresse = 'https://api-adresse.data.gouv.fr/search/'


# %% APP LAYOUT:
app.layout = dbc.Container(
    [
        dbc.Row([
            html.H3("Services d'insertion en France",
                    style={
                        "padding": "5px 0px 10px 0px",  # "padding": "top right down left"
                    }),
        ]),

        dcc.Tabs([

            dcc.Tab(label='Trouver un service', children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Row([
                            html.H5('Profils recherchés'),
                            dcc.Dropdown(
                                id='profils_dropdown',
                                placeholder="Quels types de profils recherchez-vous ?",
                                searchable=True,
                                multi=True,
                                options=build_args('profils')[2],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                    dbc.Col([
                        dbc.Row([
                            html.H5('Thématiques recherchées'),
                            dcc.Dropdown(
                                id='thematiques_dropdown',
                                placeholder="Quelles thématiques recherchez-vous ?",
                                searchable=True,
                                multi=True,
                                options=build_args('thematiques')[2],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Row([
                            html.H5('Types de services'),
                            dcc.Dropdown(
                                id='types_dropdown',
                                placeholder="Quels types de services recherchez-vous ?",
                                searchable=True,
                                multi=True,
                                options=build_args('types')[2],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                    dbc.Col([
                        dbc.Row([
                            html.H5('Frais à engager'),
                            dcc.Dropdown(
                                id='frais_dropdown',
                                placeholder="Quels types de frais recherchez-vous ?",
                                searchable=True,
                                multi=True,
                                options=build_args('frais')[2],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Row([
                            html.H5("Mode d'accueil"),
                            dcc.Dropdown(
                                id='modes_accueil_dropdown',
                                placeholder="Quel mode d'accueil recherchez-vous ?",
                                searchable=True,
                                multi=False,
                                options=build_args('modes_accueil')[2],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                    dbc.Col([
                        dbc.Row([
                            html.H5('Avec contact public'),
                            dcc.Dropdown(
                                id='contact_public_dropdown',
                                placeholder="Souhaitez-vous un contact public ?",
                                searchable=True,
                                multi=False,
                                options=[
                                    {'label': 'Oui', 'value': True},
                                    {'label': 'Non', 'value': False},
                                ],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                    dbc.Col([
                        dbc.Row([
                            html.H5('Cumulable'),
                            dcc.Dropdown(
                                id='cumulable_dropdown',
                                placeholder="Souhaitez-vous un service cumulable ?",
                                searchable=True,
                                multi=False,
                                options=[
                                    {'label': 'Oui', 'value': True},
                                    {'label': 'Non', 'value': False},
                                ],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                    dbc.Col([
                        dbc.Row([
                            html.H5('Commune'),
                            dcc.Dropdown(
                                id='commune_dropdown',
                                placeholder="Entrer un nom de commune.",
                                searchable=True,
                                multi=False,
                                options=[],
                            )
                        ],
                            style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                        )]
                    ),
                ]),

                dbc.Row(children=[
                    dbc.Col([
                        dbc.Button('Rechercher', id='search_button', color='primary'),
                    ]),
                    dbc.Col([
                        html.H4('Cliquez sur un service sur la carte pour en savoir plus !')
                    ],
                        width={'size': 10},
                    ),
                ],
                    style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                ),

                dbc.Row([
                    dcc.Graph(id='result_fig')
                ],
                    style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                ),

                dbc.Row([
                    html.Div(
                        id='map_info_div',
                        children=html.H4('Cliquez sur un service sur la carte pour en savoir plus !')
                    ),
                ],
                    style={"padding": "0px 0px 20px 0px"},  # "padding": "top right down left"
                ),
            ]),

            dcc.Tab(label='Statistiques', children=[
                
            ]),
        ])
    ])

# %% Callbacks


@app.callback(
    Output('commune_dropdown', 'options'),
    [Input('commune_dropdown', 'search_value')]
)
def suggest_communes(value):
    if not value or len(value) < 4:
        raise PreventUpdate
    r = requests.get(base_url_adresse + f'?q={value}').json()['features']
    suggestions = [
        {'label': f['properties']['label'], 'value': f['geometry']['coordinates']}
        for f in r
    ]
    return suggestions


@app.callback(
    Output('result_fig', 'figure'),
    [Input('search_button', 'n_clicks')],
    [
        State('profils_dropdown', 'value'),
        State('thematiques_dropdown', 'value'),
        State('types_dropdown', 'value'),
        State('frais_dropdown', 'value'),
        State('modes_accueil_dropdown', 'value'),
        State('contact_public_dropdown', 'value'),
        State('cumulable_dropdown', 'value'),
        State('commune_dropdown', 'value'),
    ]
)
def update_map(
    click,
    profils,
    thematiques,
    types,
    frais,
    modes_accueil,
    contact_public,
    cumulable,
    coord
):
    df = services.copy()
    if isinstance(contact_public, bool):
        df = df.loc[df['contact_public'] == contact_public]

    if isinstance(cumulable, bool):
        df = df.loc[df['cumulable'] == cumulable]

    if isinstance(modes_accueil, str):
        modes_accueil = [modes_accueil]
    if isinstance(modes_accueil, list) and len(modes_accueil) > 0:
        df = df.loc[df['modes_accueil'].apply(lambda l: any([k in l for k in modes_accueil]))]

    if isinstance(profils, str):
        profils = [profils]
    if isinstance(profils, list) and len(profils) > 0:
        df = df.loc[df['profils'].apply(lambda l: any([k in l for k in profils]))]

    if isinstance(thematiques, str):
        thematiques = [thematiques]
    if isinstance(thematiques, list) and len(thematiques) > 0:
        df = df.loc[df['thematiques'].apply(lambda l: any([k in l for k in thematiques]))]

    if isinstance(types, str):
        types = [types]
    if isinstance(types, list) and len(types) > 0:
        df = df.loc[df['types'].apply(lambda l: any([k in l for k in types]))]

    if isinstance(frais, str):
        frais = [frais]
    if isinstance(frais, list) and len(frais) > 0:
        df = df.loc[df['frais'].apply(lambda l: any([k in l for k in frais]))]

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        labels={
            k: k.replace('_', ' ').capitalize() for k in services_cols
        },
        hover_name="nom",
        hover_data=["full_adresse"],
        # custom_data=[],
        # size='',
        # color='modes_accueil',
        # color_continuous_scale=["red", "yellow", "green"],
        center={'lat': 46.3936, 'lon': 3.1875} if not coord else {'lat': coord[1], 'lon': coord[0]},
        zoom=5 if not coord else 13,
        height=600
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


@app.callback(
    Output('map_info_div', 'children'),
    [Input('result_fig', 'clickData')],
    [
        State('profils_dropdown', 'value'),
        State('thematiques_dropdown', 'value'),
        State('types_dropdown', 'value'),
        State('frais_dropdown', 'value'),
        State('modes_accueil_dropdown', 'value'),
        State('contact_public_dropdown', 'value'),
        State('cumulable_dropdown', 'value'),
    ]
)
def display_info(
    value,
    profils,
    thematiques,
    types,
    frais,
    modes_accueil,
    contact_public,
    cumulable,
):
    if not value:
        raise PreventUpdate
    full_adresse = value['points'][0]['customdata'][0]

    df = services.copy()
    df = df.loc[df['full_adresse'] == full_adresse]

    if isinstance(contact_public, bool):
        df = df.loc[df['contact_public'] == contact_public]

    if isinstance(cumulable, bool):
        df = df.loc[df['cumulable'] == cumulable]

    if isinstance(modes_accueil, str):
        modes_accueil = [modes_accueil]
    if isinstance(modes_accueil, list) and len(modes_accueil) > 0:
        df = df.loc[df['modes_accueil'].apply(lambda l: any([k in l for k in modes_accueil]))]

    if isinstance(profils, str):
        profils = [profils]
    if isinstance(profils, list) and len(profils) > 0:
        df = df.loc[df['profils'].apply(lambda l: any([k in l for k in profils]))]

    if isinstance(thematiques, str):
        thematiques = [thematiques]
    if isinstance(thematiques, list) and len(thematiques) > 0:
        df = df.loc[df['thematiques'].apply(lambda l: any([k in l for k in thematiques]))]

    if isinstance(types, str):
        types = [types]
    if isinstance(types, list) and len(types) > 0:
        df = df.loc[df['types'].apply(lambda l: any([k in l for k in types]))]

    if isinstance(frais, str):
        frais = [frais]
    if isinstance(frais, list) and len(frais) > 0:
        df = df.loc[df['frais'].apply(lambda l: any([k in l for k in frais]))]

    cards = [
        dbc.Row([
            dbc.Card([
                dbc.CardHeader(
                    "Lien vers la page dédiée : " + row['lien_source']
                    if row['lien_source'] and isinstance(row['lien_source'], str)
                    else ""
                ),
                dbc.CardBody(
                    [
                        html.H4(row['nom'].capitalize(), className="card-title"),
                        html.P(row['presentation_detail'], className="card-text"),
                        html.H6("Publics cibles", className="card-text"),
                        html.P(
                            '\n'.join([f"- {p.replace('-', ' ').capitalize()}" for p in row['profils']]),
                            className="card-text",
                            style={"whiteSpace": "pre-line"}
                        )
                        if row['profils'] else "NC",
                        html.H6("Thématiques abordées", className="card-text"),
                        html.P(
                            '\n'.join([f"- {t.replace('-', ' ').capitalize()}" for t in row['thematiques']]),
                            className="card-text",
                            style={"whiteSpace": "pre-line"}
                        )
                        if row['thematiques'] else "NC",
                    ]
                ),
                dbc.CardFooter(row['full_adresse']),
            ],
                color="primary",
                outline=True,
            ),
        ],
            style={"padding": "5px 0px 5px 0px"},  # "padding": "top right down left"
        )
        for _, row in df.iterrows()
    ]

    return cards

# %%


if __name__ == '__main__':
    app.run_server(debug=False, use_reloader=False, port=8051)
