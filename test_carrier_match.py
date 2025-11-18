"""Test script to verify carrier matching in generators_t.p_max_pu"""
import sys
sys.path.insert(0, '.')

from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.temporal_data import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.carrier_standardization import standardize_carrier_names
from libs.region_aggregator import aggregate_network_by_region
from libs.cc_merger import merge_cc_generators

# Load network using the same method as main_group.py
config_path = 'config/config_group.xlsx'
config = load_config(config_path)
network = load_network(config)
network = merge_cc_generators(network, config)

# Load and apply data
monthly_df = load_monthly_data(config)
network = apply_monthly_data_to_network(network, config, monthly_df)
snapshot_df = load_snapshot_data(config)
network = apply_snapshot_data_to_network(network, config, snapshot_df)

# Aggregate by region
network = aggregate_network_by_region(network, config)

# Standardize carrier names
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)

print("=" * 80)
print("CHECKING CARRIER MATCHING")
print("=" * 80)

# Check generators_t.p_max_pu columns
if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
    print("\ngenerators_t.p_max_pu columns (first 10):")
    print(list(network.generators_t.p_max_pu.columns[:10]))

    print("\ngenerators.index (first 10):")
    print(list(network.generators.index[:10]))

    print("\ngenerators.carrier (first 10):")
    print(network.generators.loc[network.generators.index[:10], 'carrier'].to_dict())

    # Test carrier lookup for first 5 p_max_pu columns
    print("\n" + "=" * 80)
    print("CARRIER LOOKUP TEST")
    print("=" * 80)

    for col in network.generators_t.p_max_pu.columns[:5]:
        print(f"\nColumn: {col}")
        if col in network.generators.index:
            carrier = network.generators.loc[col, 'carrier']
            print(f"  ✓ Found in generators.index")
            print(f"  Carrier: {carrier}")
        else:
            print(f"  ✗ NOT found in generators.index")
else:
    print("No generators_t.p_max_pu data available")
