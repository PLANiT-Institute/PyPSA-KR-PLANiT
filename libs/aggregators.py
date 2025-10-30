"""
Functions to aggregate generators in PyPSA networks.

Aggregates generators by carrier or other grouping attributes using config rules.
"""

import pandas as pd

def aggregate_generators_by_carrier_and_region(network, config=None, region_column=None):
    """
    Aggregate generators by carrier and region using config rules.

    If region_column is None, aggregates by carrier only.
    If region_column is specified, aggregates by (carrier, region) combination.

    After aggregation, generators are named:
    - {carrier}_aggregated (if region_column is None)
    - {carrier}_{region} (if region_column is specified)

    Rules from config define how to aggregate each attribute:
    - oldest/smallest: min()
    - newest/largest: max()
    - sum: sum()
    - mean: mean()
    - p_nom: use value from generator with largest p_nom
    - carrier: use the carrier value itself
    - region: use the region value itself
    - remove: remove this attribute from the merged generator
    - others: default rule for unspecified attributes

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object
    config : dict
        Configuration with generator_region_aggregator_rules
    region_column : str or None
        Column name to use for region grouping (default: None for carrier-only aggregation)

    Returns:
    --------
    pypsa.Network : Modified network with generators aggregated
    """
    # Check if required columns exist
    if 'carrier' not in network.generators.columns:
        print("[warn] No 'carrier' column found. Skipping generator aggregation.")
        return network

    # Determine aggregation mode
    if region_column is None:
        print(f"[info] Aggregating generators by carrier only...")
        group_by_region = False
    else:
        if region_column not in network.generators.columns:
            print(f"[warn] No '{region_column}' column found. Aggregating by carrier only...")
            group_by_region = False
            region_column = None
        else:
            print(f"[info] Aggregating generators by carrier and {region_column}...")
            group_by_region = True

    # Get merge rules from config
    if not config or 'generator_region_aggregator_rules' not in config:
        print("[warn] No generator_region_aggregator_rules in config. Skipping generator aggregation.")
        return network

    rules = config['generator_region_aggregator_rules']
    default_rule = rules.get('others', 'sum')  # Default for unspecified attributes

    # Find all unique combinations
    if group_by_region:
        # Group by (carrier, region)
        network.generators['_group_key'] = (
            network.generators['carrier'].astype(str) + '___' +
            network.generators[region_column].astype(str)
        )
        unique_groups = network.generators[['carrier', region_column, '_group_key']].drop_duplicates()
        print(f"[info] Found {len(network.generators)} generators with {len(unique_groups)} unique (carrier, {region_column}) combinations")
    else:
        # Group by carrier only
        network.generators['_group_key'] = network.generators['carrier'].astype(str)
        unique_groups = network.generators[['carrier', '_group_key']].drop_duplicates()
        unique_groups[region_column] = None  # Add dummy column for consistency
        print(f"[info] Found {len(network.generators)} generators with {len(unique_groups)} unique carriers")

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
    # Track which old generators belong to each new aggregated generator
    group_to_old_gens = {}

    # Process each group
    for _, group_info in unique_groups.iterrows():
        carrier = group_info['carrier']
        region = group_info.get(region_column) if group_by_region else None
        group_key = group_info['_group_key']

        # Skip if carrier is NaN
        if pd.isna(carrier):
            continue

        # Skip if grouping by region and region is NaN
        if group_by_region and pd.isna(region):
            continue

        group_mask = network.generators['_group_key'] == group_key
        gen_names = network.generators.index[group_mask].tolist()
        group_data = network.generators.loc[gen_names]

        if len(gen_names) == 0:
            continue

        if group_by_region:
            print(f"[info] Aggregating {len(gen_names)} generators for carrier '{carrier}' in region '{region}'")
        else:
            print(f"[info] Aggregating {len(gen_names)} generators for carrier '{carrier}'")

        # Find generator with largest p_nom (for 'p_nom' rule)
        largest_gen_idx = group_data['p_nom'].idxmax()

        # Build merged attributes by applying rules
        merged_attrs = {}
        for col in network.generators.columns:
            # Skip the temporary grouping column
            if col == '_group_key':
                continue

            # Get rule for this attribute
            rule = rules.get(col, default_rule)

            # Skip if rule is 'remove' or 'ignore'
            if rule in ['remove', 'ignore']:
                continue

            # Apply rule
            if rule == 'carrier':
                merged_attrs[col] = carrier
            elif rule == 'region':
                # Special: if attribute is 'bus', connect to regional bus
                # Otherwise, use the region value itself
                if col == 'bus':
                    merged_attrs[col] = region
                else:
                    merged_attrs[col] = region
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
                # Fixed value or unknown rule
                # If it's a simple string/number, use it as a fixed value
                # Otherwise, use from largest generator
                if isinstance(rule, (str, int, float)) and rule not in ['carrier', 'region', 'p_nom', 'oldest', 'smallest', 'newest', 'largest', 'sum', 'mean', 'remove', 'ignore']:
                    merged_attrs[col] = rule
                else:
                    merged_attrs[col] = group_data.loc[largest_gen_idx, col]

        # Store merged generator data with key
        merged_generators[group_key] = {
            'attrs': merged_attrs,
            'carrier': carrier,
            'region': region
        }
        # Store mapping from group_key to old generator names
        group_to_old_gens[group_key] = gen_names

    # Store time-series data before removing generators
    # We need to aggregate time-series data (e.g., marginal_cost_t, p_max_pu_t, etc.)
    timeseries_data = {}
    if hasattr(network, 'generators_t'):
        for attr in dir(network.generators_t):
            if attr.startswith('_'):
                continue
            ts_df = getattr(network.generators_t, attr, None)
            if ts_df is None or not hasattr(ts_df, 'columns'):
                continue
            if len(ts_df.columns) > 0:
                # Store the time-series data
                timeseries_data[attr] = ts_df.copy()

    # Remove temporary grouping column
    network.generators.drop(columns=['_group_key'], inplace=True)

    # Remove all old generators
    for gen_name in all_gen_names:
        network.remove("Generator", gen_name)

    # Add aggregated generators
    for group_key, gen_info in merged_generators.items():
        carrier = gen_info['carrier']
        region = gen_info['region']
        merged_attrs = gen_info['attrs']

        # Create merged generator name
        if region is not None:
            merged_name = f"{carrier}_{region}"  # carrier_region format
        else:
            merged_name = f"{carrier}_aggregated"  # carrier_aggregated format

        # Separate standard and custom attrs
        std_attrs = {k: v for k, v in merged_attrs.items() if k in standard_attrs and pd.notna(v)}
        network.add("Generator", merged_name, **std_attrs)

        # Add custom attributes directly to DataFrame
        custom_attrs = {k: v for k, v in merged_attrs.items() if k not in standard_attrs and pd.notna(v)}
        for attr, value in custom_attrs.items():
            network.generators.loc[merged_name, attr] = value

    # Aggregate and assign time-series data to new generators
    if timeseries_data:
        print(f"[info] Aggregating {len(timeseries_data)} time-series attributes...")
        for attr, ts_df in timeseries_data.items():
            # Collect all columns first to avoid DataFrame fragmentation
            new_columns = {}

            for group_key, gen_info in merged_generators.items():
                carrier = gen_info['carrier']
                region = gen_info['region']

                # Create merged generator name (same logic as above)
                if region is not None:
                    merged_name = f"{carrier}_{region}"
                else:
                    merged_name = f"{carrier}_aggregated"

                # Get old generator names for this group
                old_gen_names = group_to_old_gens.get(group_key, [])

                # Filter to only those that exist in the time-series data
                old_gen_names_in_ts = [g for g in old_gen_names if g in ts_df.columns]

                if len(old_gen_names_in_ts) == 0:
                    # No time-series data for this group, skip
                    continue

                # Aggregate time-series data
                # Use mean for most attributes (marginal_cost, efficiency, etc.)
                # Use sum for power outputs (p_set, etc.)
                if attr in ['p_set', 'p_min_pu', 'p_max_pu']:
                    # For power-related attributes, sum across generators
                    new_columns[merged_name] = ts_df[old_gen_names_in_ts].sum(axis=1)
                else:
                    # For other attributes (costs, efficiency), use mean
                    new_columns[merged_name] = ts_df[old_gen_names_in_ts].mean(axis=1)

            # Create DataFrame from all columns at once (avoids fragmentation)
            if len(new_columns) > 0:
                new_ts_df = pd.DataFrame(new_columns, index=ts_df.index)
                setattr(network.generators_t, attr, new_ts_df)
                print(f"[info]   - Aggregated time-series '{attr}' for {len(new_ts_df.columns)} generators")

    # Ensure PyPSA internal consistency after aggregation
    # This is important for PyPSA 1.0+ which has stricter checks
    network.consistency_check()

    if group_by_region:
        print(f"[info] Aggregated into {len(merged_generators)} generators (one per carrier-region combination)")
    else:
        print(f"[info] Aggregated into {len(merged_generators)} generators (one per carrier)")
    return network
