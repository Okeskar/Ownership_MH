import dash
from dash import html, dcc, Input, Output
import pandas as pd

# Load Excel data
df = pd.read_excel("data.xlsx")  # Make sure data.xlsx is in the same folder

app = dash.Dash(__name__)
server = app.server
app.title = "Ownership Identification"

# Layout
app.layout = html.Div([
    html.H2("Ownership Identification Dashboard"),

    html.Label("Select District"),
    dcc.Dropdown(id='district-dropdown',
                 options=[{'label': dist, 'value': dist} for dist in sorted(df['District'].unique())],
                 placeholder="Select District"),

    html.Label("Select Tehsil"),
    dcc.Dropdown(id='tehsil-dropdown', placeholder="Select Tehsil"),

    html.Label("Select Village"),
    dcc.Dropdown(id='village-dropdown', placeholder="Select Village"),

    html.Label("Select Plot No."),
    dcc.Dropdown(id='plotno-dropdown', placeholder="Select Plot No."),

    html.H4("Plot Information"),
    html.Div(id='plot-info-box', style={
        'border': '1px solid #ccc', 'padding': '10px', 'minHeight': '100px'
    }),

    html.Div("Created by Blueleap Consultancy Pvt Ltd", style={
        'position': 'fixed', 'bottom': '10px', 'left': '10px',
        'fontSize': '12px', 'color': '#888'
    })
])

@app.callback(
    Output('tehsil-dropdown', 'options'),
    Input('district-dropdown', 'value')
)
def update_tehsils(selected_district):
    if not selected_district:
        return []
    return [{'label': t, 'value': t} for t in sorted(df[df['District'] == selected_district]['Tehsil'].unique())]

@app.callback(
    Output('village-dropdown', 'options'),
    [Input('district-dropdown', 'value'),
     Input('tehsil-dropdown', 'value')]
)
def update_villages(district, tehsil):
    if not (district and tehsil):
        return []
    dff = df[(df['District'] == district) & (df['Tehsil'] == tehsil)]
    return [{'label': v, 'value': v} for v in sorted(dff['Village'].unique())]

@app.callback(
    Output('plotno-dropdown', 'options'),
    [Input('district-dropdown', 'value'),
     Input('tehsil-dropdown', 'value'),
     Input('village-dropdown', 'value')]
)
def update_plotnos(district, tehsil, village):
    if not (district and tehsil and village):
        return []
    dff = df[(df['District'] == district) & (df['Tehsil'] == tehsil) & (df['Village'] == village)]
    return [{'label': p, 'value': p} for p in sorted(dff['Plot No.'].unique())]

@app.callback(
    Output('plot-info-box', 'children'),
    [Input('district-dropdown', 'value'),
     Input('tehsil-dropdown', 'value'),
     Input('village-dropdown', 'value'),
     Input('plotno-dropdown', 'value')]
)
def display_plot_info(district, tehsil, village, plotno):
    if not all([district, tehsil, village, plotno]):
        return "Please select all options."
    row = df[(df['District'] == district) & 
             (df['Tehsil'] == tehsil) & 
             (df['Village'] == village) & 
             (df['Plot No.'] == plotno)]
    if not row.empty:
        return row['Plot Info'].values[0]
    return "No plot info available."

if __name__ == '__main__':
    app.run_server(debug=True)
