"""Test to find where p_max_pu data is created"""
import sys
sys.path.insert(0, '.')

from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.temporal_data import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.carrier_standardization import standardize_carrier_names
from libs.region_aggregator import aggregate_network_by_region
from libs.cc_merger import merge_cc_generators

config = load_config('config/config_group.xlsx')

# Step 1: Load network
network = load_network(config)
print("\n1. After load_network:")
print(f"   generators_t.p_max_pu exists: {hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty}")

# Step 2: Merge CC
network = merge_cc_generators(network, config)
print("\n2. After merge_cc_generators:")
print(f"   generators_t.p_max_pu exists: {hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty}")

# Step 3: Load monthly data
monthly_df = load_monthly_data(config)
network = apply_monthly_data_to_network(network, config, monthly_df)
print("\n3. After apply_monthly_data:")
print(f"   generators_t.p_max_pu exists: {hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty}")

# Step 4: Load snapshot data
snapshot_df = load_snapshot_data(config)
network = apply_snapshot_data_to_network(network, config, snapshot_df)
print("\n4. After apply_snapshot_data:")
print(f"   generators_t.p_max_pu exists: {hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty}")

# Step 5: Aggregate by region
network = aggregate_network_by_region(network, config)
print("\n5. After aggregate_network_by_region:")
if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
    print(f"   generators_t.p_max_pu EXISTS!")
    print(f"   Shape: {network.generators_t.p_max_pu.shape}")
    print(f"   Columns (first 5): {list(network.generators_t.p_max_pu.columns[:5])}")
    print(f"   First row values:")
    print(f"   {network.generators_t.p_max_pu.iloc[0, :5].to_dict()}")
    print(f"   Mean of first column: {network.generators_t.p_max_pu.iloc[:, 0].mean():.4f}")
else:
    print(f"   generators_t.p_max_pu does NOT exist")

# Step 6: Standardize carriers
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)
print("\n6. After standardize_carrier_names:")
if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
    print(f"   generators_t.p_max_pu shape: {network.generators_t.p_max_pu.shape}")
    print(f"   Mean of first column: {network.generators_t.p_max_pu.iloc[:, 0].mean():.4f}")
else:
    print(f"   generators_t.p_max_pu does NOT exist")
