import dash
from dash import html, dcc, Input, Output
import pandas as pd
import os

# Load and combine all Excel files from the "data" folder
folder_path = "data"
all_dataframes = []

# Loop through all files in the folder and load the Excel files
for file in os.listdir(folder_path):
    if file.endswith(".xlsx"):
        file_path = os.path.join(folder_path, file)
        df_temp = pd.read_excel(file_path)
        all_dataframes.append(df_temp)

# Combine into a single dataframe
df = pd.concat(all_dataframes, ignore_index=True)

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # For deployment on Render or Heroku
app.title = "Ownership Identification"

# Layout
app.layout = html.Div([
    html.H2("Ownership Identification Dashboard"),

    html.Label("Select District"),
    dcc.Dropdown(id='district-dropdown',
                 options=[{'label': dist, 'value': dist} for dist in sorted(df['District'].dropna().unique())],
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

# Callback to update Tehsil options based on District selection
@app.callback(
    Output('tehsil-dropdown', 'options'),
    Input('district-dropdown', 'value')
)
def update_tehsils(selected_district):
    print("Selected District:", selected_district)  # DEBUG LINE

    if not selected_district:
        return []

    filtered = df[df['District'] == selected_district]
    print("Filtered Rows:", filtered.shape[0])  # DEBUG LINE

    if filtered.empty or 'Tehsil' not in filtered.columns:
        print("No tehsil data found.")  # DEBUG LINE
        return []

    tehsils = filtered['Tehsil'].dropna().unique()
    print("Tehsils Found:", tehsils)  # DEBUG LINE

    return [{'label': t, 'value': t} for t in sorted(tehsils)]

# Callback to update Village options based on District and Tehsil selection
@app.callback(
    Output('village-dropdown', 'options'),
    [Input('district-dropdown', 'value'),
     Input('tehsil-dropdown', 'value')]
)
def update_villages(district, tehsil):
    if not (district and tehsil):
        return []
    dff = df[(df['District'] == district) & (df['Tehsil'] == tehsil)]
    return [{'label': v, 'value': v} for v in sorted(dff['Village'].dropna().unique())]

# Callback to update Plot No. options based on District, Tehsil, and Village selection
@app.callback(
    Output('plotno-dropdown', 'options'),
    [Input('district-dropdown', 'value'),
     Input('tehsil-dropdown', 'value'),
     Input('village-dropdown', 'value')]
)
def update_plotnos(district, tehsil, village):
    if not (district and tehsil and village):
        return []
    dff = df[(df['District'] == district) & 
             (df['Tehsil'] == tehsil) & 
             (df['Village'] == village)]
    return [{'label': p, 'value': p} for p in sorted(dff['Plot No.'].dropna().unique())]

# Callback to display Plot Info based on selections
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

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
