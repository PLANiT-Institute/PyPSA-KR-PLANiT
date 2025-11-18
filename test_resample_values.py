"""Test to verify p_max_pu values after resampling"""
import sys
sys.path.insert(0, '.')

from libs.config import load_config
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
from libs.temporal_data import apply_monthly_data_to_network, apply_snapshot_data_to_network
from libs.carrier_standardization import standardize_carrier_names
from libs.region_aggregator import aggregate_network_by_region
from libs.cc_merger import merge_cc_generators
from libs.resample import resample_network

config = load_config('config/config_group.xlsx')
network = load_network(config)
network = merge_cc_generators(network, config)

monthly_df = load_monthly_data(config)
network = apply_monthly_data_to_network(network, config, monthly_df)
snapshot_df = load_snapshot_data(config)
network = apply_snapshot_data_to_network(network, config, snapshot_df)

network = aggregate_network_by_region(network, config)
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)

print("\n" + "=" * 80)
print("BEFORE CALLING resample_network()")
print("=" * 80)
if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
    print(f"generators_t.p_max_pu shape: {network.generators_t.p_max_pu.shape}")
    print(f"First 5 columns: {list(network.generators_t.p_max_pu.columns[:5])}")
    print(f"\nFirst row values (first 5 columns):")
    for col in network.generators_t.p_max_pu.columns[:5]:
        val = network.generators_t.p_max_pu.iloc[0][col]
        print(f"  {col}: {val:.4f}")
    print(f"\nMean values (first 5 columns):")
    for col in network.generators_t.p_max_pu.columns[:5]:
        mean_val = network.generators_t.p_max_pu[col].mean()
        print(f"  {col}: {mean_val:.4f}")
else:
    print("No generators_t.p_max_pu data")

# Check if snapshots are DatetimeIndex
print(f"\nnetwork.snapshots type: {type(network.snapshots)}")
print(f"network.snapshots length: {len(network.snapshots)}")

# Now resample
resample_rules = config.get('resample_rules', None)
network = resample_network(network, weights=4, resample_rules=resample_rules)

print("\n" + "=" * 80)
print("AFTER RESAMPLING")
print("=" * 80)
if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
    print(f"generators_t.p_max_pu shape: {network.generators_t.p_max_pu.shape}")
    print(f"First 5 columns: {list(network.generators_t.p_max_pu.columns[:5])}")
    print(f"\nFirst row values (first 5 columns):")
    for col in network.generators_t.p_max_pu.columns[:5]:
        val = network.generators_t.p_max_pu.iloc[0][col]
        print(f"  {col}: {val:.4f}")
    print(f"\nMean values (first 5 columns):")
    for col in network.generators_t.p_max_pu.columns[:5]:
        mean_val = network.generators_t.p_max_pu[col].mean()
        print(f"  {col}: {mean_val:.4f}")
else:
    print("No generators_t.p_max_pu data")
