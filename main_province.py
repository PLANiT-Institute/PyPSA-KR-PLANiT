"""
Main function to run province-level network analysis.

Aggregates the network by geographical regions (provinces by default).
Each region gets:
- One bus (aggregated from all buses in that region)
- Generators mapped to regional bus based on their region
- Lines aggregated by region pairs based on config rules
- Loads distributed based on regional demand shares

Usage:
------
python main_province.py

Configuration:
--------------
All regional aggregation settings are in config/config_province.xlsx:
- province_aggregation sheet: Main aggregation settings
  - region_column: Column name to aggregate by (default: 'province')
  - demand_file: Path to regional demand file
  - province_mapping_file: Path to province name mapping file
  - aggregate_generators_by_carrier: Merge generators by carrier+region
- lines_config sheet: Line aggregation rules
  - grouping: How to group lines ('by_voltage' or 'ignore_voltage')
  - circuits_rule: How to aggregate circuits ('sum', 'max', 'mean')
  - s_nom_rule: How to aggregate nominal power ('keep_original', 'sum', 'max', 'scale_by_circuits')
  - impedance_rule: How to aggregate r/x/b ('weighted_by_circuits', 'mean', 'min', 'max')
  - length_rule: How to aggregate length ('mean', 'max', 'min')
  - remove_self_loops: Remove intra-regional transmission lines
- links_config sheet: Link aggregation rules (if links exist)
"""

from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.temporal_data import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.carrier_standardization import standardize_carrier_names
from libs.component_attributes import apply_generator_attributes, apply_storage_unit_attributes
from libs.cc_merger import merge_cc_generators
from libs.generator_p_set import set_generator_p_set
from libs.energy_constraints import apply_cf_energy_constraints
from libs.visualization import plot_generation_by_carrier
from libs.region_aggregator import aggregate_network_by_region
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

# Path to config file
config_path = 'config/config_province.xlsx'

# ============================================================================
# MAIN EXECUTION
# ============================================================================

config = load_config(config_path)

year = 2024

# Load network
network = load_network(config)

# Merge combined cycle generators
network = merge_cc_generators(network, config)

# Load and apply monthly data (uses original carrier names from data files)
monthly_df = load_monthly_data(config)
network = apply_monthly_data_to_network(network, config, monthly_df)

# Load and apply snapshot data (uses original carrier names from data files)
snapshot_df = load_snapshot_data(config)
network = apply_snapshot_data_to_network(network, config, snapshot_df)

network.generators_t.marginal_cost = network.generators_t.fuel_cost

# AGGREGATE NETWORK BY REGION (uses original carrier names)
# This creates one bus per region, aggregates lines/links, and distributes loads
network = aggregate_network_by_region(network, config)

# IMPORTANT: Standardize carrier names at the END, just before optimization
#
# This is the FINAL step before optimization. All data import/processing uses original
# carrier names, then we standardize everything at once for clean, consistent network.
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)

# Set p_set for solar and wind generators (AFTER standardization and attributes)
# This must come AFTER carrier standardization so carrier names are correct
network = set_generator_p_set(network, carrier_list=['solar', 'wind'])

# Apply carrier-specific generator attributes (AFTER carrier standardization)
# This sets p_min_pu, p_max_pu, etc. for each carrier type from config
generator_attributes = config.get('generator_attributes', {})
network = apply_generator_attributes(network, generator_attributes)

# Apply carrier-specific storage_unit attributes (AFTER carrier standardization)
# This sets efficiency_store, efficiency_dispatch, max_hours, etc. for each carrier type from config
storage_unit_attributes = config.get('storage_unit_attributes', {})
network = apply_storage_unit_attributes(network, storage_unit_attributes)

# Define snapshot range for optimization
# Use the first 48 snapshots from the network
optimization_snapshots = network.snapshots[:48]

# Apply capacity factor energy constraints (max_cf, min_cf → e_sum_max, e_sum_min)
# This must be called AFTER snapshots are defined and BEFORE optimization
network = apply_cf_energy_constraints(network, generator_attributes, optimization_snapshots)

# Run optimization for only the specified snapshots
status = network.optimize(snapshots=optimization_snapshots)

# Display chart only if optimization succeeded
if status[0] == 'ok':
    print("[info] Optimization succeeded")
    # Display interactive stacked area chart of generation by carrier (includes storage units)
    # Use carriers_order from config to control stacking (first = bottom/baseload, last = top)
    carriers_order = config.get('carriers_order', None)
    fig = plot_generation_by_carrier(
        network,
        snapshots=optimization_snapshots,
        include_storage=True,
        title='Generation by Carrier - Province Level (Including Storage Discharge)',
        carriers_order=carriers_order
    )
    fig.show()
