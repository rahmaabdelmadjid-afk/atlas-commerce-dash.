"""Atlas Commerce — tableau de bord décisionnel professionnel.
Dépend de donnees.py et du CSV de votre projet original.
"""
from dash import Dash, dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from donnees import df, filtrer, calculer_kpis, mad

NAVY = '#13243B'
BLUE = '#2563EB'
TEAL = '#0D9488'
COLORS = ['#2563EB', '#0D9488', '#F59E0B', '#8B5CF6', '#EC4899', '#64748B']
DATE_MIN = pd.to_datetime(df['Date']).min().date().isoformat()
DATE_MAX = pd.to_datetime(df['Date']).max().date().isoformat()
CATEGORIES = sorted(str(x) for x in df['Categorie'].dropna().unique())

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title='Atlas Commerce | Business Intelligence')
server = app.server


def kpi(title, ident, icon, subtitle):
    return dbc.Card(dbc.CardBody([
        html.Div([html.Span(icon, className='kpi-icon'), html.Span(title, className='kpi-label')], className='kpi-heading'),
        html.Div('—', id=ident, className='kpi-value'),
        html.Div(subtitle, className='kpi-subtitle')
    ]), className='kpi-card h-100')


def panel(title, ident, subtitle=None):
    return dbc.Card([
        dbc.CardHeader([html.H3(title, className='panel-title'), html.P(subtitle, className='panel-subtitle') if subtitle else None]),
        dbc.CardBody(dcc.Loading(dcc.Graph(id=ident, config={'displaylogo': False, 'responsive': True}, style={'height': '350px'})))
    ], className='chart-card h-100')


def style_chart(fig, height=350):
    fig.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif', color='#475569', size=12),
        margin=dict(l=12, r=12, t=22, b=28), height=height,
        hoverlabel=dict(bgcolor='white', font_size=12),
        legend=dict(orientation='h', y=-0.2, x=0)
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor='#E2E8F0')
    fig.update_yaxes(gridcolor='#EDF2F7', zeroline=False)
    return fig


def empty_chart():
    fig = go.Figure()
    fig.add_annotation(text='Aucune donnée pour les filtres sélectionnés', x=.5, y=.5,
                       xref='paper', yref='paper', showarrow=False, font=dict(size=15, color='#64748B'))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_chart(fig)


def filtered(debut, fin, categorie):
    # Copie pour ne jamais modifier le DataFrame global utilisé par les autres callbacks.
    return filtrer(debut, fin, categorie).copy()


def bar_fig(data, dimension, metric, horizontal=False, color=BLUE):
    if data.empty:
        return empty_chart()
    if horizontal:
        data = data.sort_values(metric)
        fig = px.bar(data, x=metric, y=dimension, orientation='h', text=metric)
        fig.update_yaxes(title=None, automargin=True)
        fig.update_xaxes(title='MAD', tickformat=',.0f')
    else:
        fig = px.bar(data, x=dimension, y=metric, text=metric)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title='MAD', tickformat=',.0f')
    fig.update_traces(marker_color=color, marker_line_width=0,
                      texttemplate='%{text:,.0f}', textposition='outside', cliponaxis=False,
                      hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>' if not horizontal else '%{y}<br>%{x:,.0f} MAD<extra></extra>')
    return style_chart(fig)


app.layout = dbc.Container([
    html.Header(dbc.Row([
        dbc.Col([html.Div('AC', className='brand-icon'), html.Div([
            html.H1('ATLAS COMMERCE', className='brand-name'),
            html.Div('BUSINESS INTELLIGENCE  /  ANALYSE DES VENTES', className='brand-subtitle')
        ])], className='brand-wrap', xs=12, md=8),
        dbc.Col([html.Div('●  DONNÉES HISTORIQUES', className='header-pill'),
                 html.Div('Tableau de bord décisionnel', className='header-note')],
                xs=12, md=4, className='header-right')
    ], align='center'), className='hero'),

    html.Div([
        html.Div([html.Div('Vue d’ensemble', className='section-eyebrow'),
                  html.H2('Performance commerciale', className='page-title'),
                  html.P('Suivez les ventes, la rentabilité commerciale et les produits les plus performants.', className='page-subtitle')]),
        dbc.Button('↺  Réinitialiser les filtres', id='reset-all', color='light', className='reset-all')
    ], className='intro-row'),

    dbc.Card(dbc.CardBody([
        html.Div('FILTRES D’ANALYSE', className='filters-title'),
        dbc.Row([
            dbc.Col([html.Label('Période', className='field-label'),
                     dcc.DatePickerRange(id='dates', start_date=DATE_MIN, end_date=DATE_MAX,
                                         min_date_allowed=DATE_MIN, max_date_allowed=DATE_MAX,
                                         display_format='DD/MM/YYYY', className='date-control')], xs=12, lg=5),
            dbc.Col([html.Label('Catégorie', className='field-label'),
                     dcc.Dropdown(id='categorie', options=[{'label': 'Toutes les catégories', 'value': 'Toutes'}] +
                                  [{'label': c, 'value': c} for c in CATEGORIES], value='Toutes', clearable=False)], xs=12, md=6, lg=4),
            dbc.Col([html.Label('Granularité', className='field-label'),
                     dbc.RadioItems(id='freq', options=[{'label': 'Jour', 'value': 'J'}, {'label': 'Mois', 'value': 'M'}],
                                    value='M', inline=True, className='freq-options')], xs=12, md=6, lg=3)
        ], className='g-3 align-items-end')
    ]), className='filters-card mb-4'),

    dbc.Row([
        dbc.Col(kpi('Chiffre d’affaires', 'ca', '↗', 'Total des ventes filtrées'), xs=12, sm=6, xl=3),
        dbc.Col(kpi('Commandes distinctes', 'commandes', '▤', 'Nombre de commandes uniques'), xs=12, sm=6, xl=3),
        dbc.Col(kpi('Panier moyen', 'panier', '◈', 'CA par commande'), xs=12, sm=6, xl=3),
        dbc.Col(kpi('Marge commerciale', 'marge', '◉', 'Somme des marges commerciales'), xs=12, sm=6, xl=3)
    ], className='g-3 mb-3'),
    html.Div(id='etat', className='data-note mb-4'),

    dbc.Row([dbc.Col(panel('Évolution du chiffre d’affaires', 'evolution', 'Tendance des ventes sur la période sélectionnée'), xs=12, lg=8),
             dbc.Col(panel('Répartition par région', 'regions', 'Cliquez sur une région pour filtrer le Top 10'), xs=12, lg=4)], className='g-4 mb-4'),
    dbc.Row([dbc.Col(panel('Chiffre d’affaires par catégorie', 'categories', 'Comparaison des catégories de produits'), xs=12, lg=6),
             dbc.Col(panel('Marge commerciale par catégorie', 'marges', 'Contribution de chaque catégorie à la marge'), xs=12, lg=6)], className='g-4 mb-4'),
    dbc.Row([dbc.Col([
        panel('Top 10 des produits', 'top-produits', 'Produits classés selon leur chiffre d’affaires'),
        html.Div([html.Span(id='region-label'), dbc.Button('Effacer la région', id='reset-region', outline=True, color='primary', size='sm')], className='region-control')
    ], xs=12, lg=8),
    dbc.Col(dbc.Card([dbc.CardHeader(html.H3('Lecture métier', className='panel-title')),
                      dbc.CardBody([html.Div('POINTS CLÉS', className='section-eyebrow'),
                                    html.Div(id='lecture-metier', className='insight-text'),
                                    html.Hr(), html.P('Les résultats dépendent des filtres actifs et ne sont pas des données en temps réel.', className='disclaimer')])],
                     className='chart-card insight-card h-100'), xs=12, lg=4)], className='g-4 mb-4'),
    dcc.Store(id='region-active', data=None),
    html.Footer('ATLAS COMMERCE  •  Dashboard analytique  •  Données fictives', className='footer')
], fluid=True, className='dashboard-shell')


@app.callback(Output('ca', 'children'), Output('commandes', 'children'),
              Output('panier', 'children'), Output('marge', 'children'), Output('etat', 'children'),
              Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'))
def update_kpis(debut, fin, categorie):
    ventes = filtered(debut, fin, categorie)
    k = calculer_kpis(ventes)
    return mad(k['ca']), f"{k['commandes']:,}".replace(',', ' '), mad(k['panier']), mad(k['marge']), f"{len(ventes):,}".replace(',', ' ') + ' lignes analysées  •  Indicateurs mis à jour selon les filtres'


@app.callback(Output('evolution', 'figure'), Input('dates', 'start_date'), Input('dates', 'end_date'),
              Input('categorie', 'value'), Input('freq', 'value'))
def update_evolution(debut, fin, categorie, freq):
    ventes = filtered(debut, fin, categorie)
    if ventes.empty:
        return empty_chart()
    ventes['Periode'] = pd.to_datetime(ventes['Date']).dt.to_period('M').dt.to_timestamp() if freq == 'M' else pd.to_datetime(ventes['Date']).dt.normalize()
    agg = ventes.groupby('Periode', as_index=False)['Chiffre_Affaires'].sum().sort_values('Periode')
    fig = px.area(agg, x='Periode', y='Chiffre_Affaires', markers=True)
    fig.update_traces(line=dict(color=BLUE, width=3), fillcolor='rgba(37,99,235,.10)', marker=dict(size=6),
                      hovertemplate='%{x|%d/%m/%Y}<br>%{y:,.0f} MAD<extra></extra>')
    fig.update_xaxes(title=None)
    fig.update_yaxes(title='CA (MAD)', tickformat=',.0f')
    return style_chart(fig)


@app.callback(Output('categories', 'figure'), Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'))
def update_categories(debut, fin, categorie):
    ventes = filtered(debut, fin, categorie)
    agg = ventes.groupby('Categorie', as_index=False)['Chiffre_Affaires'].sum().sort_values('Chiffre_Affaires', ascending=False)
    return bar_fig(agg, 'Categorie', 'Chiffre_Affaires')


@app.callback(Output('regions', 'figure'), Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'))
def update_regions(debut, fin, categorie):
    ventes = filtered(debut, fin, categorie)
    agg = ventes.groupby('Region', dropna=False, as_index=False)['Chiffre_Affaires'].sum()
    agg['Region'] = agg['Region'].fillna('Non renseignée').astype(str)
    if agg.empty or agg['Chiffre_Affaires'].clip(lower=0).sum() <= 0:
        return empty_chart()
    # Une répartition en pourcentage exige des valeurs non négatives.
    agg['CA_positif'] = agg['Chiffre_Affaires'].clip(lower=0)
    fig = px.pie(agg, names='Region', values='CA_positif', hole=.68, color_discrete_sequence=COLORS)
    fig.update_traces(textposition='outside', textinfo='percent', hovertemplate='%{label}<br>%{value:,.0f} MAD<br>%{percent}<extra></extra>')
    fig.update_layout(showlegend=True, legend=dict(orientation='h', y=-.18, x=0), margin=dict(l=10, r=10, t=22, b=45))
    return style_chart(fig)


@app.callback(Output('marges', 'figure'), Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'))
def update_marges(debut, fin, categorie):
    ventes = filtered(debut, fin, categorie)
    agg = ventes.groupby('Categorie', as_index=False)['Marge'].sum().sort_values('Marge', ascending=False)
    return bar_fig(agg, 'Categorie', 'Marge', color=TEAL)


@app.callback(Output('top-produits', 'figure'), Output('region-label', 'children'),
              Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'), Input('region-active', 'data'))
def update_top(debut, fin, categorie, region):
    ventes = filtered(debut, fin, categorie)
    if region:
        ventes = ventes[ventes['Region'].fillna('Non renseignée') == region].copy()
    agg = ventes.groupby('Produit', as_index=False)['Chiffre_Affaires'].sum().nlargest(10, 'Chiffre_Affaires')
    return bar_fig(agg, 'Produit', 'Chiffre_Affaires', horizontal=True), f"Région sélectionnée : {region or 'Toutes les régions'}"


@app.callback(Output('region-active', 'data'), Input('regions', 'clickData'), Input('reset-region', 'n_clicks'),
              Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'), prevent_initial_call=True)
def select_region(click, _reset, _start, _end, _category):
    if ctx.triggered_id == 'regions' and click and click.get('points'):
        return click['points'][0].get('label')
    return None


@app.callback(Output('dates', 'start_date'), Output('dates', 'end_date'), Output('categorie', 'value'), Output('freq', 'value'),
              Input('reset-all', 'n_clicks'), prevent_initial_call=True)
def reset_filters(_):
    return DATE_MIN, DATE_MAX, 'Toutes', 'M'


@app.callback(Output('lecture-metier', 'children'), Input('dates', 'start_date'), Input('dates', 'end_date'), Input('categorie', 'value'))
def business_insight(debut, fin, categorie):
    ventes = filtered(debut, fin, categorie)
    if ventes.empty:
        return html.P('Aucune vente sur cette sélection. Essayez une période ou une catégorie différente.')
    regions = ventes.groupby('Region')['Chiffre_Affaires'].sum()
    categories = ventes.groupby('Categorie')['Marge'].sum()
    insights = []
    if not regions.empty:
        insights.append(html.P([html.Strong('Région leader : '), str(regions.idxmax()), ' (CA le plus élevé).']))
    if not categories.empty:
        insights.append(html.P([html.Strong('Catégorie la plus contributrice : '), str(categories.idxmax()), ' (marge totale la plus élevée).']))
    insights.append(html.P('Comparez les catégories et les régions avant de définir vos priorités commerciales.'))
    return insights


if __name__ == '__main__':
    app.run(debug=True)
