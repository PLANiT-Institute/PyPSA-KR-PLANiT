"""
Functions to aggregate generators in PyPSA networks.

Aggregates generators by carrier or other grouping attributes using config rules.
"""

import pandas as pd


def aggregate_generators_by_carrier(network, config=None):
    """
    Aggregate generators by their carrier using config rules.

    After aggregation, each carrier becomes one generator.

    Rules from config define how to aggregate each attribute:
    - oldest/smallest: min()
    - newest/largest: max()
    - sum: sum()
    - mean: mean()
    - p_nom: use value from generator with largest p_nom
    - carrier: use the carrier value itself
    - remove: remove this attribute from the merged generator
    - others: default rule for unspecified attributes

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object
    config : dict
        Configuration with generator_aggregator_rules

    Returns:
    --------
    pypsa.Network : Modified network with generators aggregated by carrier
    """
    print("[info] Aggregating generators by carrier...")

    # Check if carrier column exists
    if 'carrier' not in network.generators.columns:
        print("[warn] No 'carrier' column found. Skipping generator aggregation.")
        return network

    # Get merge rules from config
    if not config or 'generator_aggregator_rules' not in config:
        print("[warn] No generator_aggregator_rules in config. Skipping generator aggregation.")
        return network

    rules = config['generator_aggregator_rules']
    default_rule = rules.get('others', 'sum')  # Default for unspecified attributes

    # Find all unique carriers
    unique_carriers = network.generators['carrier'].dropna().unique()
    print(f"[info] Found {len(network.generators)} generators with {len(unique_carriers)} unique carriers")

    # Standard PyPSA generator attributes
    standard_attrs = ['bus', 'control', 'type', 'p_nom', 'p_nom_extendable', 'p_nom_min', 'p_nom_max',
                     'p_min_pu', 'p_max_pu', 'p_set', 'q_set', 'sign', 'carrier', 'marginal_cost',
                     'capital_cost', 'efficiency', 'committable', 'start_up_cost', 'shut_down_cost',
                     'min_up_time', 'min_down_time', 'up_time_before', 'down_time_before',
                     'ramp_limit_up', 'ramp_limit_down', 'ramp_limit_start_up', 'ramp_limit_shut_down',
                     'build_year', 'lifetime', 'weight', 'max_hours']

    # Store all original generator names to remove later
    all_gen_names = network.generators.index.tolist()

    # Store merged generators data
    merged_generators = {}

    # Process each carrier
    for carrier in unique_carriers:
        carrier_mask = network.generators['carrier'] == carrier
        gen_names = network.generators.index[carrier_mask].tolist()
        group_data = network.generators.loc[gen_names]

        if len(gen_names) == 0:
            continue

        print(f"[info] Aggregating {len(gen_names)} generators for carrier '{carrier}'")

        # Find generator with largest p_nom (for 'p_nom' rule)
        largest_gen_idx = group_data['p_nom'].idxmax()

        # Build merged attributes by applying rules
        merged_attrs = {}
        for col in network.generators.columns:
            # Get rule for this attribute
            rule = rules.get(col, default_rule)

            # Skip if rule is 'remove'
            if rule == 'remove':
                continue

            # Apply rule
            if rule == 'carrier':
                merged_attrs[col] = carrier
            elif rule == 'p_nom':
                merged_attrs[col] = group_data.loc[largest_gen_idx, col]
            elif rule in ['oldest', 'smallest']:
                merged_attrs[col] = group_data[col].min()
            elif rule in ['newest', 'largest']:
                merged_attrs[col] = group_data[col].max()
            elif rule == 'sum':
                merged_attrs[col] = group_data[col].sum()
            elif rule == 'mean':
                merged_attrs[col] = group_data[col].mean()
            else:
                # Unknown rule, use from largest generator
                merged_attrs[col] = group_data.loc[largest_gen_idx, col]

        # Store merged generator data
        merged_generators[carrier] = merged_attrs

    # Remove all old generators
    for gen_name in all_gen_names:
        network.remove("Generator", gen_name)

    # Add aggregated generators
    for carrier, merged_attrs in merged_generators.items():
        # Create merged generator name
        merged_name = f"{carrier}_aggregated"

        # Separate standard and custom attrs
        std_attrs = {k: v for k, v in merged_attrs.items() if k in standard_attrs and pd.notna(v)}
        network.add("Generator", merged_name, **std_attrs)

        # Add custom attributes directly to DataFrame
        custom_attrs = {k: v for k, v in merged_attrs.items() if k not in standard_attrs and pd.notna(v)}
        for attr, value in custom_attrs.items():
            network.generators.loc[merged_name, attr] = value

    print(f"[info] Aggregated into {len(unique_carriers)} generators (one per carrier)")
    return network
