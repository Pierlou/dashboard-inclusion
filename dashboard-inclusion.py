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
import geopandas as gpd
from shapely import wkt
import requests
import json

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

print('Loading services')
services = pd.read_csv(
    # 'services_enrichis_insee.csv',
    'https://demo-static.data.gouv.fr/resources/utils-fichiers-dashboard-inclusion/20230728-131514/services-enrichis-insee.csv',
    dtype=str
)


def convert_to_geometry(string_geom):
    return wkt.loads(string_geom)


print('Loading departements geometry')
# departements = pd.read_csv('./../../geo_utils/departements.csv')
departements = pd.read_csv("https://demo-static.data.gouv.fr/resources/utils-fichiers-dashboard-inclusion/20230728-131001/departements.csv")
departements = departements[['DEP', 'LIBELLE', 'geometry']]
departements = departements.rename({
    'DEP': 'departement',
    'LIBELLE': 'Libellé',
}, axis=1)
departements['geometry'] = departements['geometry'].apply(convert_to_geometry)
departements = gpd.GeoDataFrame(departements, geometry='geometry')
departements.crs = 'EPSG:4326'
# saving geom so that we don't have to recompute it everytime
geom = departements['geometry']
geom.index = departements['departement']
geom = json.loads(geom.to_json())
# dropping in the main df to save space
departements = departements.drop('geometry', axis=1)

# ## Les communes prennent trop de temps à charger et seules 3k d'entre elles ont des services, peu pertinent finalement
# print('Loading communes geometry')
# communes_path = './../../geo_utils/communes-5m.geojson'
# communes = gpd.read_file(communes_path)
# communes = communes[['code', 'nom', 'departement' ,'region', 'epci', 'geometry']]
# communes = communes.loc[~(communes['code'].isin(['75056', '69123', '13055']))]
# communes.loc[~(communes.geometry.is_valid), 'geometry'] = communes.loc[~(communes.geometry.is_valid), 'geometry'].buffer(0)

services_cols = {
    'contact_public': str,
    'cumulable': str,
    'formulaire_en_ligne': str,
    'frais_autres': str,
    'justificatifs': str,
    'lien_source': str,
    'modes_accueil': str,
    'nom': str,
    'presentation_resume': str,
    'presentation_detail': str,
    'prise_rdv': str,
    'profils': str,
    'recurrence': str,
    'source': str,
    'thematiques': str,
    'types': str,
    'pre_requis': str,
    'frais': str,
    '_di_surrogate_id': str,
    '_di_structure_surrogate_id': str,
    'longitude': float,
    'latitude': float,
    'complement_adresse': str,
    'commune': str,
    'adresse': str,
    'code_postal': str,
    'code_insee': str,
    'courriel': str,
    'telephone': str,
}

to_map_cols = {
    'contact_public': bool,
    'cumulable': bool,
    'modes_accueil': list,
    'profils': list,
    'thematiques': list,
    'types': list,
    'frais': list,
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


for c in to_map_cols.keys():
    services[c] = services[c].apply(lambda x: map_cols(to_map_cols[c], x))
no_coord = int(round(sum(services['latitude'].isna())/len(services)*100, 0))
no_dep = int(round(sum(services['departement'].isna())/len(services)*100, 0))


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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
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
                    style={"padding": "0px 0px 20px 0px"},
                )]
            ),
        ]),

        dbc.Row(children=[
            dbc.Col([
                dbc.Button('Rechercher', id='search_button', color='primary'),
                dbc.Tooltip(
                    f"⚠️ {no_coord}% des services n'ont pas de coordonnées géographiques renseignées "
                    f"et {no_dep}% n'ont pas de département ni de commune. "
                    "Les statistiques sont à prendre avec des pincettes. 🤏",
                    target="search_button",
                ),
            ]),
            dbc.Col(id='map_description_col', width={'size': 10}),
        ],
            style={"padding": "0px 0px 20px 0px"},
        ),

        dcc.Tabs(id='tabs', children=[

            dcc.Tab(
                id='find_service_tab',
                label='Trouver un service',
                children=[
                    dbc.Row([
                        dcc.Loading([
                            dcc.Graph(id='result_fig')
                        ],
                            type='circle'
                        )
                    ],
                        style={"padding": "0px 0px 20px 0px"},
                    ),

                    dbc.Row([
                        html.Div(
                            id='map_info_div',
                            children=html.H4('Cliquez sur un service sur la carte pour en savoir plus !')
                        ),
                    ],
                        style={"padding": "0px 0px 20px 0px"},
                    ),
                ],
            ),

            dcc.Tab(
                id='stats_tab',
                label='Statistiques géographiques',
                children=[
                    dbc.Row([
                        dcc.Loading([
                            dcc.Graph(id='stats_fig')
                        ],
                            type='circle'
                        )
                    ],
                        style={"padding": "0px 0px 20px 0px"},
                    ),
                ]
            ),
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
def update_scatter_map(
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
            style={"padding": "5px 0px 5px 0px"},
        )
        for _, row in df.iterrows()
    ]

    return cards


@app.callback(
    Output('map_description_col', 'children'),
    [Input('tabs', 'value')]
)
def change_title(tab_id):
    if tab_id == 'tab-1':
        return [
            html.H4('Cliquez sur un service sur la carte pour en savoir plus en-dessous !')
        ]
    else:
        return [
            html.H4('Survolez la carte pour voir les statistiques !')
        ]


@app.callback(
    Output('stats_fig', 'figure'),
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
def update_chloropleth_map(
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

    echelle_geo = 'departement'
    stats = df.groupby(echelle_geo)['_di_surrogate_id'].count().reset_index()
    stats = pd.merge(
        stats,
        departements,
        on=echelle_geo,
        how='outer'
    )
    stats = stats.sort_values(echelle_geo)
    stats = stats.rename({'_di_surrogate_id': 'nb_services'}, axis=1)
    stats.index = stats[echelle_geo]
    stats['nb_services'] = stats['nb_services'].fillna(0)

    fig = px.choropleth_mapbox(
        stats,
        geojson=geom,
        locations='departement',
        color='nb_services',
        color_continuous_scale='RdYlGn',
        mapbox_style="open-street-map",
        zoom=4,
        center={"lat": 46.5, "lon": 2.77},
        opacity=0.5,
        hover_name='Libellé',
        hover_data=['departement'],
        labels={
            'nb_services': 'Nombre de services',
            'departement': 'Numéro de département'
        },
        title='Nombre de services avec les critères sélectionnés par département',
        height=500
    )
    return fig

# %%


if __name__ == '__main__':
    app.run_server(debug=False, use_reloader=False, port=8051)
