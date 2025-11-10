"""
Test script to visualize transmission flows in the province-level network.
"""

from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.temporal_data import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.carrier_standardization import standardize_carrier_names
from libs.component_attributes import apply_generator_attributes, apply_storage_unit_attributes
from libs.cc_merger import merge_cc_generators
from libs.generator_p_set import set_generator_p_set
from libs.energy_constraints import apply_cf_energy_constraints
from libs.visualization import plot_transmission_flows
from libs.region_aggregator import aggregate_network_by_region

# Load config
config_path = 'config/config_province.xlsx'
config = load_config(config_path)

# Load and process network
network = load_network(config)
network = merge_cc_generators(network, config)

# Apply data
monthly_df = load_monthly_data(config)
network = apply_monthly_data_to_network(network, config, monthly_df)

snapshot_df = load_snapshot_data(config)
network = apply_snapshot_data_to_network(network, config, snapshot_df)

network.generators_t.marginal_cost = network.generators_t.fuel_cost

# Aggregate by region
network = aggregate_network_by_region(network, config)

# Standardize carriers
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)

# Set p_set
network = set_generator_p_set(network, carrier_list=['solar', 'wind'])

# Apply attributes
generator_attributes = config.get('generator_attributes', {})
network = apply_generator_attributes(network, generator_attributes)

storage_unit_attributes = config.get('storage_unit_attributes', {})
network = apply_storage_unit_attributes(network, storage_unit_attributes)

# Define optimization snapshots
optimization_snapshots = network.snapshots[:48]

# Apply energy constraints
network = apply_cf_energy_constraints(network, generator_attributes, optimization_snapshots)

# Run optimization
print("\n[info] Running optimization...")
status = network.optimize(snapshots=optimization_snapshots)

if status[0] == 'ok':
    print("[info] Optimization succeeded\n")

    # Show transmission flows for links (top 10)
    print("=" * 80)
    print("INTER-PROVINCIAL LINK FLOWS (Top 10)")
    print("=" * 80)
    fig_links = plot_transmission_flows(
        network,
        snapshots=optimization_snapshots,
        component='links',
        top_n=10,
        title='Inter-Provincial Link Flows (Top 10 Routes)'
    )
    if fig_links:
        fig_links.show()

    # Show all link flows
    print("\n" + "=" * 80)
    print("ALL INTER-PROVINCIAL LINK FLOWS")
    print("=" * 80)
    fig_all_links = plot_transmission_flows(
        network,
        snapshots=optimization_snapshots,
        component='links',
        top_n=None,
        title='All Inter-Provincial Link Flows'
    )
    if fig_all_links:
        fig_all_links.show()

    # Show line flows if any exist
    if len(network.lines) > 0:
        print("\n" + "=" * 80)
        print("TRANSMISSION LINE FLOWS")
        print("=" * 80)
        fig_lines = plot_transmission_flows(
            network,
            snapshots=optimization_snapshots,
            component='lines',
            top_n=10,
            title='Transmission Line Flows (Top 10)'
        )
        if fig_lines:
            fig_lines.show()

else:
    print(f"[error] Optimization failed with status: {status[0]}")
    print(f"[error] Termination condition: {status[1]}")
