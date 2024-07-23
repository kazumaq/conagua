import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import datetime, date

# Function to load and process JSON files
def load_data(file_path):
    print(f"Loading file: {file_path}")
    with open(file_path, 'r') as file:
        data = json.load(file)
    df = pd.json_normalize(data)
    df['fechamonitoreo'] = pd.to_datetime(df['fechamonitoreo'], errors='coerce')
    print(f"Date range in {file_path}: {df['fechamonitoreo'].min()} to {df['fechamonitoreo'].max()}")
    return df

# Function to get all JSON files in the dam_data directory
def get_json_files():
    dam_data_dir = 'dam_data'
    files = [os.path.join(dam_data_dir, f) for f in os.listdir(dam_data_dir) 
             if f.endswith('.json') and f[0].isdigit()]
    print(f"Found {len(files)} JSON files")
    return files

# Load all data
@st.cache_data
def load_all_data():
    files = get_json_files()
    all_data = pd.concat([load_data(file) for file in files], ignore_index=True)
    
    all_data = all_data.dropna(subset=['fechamonitoreo', 'clavesih'])
    all_data = all_data.sort_values('fechamonitoreo')
    
    # Create a mapping of clavesih to the most common nombrecomun
    name_mapping = all_data.groupby('clavesih')['nombrecomun'].agg(lambda x: x.value_counts().index[0]).to_dict()
    all_data['reservoir_name'] = all_data['clavesih'] + ' - ' + all_data['clavesih'].map(name_mapping)
    
    print(f"Total rows after processing: {len(all_data)}")
    print(f"Date range in all data: {all_data['fechamonitoreo'].min()} to {all_data['fechamonitoreo'].max()}")
    
    return all_data

# Streamlit app
def main():
    st.title("Water Reservoir Visualization")

    # Load data
    df = load_all_data()

    # Sidebar for filtering
    st.sidebar.header("Filters")
    
    # State selection
    selected_state = st.sidebar.multiselect("Select State", options=sorted(df['estado'].unique()))
    
    # Filter dataframe based on selected state
    if selected_state:
        df_filtered = df[df['estado'].isin(selected_state)]
    else:
        df_filtered = df

    # Reservoir selection (only show reservoirs from selected states)
    available_reservoirs = sorted(df_filtered['reservoir_name'].unique())
    selected_reservoir = st.sidebar.multiselect("Select Reservoir", options=available_reservoirs)

    # Apply reservoir filter
    if selected_reservoir:
        df_filtered = df_filtered[df_filtered['reservoir_name'].isin(selected_reservoir)]

    # Date range selector
    valid_dates = df_filtered['fechamonitoreo'].dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
    else:
        min_date = date(1991, 1, 1)  # Fallback start date
        max_date = date.today()  # Fallback end date
        st.warning("No valid dates found in the data. Using default date range.")

    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    df_filtered = df_filtered[(df_filtered['fechamonitoreo'].dt.date >= start_date) & (df_filtered['fechamonitoreo'].dt.date <= end_date)]

    # Visualizations
    st.header("Reservoir Storage Over Time")

    if selected_reservoir:
        if not df_filtered.empty:
            # Line chart of storage levels (almacenaactual)
            fig_storage = px.line(df_filtered, x='fechamonitoreo', y='almacenaactual', color='reservoir_name',
                                  title="Storage Levels Over Time")
            fig_storage.update_layout(xaxis_title="Date", yaxis_title="Storage (almacenaactual)")
            st.plotly_chart(fig_storage)
        else:
            st.warning("No data available for the selected criteria.")
    else:
        st.write("Please select at least one reservoir to display the visualization.")

    # Display date range information
    st.write(f"Full data range: from {min_date} to {max_date}")
    st.write(f"Number of unique dates in the data: {df_filtered['fechamonitoreo'].nunique()}")

    # Display raw data
    if st.checkbox("Show Raw Data"):
        st.write(df_filtered[['fechamonitoreo', 'clavesih', 'nombrecomun', 'estado', 'almacenaactual']])

    # Debug information
    st.subheader("Debug Information")
    st.write(f"Total number of rows: {len(df_filtered)}")
    st.write(f"Number of unique reservoirs: {df_filtered['clavesih'].nunique()}")
    st.write(f"Number of unique states: {df_filtered['estado'].nunique()}")
    st.write(f"Date range: {df_filtered['fechamonitoreo'].min()} to {df_filtered['fechamonitoreo'].max()}")
    st.write(f"Number of rows with NaT dates: {df_filtered['fechamonitoreo'].isna().sum()}")

if __name__ == "__main__":
    main()