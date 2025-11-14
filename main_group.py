"""
Main function to run regional/group-level network analysis.

Aggregates the network by geographical regions (provinces by default) and optionally
further aggregates into system groups (e.g., mainland vs islands).

Aggregation levels:
-------------------
1. Regional level (17 provinces): Each region gets:
   - One bus (aggregated from all buses in that region)
   - Generators mapped to regional bus based on their region
   - Lines aggregated by region pairs based on config rules
   - Loads distributed based on regional demand shares

2. Group level (2-3 groups): Optional second-level aggregation:
   - Regional buses aggregated into group buses (e.g., 육지, 제주)
   - Generators remapped to group buses
   - Lines/links aggregated by group pairs
   - Loads summed within each group

Usage:
------
python main_group.py

Configuration:
--------------
All settings are in config/config_group.xlsx:
- regional_aggregation sheet: Main aggregation settings
  - aggregate_by_region: Enable regional aggregation (TRUE/FALSE)
  - aggregate_by_carrier: Merge generators by carrier within region (TRUE/FALSE)
  - aggregate_regions_by_group: Enable group-level aggregation (TRUE/FALSE)
  - region_column: Column name to aggregate by (default: 'province')
  - region_groups: Column name for group aggregation (default: 'group1')
  - demand_file: Path to regional demand file
  - province_mapping_file: Path to province name mapping file
- province_mapping sheet: Region and group definitions
  - short: Short region name (e.g., '강원', '경기')
  - official: Official region name (e.g., '강원특별자치도')
  - group1: First grouping level (e.g., '육지', '제주')
  - group2: Second grouping level (e.g., '수도권', '육지', '제주')
- lines_config sheet: Line aggregation rules
  - grouping: How to group lines ('by_voltage' or 'ignore_voltage')
  - circuits_rule: How to aggregate circuits ('sum', 'max', 'mean')
  - s_nom_rule: How to aggregate nominal power ('keep_original', 'sum', 'max', 'scale_by_circuits')
  - impedance_rule: How to aggregate r/x/b ('weighted_by_circuits', 'mean', 'min', 'max')
  - length_rule: How to aggregate length ('mean', 'max', 'min')
  - remove_self_loops: Remove intra-regional transmission lines
- links_config sheet: Link aggregation rules (if links exist)
- generator_region_agg_rules sheet: Generator aggregation rules (if aggregate_by_carrier=TRUE)
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

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

# Path to config file
config_path = 'config/config_group.xlsx'

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

    # Determine aggregation level for chart title
    regional_config = config.get('regional_aggregation', {})
    if regional_config.get('aggregate_regions_by_group', False):
        agg_level = 'Group Level'
    else:
        agg_level = 'Regional Level'

    fig = plot_generation_by_carrier(
        network,
        snapshots=optimization_snapshots,
        include_storage=True,
        title=f'Generation by Carrier - {agg_level} (Including Storage Discharge)',
        carriers_order=carriers_order
    )
    fig.show()
