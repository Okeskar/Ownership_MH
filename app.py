import dash
from dash import html, dcc, Input, Output, State
import dash_leaflet as dl
import pandas as pd
import geopandas as gpd
import json
import os
import logging
from shapely.geometry import Polygon, MultiPolygon

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load Excel data
def load_excel_data():
    folder_path = "data"
    all_dataframes = []
    for file in os.listdir(folder_path):
        if file.endswith(".xlsx"):
            df = pd.read_excel(os.path.join(folder_path, file))
            if 'Taluka' in df.columns:
                df.rename(columns={'Taluka': 'Tehsil'}, inplace=True)
            if 'Plot_No' in df.columns or 'PlotNo' in df.columns:
                df.rename(columns={'Plot_No': 'Plot No.', 'PlotNo': 'Plot No.'}, inplace=True)
            all_dataframes.append(df)
    if all_dataframes:
        df = pd.concat(all_dataframes, ignore_index=True)
        df['Plot No.'] = df['Plot No.'].astype(str).str.strip()
        logger.info(f"Excel data loaded with {len(df)} rows. Columns: {df.columns.tolist()}")
        return df
    logger.error("No Excel files found in data folder")
    return pd.DataFrame()

df = load_excel_data()

# Load GeoJSON
def load_geojson(tehsil):
    geojson_file = f"geojson/{tehsil}.geojson"
    logger.debug(f"Checking GeoJSON file: {geojson_file}")
    if not os.path.exists(geojson_file):
        logger.error(f"GeoJSON file not found: {geojson_file}")
        return None
    try:
        gdf = gpd.read_file(geojson_file)
        logger.info(f"Loaded GeoJSON with {len(gdf)} features. CRS: {gdf.crs}")
        gdf = gdf[gdf.geometry.notnull() & gdf.geometry.is_valid]

        if gdf.crs != "EPSG:4326":
            logger.info("Reprojecting to EPSG:4326")
            gdf = gdf.to_crs(epsg=4326)

        if 'Taluka' in gdf.columns:
            gdf.rename(columns={'Taluka': 'Tehsil'}, inplace=True)
        if 'Plot_No' in gdf.columns or 'PlotNo' in gdf.columns:
            gdf.rename(columns={'Plot_No': 'Plot No.', 'PlotNo': 'Plot No.'}, inplace=True)
        gdf['Plot No.'] = gdf['Plot No.'].astype(str).str.strip()

        return gdf
    except Exception as e:
        logger.error(f"Error loading GeoJSON {geojson_file}: {str(e)}")
        return None

# Initialize Dash
app = dash.Dash(__name__)
app.title = "Khasra Dashboard"

# Layout
app.layout = html.Div([
    html.H2("Khasra Ownership Map Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.Div([
        html.Div([
            html.Label("Select District", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='district-dropdown',
                options=[{'label': dist, 'value': dist} for dist in sorted(df['District'].dropna().unique())],
                placeholder="Select District",
                style={'marginBottom': '10px'}
            ),
            html.Label("Select Taluka", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='tehsil-dropdown', placeholder="Select Taluka", style={'marginBottom': '10px'}),
            html.Label("Select Village", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='village-dropdown', placeholder="Select Village", style={'marginBottom': '10px'}),
            html.Label("Select Plot No.", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='plotno-dropdown', placeholder="Select Plot No.", style={'marginBottom': '10px'}),

            html.Button("Show Khasra", id='show-khasra-button', n_clicks=0, style={
                'width': '100%', 'padding': '10px', 'backgroundColor': '#2c3e50', 'color': 'white',
                'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'marginBottom': '10px'
            }),

            html.Button("Show Ownership", id='show-ownership-button', n_clicks=0, style={
                'width': '100%', 'padding': '10px', 'backgroundColor': '#27ae60', 'color': 'white',
                'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'marginBottom': '10px'
            }),

            html.Hr(),
            html.H4("Plot Information", style={'color': '#2c3e50'}),
            html.Div(id='plot-info', style={
                'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px',
                'minHeight': '100px', 'whiteSpace': 'pre-line'
            })
        ], style={'width': '30%', 'padding': '20px', 'backgroundColor': '#f5f5f5', 'borderRadius': '5px'}),

        html.Div([
            dl.Map(id='map', center=[17.123, 75.644], zoom=16, children=[
                dl.TileLayer(
                    url="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                    attribution="© Google Maps",
                    subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
                    maxZoom=20
                ),
                dl.LayerGroup(id='geojson-layer')
            ], style={'width': '100%', 'height': '600px', 'borderRadius': '5px'})
        ], style={'width': '70%', 'padding': '20px'})
    ], style={'display': 'flex', 'gap': '20px'})
], style={'padding': '20px', 'maxWidth': '1200px', 'margin': 'auto'})

# Callbacks for dropdowns
@app.callback(Output('tehsil-dropdown', 'options'), Input('district-dropdown', 'value'))
def update_tehsils(district):
    if not district:
        return []
    return [{'label': t, 'value': t} for t in sorted(df[df['District'] == district]['Tehsil'].dropna().unique())]

@app.callback(
    Output('village-dropdown', 'options'),
    [Input('district-dropdown', 'value'), Input('tehsil-dropdown', 'value')]
)
def update_villages(district, tehsil):
    if not (district and tehsil):
        return []
    dff = df[(df['District'] == district) & (df['Tehsil'] == tehsil)]
    return [{'label': v, 'value': v} for v in sorted(dff['Village'].dropna().unique())]

@app.callback(
    Output('plotno-dropdown', 'options'),
    [Input('district-dropdown', 'value'), Input('tehsil-dropdown', 'value'), Input('village-dropdown', 'value')]
)
def update_plotnos(district, tehsil, village):
    if not (district and tehsil and village):
        return []
    dff = df[(df['District'] == district) & (df['Tehsil'] == tehsil) & (df['Village'] == village)]
    return [{'label': p, 'value': p} for p in sorted(dff['Plot No.'].dropna())]

# Show Ownership button: Only show plot info
@app.callback(
    Output('plot-info', 'children'),
    Input('show-ownership-button', 'n_clicks'),
    State('district-dropdown', 'value'),
    State('tehsil-dropdown', 'value'),
    State('village-dropdown', 'value'),
    State('plotno-dropdown', 'value')
)
def show_ownership_info(n_clicks, district, tehsil, village, plotno):
    if not n_clicks or not all([district, tehsil, village, plotno]):
        return "Please select all options."
    row = df[(
        df['District'].str.strip().str.lower() == str(district).strip().lower()) &
        (df['Tehsil'].str.strip().str.lower() == str(tehsil).strip().lower()) &
        (df['Village'].str.strip().str.lower() == str(village).strip().lower()) &
        (df['Plot No.'] == str(plotno).strip())
    ]
    if not row.empty and 'Plot Info' in row.columns and not pd.isna(row['Plot Info'].values[0]):
        return row['Plot Info'].values[0]
    return "No ownership information available."

# Show Khasra button: Plot + Adjacent Polygons
@app.callback(
    [Output('geojson-layer', 'children'), Output('map', 'center')],
    Input('show-khasra-button', 'n_clicks'),
    State('district-dropdown', 'value'),
    State('tehsil-dropdown', 'value'),
    State('village-dropdown', 'value'),
    State('plotno-dropdown', 'value')
)
def update_map_with_adjacent_polygons(n_clicks, district, tehsil, village, plotno):
    if not n_clicks or not all([district, tehsil, village, plotno]):
        return [], [17.123, 75.644]

    gdf = load_geojson(tehsil)
    if gdf is None:
        return [], [17.123, 75.644]

    village_plots = gdf[(
        gdf['District'].str.strip().str.lower() == str(district).strip().lower()) &
        (gdf['Tehsil'].str.strip().str.lower() == str(tehsil).strip().lower()) &
        (gdf['Village'].str.strip().str.lower() == str(village).strip().lower())
    ]
    selected_plot = village_plots[village_plots['Plot No.'] == str(plotno).strip()]
    map_center = [17.123, 75.644]
    
    if not selected_plot.empty:
        bounds = selected_plot.geometry.iloc[0].bounds
        map_center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    # Identify adjacent polygons
    adjacent_polygons = []
    if not selected_plot.empty:
        selected_geometry = selected_plot.geometry.iloc[0]
        for _, row in village_plots.iterrows():
            if row.geometry.intersects(selected_geometry) and not row.geometry.equals(selected_geometry):
                adjacent_polygons.append(row)

    # Construct geojson for selected plot and adjacent polygons
    selected_geojson = {'type': 'FeatureCollection', 'features': []}
    adjacent_geojson = {'type': 'FeatureCollection', 'features': []}

    if not selected_plot.empty:
        geojson_geom = json.loads(gpd.GeoSeries([selected_plot.geometry.iloc[0]]).to_json())
        feature = {
            'type': 'Feature',
            'geometry': geojson_geom['features'][0]['geometry'],
            'properties': {'Plot No.': str(plotno)}
        }
        selected_geojson['features'].append(feature)

    # Add selected plot GeoJSON layer
    layers = []
    if selected_geojson['features']:
        layers.append(
            dl.GeoJSON(
                data=selected_geojson,
                id="selected-geojson-data",
                zoomToBounds=True,
                options={
                    "style": {"color": "green", "weight": 5, "fillOpacity": 0.5, "fillColor": "#00FF00"}
                },
                children=[dl.Popup([html.Div(f"Plot No: {str(plotno)}")])]
            )
        )

    # Add adjacent polygons GeoJSON layers
    for adj in adjacent_polygons:
        geojson_geom = json.loads(gpd.GeoSeries([adj.geometry]).to_json())
        feature = {
            'type': 'Feature',
            'geometry': geojson_geom['features'][0]['geometry'],
            'properties': {'Plot No.': adj['Plot No.']}
        }
        adjacent_geojson['features'].append(feature)

        layers.append(
            dl.GeoJSON(
                data=feature,
                id=f"adjacent-geojson-data-{adj['Plot No.']}",
                options={
                    "style": {"color": "blue", "weight": 3, "fillOpacity": 0.3, "fillColor": "#0000FF"}
                },
                children=[dl.Popup([html.Div(f"Plot No: {adj['Plot No.']}")])]
            )
        )

    return layers, map_center


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)