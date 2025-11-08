"""
Main function to run regional network analysis.

Aggregates the network by geographical regions (provinces by default).
Each region gets:
- One bus (aggregated from all buses in that region)
- Generators mapped to regional bus based on their region
- Lines aggregated by region pairs based on config rules
- Loads distributed based on regional demand shares

Usage:
------
python main_region.py

Configuration:
--------------
All regional aggregation settings are in config/config.yaml under 'regional_aggregation':
- region_column: Column name to aggregate by (default: 'province')
- demand_file: Path to regional demand file
- province_mapping_file: Path to province name mapping file
- lines.grouping: How to group lines ('by_voltage' or 'ignore_voltage')
- lines.circuits: How to aggregate circuits ('sum', 'max', 'mean')
- lines.s_nom: How to aggregate nominal power ('keep_original', 'sum', 'max', 'scale_by_circuits')
- lines.impedance: How to aggregate r/x/b ('weighted_by_circuits', 'mean', 'min', 'max')
- lines.length: How to aggregate length ('mean', 'max', 'min')
- lines.remove_self_loops: Remove intra-regional transmission lines (true/false)
"""

from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.cost_mapping import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.cc_merger import merge_cc_generators
from libs.region_aggregator import aggregate_network_by_region
# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

# Path to config file
config_path = 'config/config_province.yaml'

# ============================================================================
# MAIN EXECUTION
# ============================================================================

config = load_config(config_path)

network = load_network(config)

network = merge_cc_generators(network, config)

# Load and apply monthly data (uses original carrier names from data files)
monthly_df = load_monthly_data(config)
network = apply_monthly_data_to_network(network, config, monthly_df)

# Load and apply snapshot data (uses original carrier names from data files)
snapshot_df = load_snapshot_data(config)
network = apply_snapshot_data_to_network(network, config, snapshot_df)

# Aggregate network by region (uses original carrier names)
network = aggregate_network_by_region(network, config)

# Optional: Aggregate generators by carrier and region
# This creates one generator per (carrier, region) combination
# NOTE: This is already done inside aggregate_network_by_region() if config has:
#       regional_aggregation.aggregate_generators_by_carrier: true
# Only uncomment below if you disabled it in config but want to run it manually:
# from libs.region_aggregator import load_province_mapping
# province_mapping = load_province_mapping(config['regional_aggregation']['province_mapping_file'])
# network = aggregate_generators_by_carrier_and_region(network, config, region_column='province', province_mapping=province_mapping)

# IMPORTANT: Standardize carrier names at the END, just before optimization
#
# This is the FINAL step before optimization. All data import/processing uses original
# carrier names, then we standardize everything at once for clean, consistent network.
from libs.cost_mapping import standardize_carrier_names
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)

# Define 48-hour snapshot range for optimization
optimization_snapshots = network.snapshots[:48]

# Run optimization
network.optimize(snapshots=optimization_snapshots)

# Results would be available in:
# - network.generators_t.p  (generator dispatch)
# - network.lines_t.p0      (line flows)
# - network.loads_t.p       (load consumption)


# try with links
# update to lines

