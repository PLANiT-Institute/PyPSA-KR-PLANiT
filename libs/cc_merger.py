"""
Functions to merge combined cycle (CC) generators in PyPSA networks.

Simple rule-based merging using config.
"""

import pandas as pd


def merge_cc_generators(network, config=None):
    """
    Merge combined cycle generators by their cc_group using config rules.

    Rules from config define how to aggregate each attribute:
    - oldest/smallest: min()
    - newest/largest: max()
    - sum: sum()
    - mean: mean()
    - p_nom: use value from generator with largest p_nom
    - cc_group: use the cc_group value itself
    - others: default rule for unspecified attributes

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object
    config : dict
        Configuration with cc_merge_rules

    Returns:
    --------
    pypsa.Network : Modified network with CC groups merged
    """
    print("[info] Merging CC generators...")

    # Check if cc_group column exists
    if 'cc_group' not in network.generators.columns:
        print("[warn] No 'cc_group' column found. Skipping CC merge.")
        return network

    # Get merge rules from config
    if not config or 'cc_merge_rules' not in config:
        print("[warn] No cc_merge_rules in config. Skipping CC merge.")
        return network

    rules = config['cc_merge_rules']
    default_rule = rules.get('others', 'p_nom')  # Default for unspecified attributes

    # Find all generators with a cc_group (non-null)
    cc_mask = network.generators['cc_group'].notna()
    if not cc_mask.any():
        print("[info] No CC generators found.")
        return network

    unique_groups = network.generators.loc[cc_mask, 'cc_group'].unique()
    print(f"[info] Found {cc_mask.sum()} CC generators in {len(unique_groups)} groups")

    # Standard PyPSA generator attributes
    standard_attrs = ['bus', 'control', 'type', 'p_nom', 'p_nom_extendable', 'p_nom_min', 'p_nom_max',
                     'p_min_pu', 'p_max_pu', 'p_set', 'q_set', 'sign', 'carrier', 'marginal_cost',
                     'capital_cost', 'efficiency', 'committable', 'start_up_cost', 'shut_down_cost',
                     'min_up_time', 'min_down_time', 'up_time_before', 'down_time_before',
                     'ramp_limit_up', 'ramp_limit_down', 'ramp_limit_start_up', 'ramp_limit_shut_down',
                     'build_year', 'lifetime', 'weight', 'max_hours']

    # Store list of merged generators to track what was processed
    merged_generators_data = {}

    # Process each CC group
    for group_name in unique_groups:
        group_mask = network.generators['cc_group'] == group_name
        gen_names = network.generators.index[group_mask].tolist()
        group_data = network.generators.loc[gen_names]

        # Find generator with largest p_nom (for 'p_nom' rule)
        largest_gen_idx = group_data['p_nom'].idxmax()

        # Build merged attributes by applying rules
        merged_attrs = {}
        for col in network.generators.columns:
            # Get rule for this attribute
            rule = rules.get(col, default_rule)

            # Apply rule
            if rule == 'cc_group':
                merged_attrs[col] = group_name
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

        # Remove all old generators
        for gen_name in gen_names:
            network.remove("Generator", gen_name)

        # Add merged generator - separate standard and custom attrs
        merged_name = f"{group_name}_CC"
        std_attrs = {k: v for k, v in merged_attrs.items() if k in standard_attrs and pd.notna(v)}

        # Convert time-based parameters to integers (required by PyPSA)
        integer_attrs = ['min_up_time', 'min_down_time', 'up_time_before', 'down_time_before']
        for attr in integer_attrs:
            if attr in std_attrs:
                std_attrs[attr] = int(std_attrs[attr])

        network.add("Generator", merged_name, **std_attrs)

        # Add custom attributes directly to DataFrame
        custom_attrs = {k: v for k, v in merged_attrs.items() if k not in standard_attrs and pd.notna(v)}
        for attr, value in custom_attrs.items():
            network.generators.loc[merged_name, attr] = value

    print(f"[info] Merged into {len(unique_groups)} combined units")
    return network
