import dash
from dash import html, dcc, Input, Output
import pandas as pd
import os

# 🔹 Load and combine all Excel files from the "data" folder
folder_path = "data"
all_dataframes = []

for file in os.listdir(folder_path):
    if file.endswith(".xlsx"):
        file_path = os.path.join(folder_path, file)
        df_temp = pd.read_excel(file_path)
        all_dataframes.append(df_temp)

df = pd.concat(all_dataframes, ignore_index=True)
print("Loaded columns:", df.columns.tolist())  # Debug line

# Rename Taluka column internally if needed
# df = df.rename(columns={"Taluka": "Tehsil"})  # Optional if you want to keep using 'Tehsil'

app = dash.Dash(__name__)
server = app.server
app.title = "Ownership Identification"

# Layout
app.layout = html.Div([
    html.H2("Ownership Identification Dashboard", id='header'),

    html.Label("Select District"),
    dcc.Dropdown(id='district-dropdown',
                 options=[{'label': dist, 'value': dist} for dist in sorted(df['District'].dropna().unique())],
                 placeholder="Select District"),

    html.Label("Select Taluka"),
    dcc.Dropdown(id='taluka-dropdown', placeholder="Select Taluka"),

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

# 🔁 Callback to update Taluka options
@app.callback(
    Output('taluka-dropdown', 'options'),
    Input('district-dropdown', 'value')
)
def update_talukas(selected_district):
    print("Selected District:", selected_district)
    if not selected_district:
        return []
    try:
        talukas = df[df['District'] == selected_district]['Taluka'].dropna().unique()
        print("Talukas:", talukas)
        return [{'label': t, 'value': t} for t in sorted(talukas)]
    except Exception as e:
        print("Error updating Talukas:", e)
        return []

# 🔁 Callback to update Villages
@app.callback(
    Output('village-dropdown', 'options'),
    [Input('district-dropdown', 'value'),
     Input('taluka-dropdown', 'value')]
)
def update_villages(district, taluka):
    if not (district and taluka):
        return []
    try:
        dff = df[(df['District'] == district) & (df['Taluka'] == taluka)]
        return [{'label': v, 'value': v} for v in sorted(dff['Village'].dropna().unique())]
    except Exception as e:
        print("Error updating Villages:", e)
        return []

# 🔁 Callback to update Plot Nos
@app.callback(
    Output('plotno-dropdown', 'options'),
    [Input('district-dropdown', 'value'),
     Input('taluka-dropdown', 'value'),
     Input('village-dropdown', 'value')]
)
def update_plotnos(district, taluka, village):
    if not (district and taluka and village):
        return []
    try:
        dff = df[(df['District'] == district) & (df['Taluka'] == taluka) & (df['Village'] == village)]
        return [{'label': p, 'value': p} for p in sorted(dff['Plot No.'].dropna().unique())]
    except Exception as e:
        print("Error updating Plot Nos:", e)
        return []

# 🔁 Callback to show Plot Info
@app.callback(
    Output('plot-info-box', 'children'),
    [Input('district-dropdown', 'value'),
     Input('taluka-dropdown', 'value'),
     Input('village-dropdown', 'value'),
     Input('plotno-dropdown', 'value')]
)
def display_plot_info(district, taluka, village, plotno):
    if not all([district, taluka, village, plotno]):
        return "Please select all options."
    try:
        row = df[(df['District'] == district) & 
                 (df['Taluka'] == taluka) & 
                 (df['Village'] == village) & 
                 (df['Plot No.'] == plotno)]
        if not row.empty:
            return row['Plot Info'].values[0]
        return "No plot info available."
    except Exception as e:
        print("Error displaying Plot Info:", e)
        return "Error occurred."

# ✅ Correct run method for Dash 3+
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=True, port=port, host="0.0.0.0")