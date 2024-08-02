import panel as pn
import pandas as pd
import plotly.express as px
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a sample DataFrame
df = pd.DataFrame({
    'date': pd.date_range(start='2022-01-01', end='2023-01-01', freq='D'),
    'value': range(366),
    'category': ['A', 'B'] * 183
})

pn.extension('plotly')

@pn.depends()
def plot_data():
    logging.debug("Creating plot")
    fig = px.line(df, x='date', y='value', color='category', title="Sample Plot")
    logging.debug("Plot created successfully")
    return pn.pane.Plotly(fig, sizing_mode='stretch_both', height=600)

layout = pn.template.MaterialTemplate(
    title='Simplified Visualization',
    main=[pn.panel(plot_data, sizing_mode='stretch_both')]
)

logging.debug("Setting up the layout")
layout.servable()
logging.debug("Layout is ready to be served")