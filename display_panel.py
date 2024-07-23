import panel as pn
import pandas as pd
import os
import json
import plotly.express as px
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to load and process JSON files
def load_data(file_path):
    logging.debug(f"Loading file: {file_path}")
    with open(file_path, 'r') as file:
        data = json.load(file)
    df = pd.json_normalize(data)
    df['fechamonitoreo'] = pd.to_datetime(df['fechamonitoreo'], errors='coerce')
    logging.debug(f"Loaded data with shape: {df.shape}")
    return df

# Function to get all JSON files in the dam_data directory
def get_json_files():
    dam_data_dir = 'dam_data'
    files = [os.path.join(dam_data_dir, f) for f in os.listdir(dam_data_dir) 
             if f.endswith('.json') and f[0].isdigit()]
    logging.debug(f"Found {len(files)} JSON files")
    return files

# Load all data
def load_all_data():
    files = get_json_files()
    all_data = pd.concat([load_data(file) for file in files], ignore_index=True)
    all_data = all_data.dropna(subset=['fechamonitoreo', 'clavesih'])
    all_data = all_data.sort_values('fechamonitoreo')
    name_mapping = all_data.groupby('clavesih')['nombrecomun'].agg(lambda x: x.value_counts().index[0]).to_dict()
    all_data['reservoir_name'] = all_data['clavesih'] + ' - ' + all_data['clavesih'].map(name_mapping)
    logging.debug(f"Total rows after processing: {len(all_data)}")
    return all_data

# Start logging
logging.debug("Starting to load data")
df = load_all_data()
logging.debug("Finished loading data")

pn.extension('plotly')

# State filter
state_filter = pn.widgets.MultiSelect(name='Select State', options=list(df['estado'].unique()))

# Reservoir filter
reservoir_filter = pn.widgets.MultiSelect(name='Select Reservoir', options=[])

@pn.depends(state_filter.param.value, watch=True)
def update_reservoir_options(states):
    logging.debug(f"Updating reservoir options for states: {states}")
    if not states:
        reservoir_filter.options = []
    else:
        filtered_df = df[df['estado'].isin(states)]
        reservoirs = list(filtered_df['reservoir_name'].unique())
        reservoir_filter.options = reservoirs
    logging.debug(f"Reservoir options updated: {reservoir_filter.options}")

# Date range filter
date_range = pn.widgets.DateRangeSlider(name='Select Date Range', 
                                        start=df['fechamonitoreo'].min().date(),
                                        end=df['fechamonitoreo'].max().date(),
                                        value=(df['fechamonitoreo'].min().date(), df['fechamonitoreo'].max().date()))

@pn.depends(state_filter.param.value, reservoir_filter.param.value, date_range.param.value)
def plot_data(states, reservoirs, date_range):
    logging.debug(f"Plotting data for states: {states}, reservoirs: {reservoirs}, date_range: {date_range}")
    start_date, end_date = date_range
    if not states and not reservoirs:
        return pn.pane.Markdown("Please select state(s) and/or reservoir(s) to display the visualization.")

    filtered_df = df.copy()
    if states:
        filtered_df = filtered_df[filtered_df['estado'].isin(states)]
    if reservoirs:
        filtered_df = filtered_df[filtered_df['reservoir_name'].isin(reservoirs)]
    filtered_df = filtered_df[(filtered_df['fechamonitoreo'] >= pd.to_datetime(start_date)) & 
                              (filtered_df['fechamonitoreo'] <= pd.to_datetime(end_date))]
    
    if filtered_df.empty:
        logging.debug("Filtered dataframe is empty")
        return pn.pane.Markdown("No data available for the selected criteria.")

    fig = px.line(filtered_df, x='fechamonitoreo', y='almacenaactual', color='reservoir_name',
                  title="Storage Levels Over Time")
    logging.debug("Plot created successfully")
    return pn.pane.Plotly(fig, sizing_mode='stretch_both', height=600)

layout = pn.template.MaterialTemplate(
    title='Water Reservoir Visualization',
    sidebar=[state_filter, reservoir_filter, date_range],
    main=[pn.panel(plot_data, sizing_mode='stretch_both')]
)

logging.debug("Setting up the layout")
layout.servable()
logging.debug("Layout is ready to be served")
