"""
Temporal resampling for PyPSA networks using built-in method.
"""
import pandas as pd


def limit_snapshots(network, snapshot_start=None, snapshot_end=None):
    """
    Limit network snapshots to a specific date range.

    Parameters:
    -----------
    network : pypsa.Network
        The network to limit
    snapshot_start : str or None
        Start date in format 'YYYY-MM-DD HH:MM' or None to start from beginning
    snapshot_end : int or None
        Number of snapshots to include, or None for all remaining snapshots

    Returns:
    --------
    pypsa.Network
        The network with limited snapshots (modified in place)
    """
    if snapshot_start is None and snapshot_end is None:
        return network

    print(f"[info] Limiting snapshots")
    print(f"[info]   Original snapshots: {len(network.snapshots)}")

    # Convert snapshots to DatetimeIndex if needed
    if not isinstance(network.snapshots, pd.DatetimeIndex):
        network.snapshots = pd.DatetimeIndex(network.snapshots)

    # Find start index
    if snapshot_start is not None:
        # Parse date with day-first format (international standard: d/m/y)
        start_date = pd.to_datetime(snapshot_start, dayfirst=True)
        # Find the index of the first snapshot >= start_date
        start_idx = network.snapshots.searchsorted(start_date)
        print(f"[info]   Start date: {snapshot_start} -> {start_date} (index: {start_idx})")
    else:
        start_idx = 0

    # Calculate end index
    if snapshot_end is not None:
        end_idx = start_idx + int(snapshot_end)
        print(f"[info]   Number of snapshots: {snapshot_end} (end index: {end_idx})")
    else:
        end_idx = len(network.snapshots)

    # Limit snapshots
    print(f"[DEBUG] Before limiting: len={len(network.snapshots)}, range={network.snapshots[0]} to {network.snapshots[-1]}")
    print(f"[DEBUG] Slicing [{start_idx}:{end_idx}]")
    new_snapshots = network.snapshots[start_idx:end_idx]
    print(f"[DEBUG] After slicing: len={len(new_snapshots)}, range={new_snapshots[0]} to {new_snapshots[-1]}")

    # Limit all temporal data (_t components)
    for attr in dir(network):
        if not attr.endswith('_t'):
            continue

        component = getattr(network, attr)
        if component is None:
            continue

        # Limit each time-series attribute
        for ts_attr in dir(component):
            if ts_attr.startswith('_'):
                continue

            df = getattr(component, ts_attr)
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            # Limit the dataframe to the new snapshot range
            limited_df = df.iloc[start_idx:end_idx]
            setattr(component, ts_attr, limited_df)
            print(f"[info]   {attr}.{ts_attr}: limited ({len(df)} -> {len(limited_df)} snapshots)")

    # Update network snapshots and restore frequency
    network.snapshots = new_snapshots

    # Restore frequency after slicing (slicing loses freq attribute)
    if network.snapshots.freq is None and len(network.snapshots) > 1:
        inferred_freq = pd.infer_freq(network.snapshots)
        if inferred_freq is not None:
            network.snapshots = pd.DatetimeIndex(network.snapshots, freq=inferred_freq)

    print(f"[info]   Limited snapshots: {len(network.snapshots)}")
    print(f"[info]   Limited snapshot range: {network.snapshots[0]} to {network.snapshots[-1]}")
    print(f"[info] Snapshot limiting complete")

    return network


def resample_network(network, weights=1, resample_rules=None, optimization_snapshots=None):
    """
    Resample network using PyPSA's built-in set_snapshots method.

    Parameters:
    -----------
    network : pypsa.Network
        The network to resample
    weights : int
        Temporal aggregation factor in hours (e.g., 4 for 4-hour snapshots)
    resample_rules : pd.DataFrame or None
        DataFrame with resampling rules for static components
    optimization_snapshots : pd.DatetimeIndex or None
        Not used - kept for backwards compatibility

    Returns:
    --------
    pypsa.Network
        The resampled network (network.snapshots already updated)
    """
    if weights <= 1:
        return network

    print(f"[info] Resampling network to {weights}-hour snapshots")
    print(f"[info]   Original snapshots: {len(network.snapshots)}")
    print(f"[info]   Snapshot range: {network.snapshots[0]} to {network.snapshots[-1]}")

    # Convert snapshots to DatetimeIndex if needed
    if not isinstance(network.snapshots, pd.DatetimeIndex):
        network.snapshots = pd.DatetimeIndex(network.snapshots)

    # Manually resample snapshots using pandas
    resample_rule = f'{weights}h'
    print(f"[info]   Resample rule: {resample_rule}")
    new_snapshots = network.snapshots.to_series().resample(resample_rule).first().index
    print(f"[info]   New snapshots count: {len(new_snapshots)}")

    # Manually resample all temporal data to match new snapshots
    for attr in dir(network):
        if not attr.endswith('_t'):
            continue

        component = getattr(network, attr)
        if component is None:
            continue

        for ts_attr in dir(component):
            if ts_attr.startswith('_'):
                continue

            df = getattr(component, ts_attr)
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            # Resample using mean
            if isinstance(df.index, pd.DatetimeIndex):
                resampled_df = df.resample(resample_rule).mean()
                setattr(component, ts_attr, resampled_df)

    # Update network snapshots directly (don't use set_snapshots!)
    network.snapshots = new_snapshots
    print(f"[info]   Resampled snapshots: {len(network.snapshots)}")

    # Resample static component attributes based on resample_rules
    if resample_rules is not None and not resample_rules.empty:
        _resample_static_components(network, resample_rules, weights)

    print(f"[info] Resampling complete")
    return network


def _resample_static_components(network, resample_rules, weights):
    """
    Resample static component attributes based on resample_rules.

    Parameters:
    -----------
    network : pypsa.Network
        The network being modified
    resample_rules : pd.DataFrame
        DataFrame with columns: component, attribute, rule, value
    weights : int
        Temporal aggregation factor
    """
    # Get rules for static components only (not ending with _t)
    static_rules = resample_rules[~resample_rules['component'].str.endswith('_t')]

    if static_rules.empty:
        return

    # Group rules by component
    rules_by_component = {}
    for _, row in static_rules.iterrows():
        component = row['component']
        if component not in rules_by_component:
            rules_by_component[component] = []
        rules_by_component[component].append(row)

    # Process each component
    for component_name, rules in rules_by_component.items():
        if not hasattr(network, component_name):
            continue

        component_df = getattr(network, component_name)
        if len(component_df) == 0:
            continue

        for rule_row in rules:
            attribute = rule_row['attribute']
            rule = rule_row['rule']

            if attribute not in component_df.columns:
                continue

            if rule == 'scale':
                # Scale attribute by weights factor (e.g., ramp_limit_up)
                component_df[attribute] = component_df[attribute] * weights
                print(f"[info]   {component_name}.{attribute}: scaled by {weights}")

            elif rule == 'fixed':
                # Set to fixed value
                fixed_value = rule_row.get('value')
                if fixed_value is not None:
                    component_df[attribute] = fixed_value
                    print(f"[info]   {component_name}.{attribute}: set to {fixed_value}")

            elif rule == 'default':
                # Reset to PyPSA's default value
                from pypsa import Network
                temp_network = Network()
                component_class = getattr(temp_network.components, component_name)
                default_value = component_class.defaults.loc[attribute, 'default']

                # Handle inf/-inf strings
                if isinstance(default_value, str):
                    if default_value == 'inf':
                        default_value = float('inf')
                    elif default_value == '-inf':
                        default_value = float('-inf')

                component_df[attribute] = default_value
                print(f"[info]   {component_name}.{attribute}: reset to PyPSA default ({default_value})")

            elif rule == 'skip':
                continue

            else:
                print(f"[warn] Unknown rule '{rule}' for {component_name}.{attribute}")

