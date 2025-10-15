from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.cost_mapping import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.national_aggregator import aggregate_to_national_level
import pandas as pd

"""
Main function to run the nationally aggregated analysis for all modelling years.

Parameters:
-----------
config_path : str
    Path to config file (default: 'config.yaml')

Returns:
--------
dict : Dictionary of networks keyed by year
"""

config_path='config.yaml'
# Load configuration
config = load_config(config_path)

# Get modelling years
years = config.get('Years', [])
if not years:
    years = [config['Base_year']['year']]

# Prepare networks for each year
networks = {}

for year in years:
    print(f"\nProcessing year: {year}")

    # to-do
    # develop filtering by year for other years
    # for other years base network - retirements + addition
    # develop a function to create grid network by region based on the OSM grid
    # aggregate generators by carrier?

    # Load network
    network = load_network(config)

    # Set snapshots to 48 hours starting from January 1st (BEFORE applying data)
    start_time = pd.Timestamp(f'{year}-01-01 00:00:00')
    end_time = start_time + pd.Timedelta(hours=48)
    network.set_snapshots(pd.date_range(start=start_time, end=end_time, freq='h', inclusive='left'))

    # Load and apply monthly data
    monthly_df = load_monthly_data(config)
    apply_monthly_data_to_network(network, config, monthly_df)

    # Load and apply snapshot data
    snapshot_df = load_snapshot_data(config)
    apply_snapshot_data_to_network(network, config, snapshot_df)

    # Aggregate to national level (after applying regional data)
    network = aggregate_to_national_level(network)
    network.generators[['p_min_pu', 'ramp_limit_up', 'ramp_limit_down', 'min_up_time', 'min_down_time']] = 0

    network.optimize()
    
    # Store the network
    networks[year] = network

