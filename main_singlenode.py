from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.cost_mapping import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.cc_merger import merge_cc_generators

"""
Main function to run the single node analysis for all modelling years.

The network data is already a single node (all components connected to 'KR' bus).

Parameters:
-----------
config_path : str
    Path to config file (default: 'config.yaml')

Returns:
--------
dict : Dictionary of networks keyed by year
"""

config_path='config/config.yaml'
# Load configuration
config = load_config(config_path)

year = 2024

# Load network
network = load_network(config)

# Merge combined cycle generators
network = merge_cc_generators(network, config)

# Load and apply monthly data
monthly_df = load_monthly_data(config)
apply_monthly_data_to_network(network, config, monthly_df)

# Load and apply snapshot data
snapshot_df = load_snapshot_data(config)
apply_snapshot_data_to_network(network, config, snapshot_df)

# Network is already single node - no bus mapping needed

# Define 48-hour snapshot range for optimization
# Use the first 48 snapshots from the network
optimization_snapshots = network.snapshots[:48]

# Run optimization for only the specified snapshots
network.optimize(snapshots=optimization_snapshots) # 

# To do
# 1. Add a gui function that allows the user to run utils. 
# 2. Add a function to merge generators and others by privince or other regions in column (aggregation)
# 3. Add a function to create a bus mapping function that allows the user to map the network to a single bus or multiple buses by region or other regions in column (aggregation)
# 4. Add a function to create the links or lines (with limited flows or capacities that is user input) between buses
# 5. add a function divide load into the region, and the share is from the config (normalized by the total value, the user can use the annual generation total, population or anything that the user would like to use)
# 6. regional generation limit is from 행정구역별 시간대별 전력거래량 (generation by region and hour)
# 7. regional load should come from somwehere. 

