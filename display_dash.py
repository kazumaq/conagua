import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import os
import glob
import json

# Function to load and process JSON files
def load_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    df = pd.json_normalize(data)
    df['fechamonitoreo'] = pd.to_datetime(df['fechamonitoreo'], errors='coerce')
    return df

# Function to get all JSON files in the dam_data directory
def get_json_files():
    dam_data_dir = 'dam_data'
    files = [os.path.join(dam_data_dir, f) for f in os.listdir(dam_data_dir) 
             if f.endswith('.json') and f[0].isdigit()]
    return files

# Load all data
def load_all_data():
    files = get_json_files()
    all_data = pd.concat([load_data(file) for file in files], ignore_index=True)
    all_data = all_data.dropna(subset=['fechamonitoreo', 'clavesih'])
    all_data = all_data.sort_values('fechamonitoreo')
    name_mapping = all_data.groupby('clavesih')['nombrecomun'].agg(lambda x: x.value_counts().index[0]).to_dict()
    all_data['reservoir_name'] = all_data['clavesih'] + ' - ' + all_data['clavesih'].map(name_mapping)
    return all_data

# Load data
df = load_all_data()

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Water Reservoir Visualization"),
    
    html.Div([
        html.Label("Select State"),
        dcc.Dropdown(
            id='state-dropdown',
            options=[{'label': state, 'value': state} for state in sorted(df['estado'].unique())],
            multi=True
        )
    ]),
    
    html.Div([
        html.Label("Select Reservoir"),
        dcc.Dropdown(
            id='reservoir-dropdown',
            options=[],
            multi=True
        )
    ]),
    
    html.Div([
        html.Label("Select Date Range"),
        dcc.DatePickerRange(
            id='date-picker',
            start_date=df['fechamonitoreo'].min().date(),
            end_date=df['fechamonitoreo'].max().date()
        )
    ]),
    
    dcc.Graph(id='storage-graph')
])

@app.callback(
    Output('reservoir-dropdown', 'options'),
    Input('state-dropdown', 'value')
)
def set_reservoir_options(selected_state):
    if not selected_state:
        return []
    filtered_df = df[df['estado'].isin(selected_state)]
    reservoirs = sorted(filtered_df['reservoir_name'].unique())
    return [{'label': res, 'value': res} for res in reservoirs]

@app.callback(
    Output('storage-graph', 'figure'),
    [Input('state-dropdown', 'value'),
     Input('reservoir-dropdown', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_graph(selected_state, selected_reservoir, start_date, end_date):
    filtered_df = df.copy()
    if selected_state:
        filtered_df = filtered_df[filtered_df['estado'].isin(selected_state)]
    if selected_reservoir:
        filtered_df = filtered_df[filtered_df['reservoir_name'].isin(selected_reservoir)]
    filtered_df = filtered_df[(filtered_df['fechamonitoreo'] >= start_date) & (filtered_df['fechamonitoreo'] <= end_date)]
    
    if not selected_reservoir:
        return px.line(title="Please select at least one reservoir to display the visualization.")
    
    fig = px.line(filtered_df, x='fechamonitoreo', y='almacenaactual', color='reservoir_name',
                  title="Storage Levels Over Time")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
