"""
Configurable temporal resampling for PyPSA networks.

This module resamples PyPSA networks based on user-defined rules from configuration.
All resampling behavior is controlled by the 'resample_rules' sheet in config.
"""
import pandas as pd


def resample_network(network, weights=1, resample_rules=None, optimization_snapshots=None):
    """
    Resample network to coarser temporal resolution using configurable rules.

    This function is completely data-driven - all resampling behavior is defined
    in the resample_rules configuration (typically from config_group.xlsx).

    Parameters:
    -----------
    network : pypsa.Network
        The network to resample
    weights : int
        Temporal aggregation factor in hours (e.g., 4 for 4-hour snapshots)
    resample_rules : pd.DataFrame or None
        DataFrame with columns: component, attribute, carrier, rule, value, notes
        If None, no resampling is performed (just return network)
    optimization_snapshots : pd.DatetimeIndex or None
        The snapshots that will be used for optimization (before resampling).
        If provided, returns the resampled version of these snapshots.

    Returns:
    --------
    tuple: (network, resampled_optimization_snapshots) if optimization_snapshots provided
           network only if optimization_snapshots is None

    Resample Rules:
    ---------------
    component: Component name (e.g., 'generators_t', 'generators', 'loads_t')
    attribute: Attribute name (e.g., 'p_max_pu', 'ramp_limit_up', 'e_sum_max', 'e_sum_min')
    carrier: (Optional) Carrier name (e.g., 'solar', 'wind', 'nuclear')
             If specified, rule only applies to components with this carrier.
             If None/empty, applies to all carriers (default rule).
    rule: How to resample - one of:
        - 'mean': Average values over period (default for time-series)
        - 'sum': Sum values over period (for flows/energy)
        - 'max': Take maximum value (conservative)
        - 'min': Take minimum value
        - 'scale': Multiply by weights factor (for per-snapshot rates)
        - 'fixed': Set to fixed value (from 'value' column)
        - 'default': Reset to PyPSA's default value from component definitions
        - 'skip': Do not resample (leave as-is)
    value: Fixed value to use when rule='fixed', otherwise ignored
    notes: Documentation/comments (ignored by code)

    Carrier-Specific Rules:
    -----------------------
    Rules are applied in order: carrier-specific rules override defaults.
    Example:
        - component='generators_t', attribute='p_max_pu', carrier=None, rule='mean'
        - component='generators_t', attribute='p_max_pu', carrier='solar', rule='max'
    Result: Solar uses 'max', all other generators use 'mean'

    Examples:
    ---------
    >>> rules = pd.DataFrame([
    ...     {'component': 'generators_t', 'attribute': 'p_max_pu', 'rule': 'mean'},
    ...     {'component': 'generators', 'attribute': 'ramp_limit_up', 'rule': 'scale'},
    ...     {'component': 'generators', 'attribute': 'e_sum_max', 'rule': 'scale'},
    ... ])
    >>> network = resample_network(network, weights=4, resample_rules=rules)
    """
    if weights <= 1:
        # No resampling needed
        if optimization_snapshots is not None:
            return network, optimization_snapshots
        return network

    if resample_rules is None or resample_rules.empty:
        print("[warn] No resample_rules provided, skipping resampling")
        if optimization_snapshots is not None:
            return network, optimization_snapshots
        return network

    print(f"[info] Resampling network to {weights}-hour snapshots")
    print(f"[info]   Original snapshots: {len(network.snapshots)}")

    # Define resampling rule (e.g., '4H' for 4 hours)
    resample_rule = f'{weights}H'

    # Step 1: Convert snapshots to DatetimeIndex if it isn't already
    if not isinstance(network.snapshots, pd.DatetimeIndex):
        network.snapshots = pd.DatetimeIndex(network.snapshots)

    # Step 2: Manually resample ALL time-series (_t) components BEFORE changing network.snapshots
    # This is critical because PyPSA will fill with default values if we change snapshots first
    _resample_all_time_series(network, resample_rule, resample_rules)

    # Step 3: Now change network.snapshots to match the resampled time-series data
    network.snapshots = network.snapshots.to_series().resample(resample_rule).first().index
    print(f"[info]   Resampled snapshots: {len(network.snapshots)}")

    # Step 4: Process static components (generators, storage_units, etc.)
    rules_by_component = {}
    for _, row in resample_rules.iterrows():
        component = row['component']

        # Only process static components here
        if component.endswith('_t'):
            continue

        if component not in rules_by_component:
            rules_by_component[component] = []
        rules_by_component[component].append(row)

    for component_name, rules in rules_by_component.items():
        _resample_static_component(network, component_name, rules, weights)

    # Resample optimization_snapshots if provided
    resampled_optimization_snapshots = None
    if optimization_snapshots is not None:
        # Create a mapping from original to resampled snapshots
        resampled_optimization_snapshots = pd.DatetimeIndex(optimization_snapshots).to_series().resample(resample_rule).first().index
        print(f"[info]   Resampled optimization snapshots: {len(optimization_snapshots)} -> {len(resampled_optimization_snapshots)}")

    print(f"[info] Resampling complete")

    if optimization_snapshots is not None:
        return network, resampled_optimization_snapshots
    return network


def _resample_all_time_series(network, resample_rule, resample_rules):
    """
    Resample time-series data using pandas resample.

    Simple approach:
    1. Convert index to DatetimeIndex if needed
    2. Apply pandas resample with mean/sum/max/min
    """
    if resample_rules is None or resample_rules.empty:
        return

    # Get rules for time-series components only
    ts_rules = resample_rules[resample_rules['component'].str.endswith('_t')]
    if ts_rules.empty:
        return

    # Build lookup dict
    rule_lookup = {}
    for _, row in ts_rules.iterrows():
        component = row['component']
        attribute = row['attribute']
        rule = row['rule']
        rule_lookup[(component, attribute)] = rule

    # Process each time-series component
    ts_components = ['generators_t', 'loads_t', 'storage_units_t', 'links_t']

    for comp_name in ts_components:
        if not hasattr(network, comp_name):
            continue

        component = getattr(network, comp_name)

        for attr_name in dir(component):
            if attr_name.startswith('_'):
                continue

            attr = getattr(component, attr_name)
            if not isinstance(attr, pd.DataFrame) or attr.empty:
                continue

            # Check if we have a rule
            if (comp_name, attr_name) not in rule_lookup:
                continue

            rule = rule_lookup[(comp_name, attr_name)]
            if rule == 'skip':
                continue

            # Convert index to DatetimeIndex if needed
            if not isinstance(attr.index, pd.DatetimeIndex):
                attr.index = pd.DatetimeIndex(attr.index)

            # Apply pandas resample
            if rule == 'mean':
                resampled = attr.resample(resample_rule).mean()
            elif rule == 'sum':
                resampled = attr.resample(resample_rule).sum()
            elif rule == 'max':
                resampled = attr.resample(resample_rule).max()
            elif rule == 'min':
                resampled = attr.resample(resample_rule).min()
            else:
                continue

            # Update component
            setattr(component, attr_name, resampled)
            print(f"[info]   {comp_name}.{attr_name}: resampled using '{rule}'")


def _resample_static_component(network, component_name, rules, weights):
    """
    Resample static component attributes with carrier-specific rules.

    Parameters:
    -----------
    network : pypsa.Network
        The network being modified
    component_name : str
        Name of the static component (e.g., 'generators', 'storage_units')
    rules : list of dict
        List of rules for this component's attributes
    weights : int
        Temporal aggregation factor
    """
    # Get the component DataFrame (e.g., network.generators)
    if not hasattr(network, component_name):
        return

    component_df = getattr(network, component_name)

    # Check if component has any rows
    if len(component_df) == 0:
        return

    has_carrier = 'carrier' in component_df.columns

    # Group rules by attribute
    rules_by_attr = {}
    for rule_row in rules:
        attribute = rule_row['attribute']
        if attribute not in rules_by_attr:
            rules_by_attr[attribute] = []
        rules_by_attr[attribute].append(rule_row)

    # Process each attribute
    for attribute, attr_rules in rules_by_attr.items():
        # Check if attribute exists
        if attribute not in component_df.columns:
            continue

        # Separate default and carrier-specific rules
        default_rule = None
        carrier_rules = {}

        for rule_row in attr_rules:
            carrier = rule_row.get('carrier')
            if pd.isna(carrier) or carrier is None or carrier == '':
                default_rule = rule_row
            else:
                carrier_rules[carrier] = rule_row

        # Apply rules
        if carrier_rules and has_carrier:
            # Carrier-specific rules exist
            for carrier, carrier_rule in carrier_rules.items():
                mask = component_df['carrier'] == carrier
                _apply_static_rule(component_df, component_name, mask, attribute,
                                   carrier_rule, weights, f"carrier={carrier}")

            # Apply default rule to remaining carriers
            if default_rule is not None:
                handled_carriers = set(carrier_rules.keys())
                mask = ~component_df['carrier'].isin(handled_carriers)
                if mask.any():
                    _apply_static_rule(component_df, component_name, mask, attribute,
                                       default_rule, weights, "default")
        elif default_rule is not None:
            # No carrier-specific rules, apply default to all
            _apply_static_rule(component_df, component_name, None, attribute,
                               default_rule, weights, "all")


def _apply_static_rule(component_df, component_name, mask, attribute, rule_row, weights, scope):
    """Apply a static resampling rule to a DataFrame subset."""
    rule = rule_row['rule']

    if mask is None:
        target_df = component_df
    else:
        target_df = component_df.loc[mask]

    if target_df.empty:
        return

    if rule == 'skip':
        return

    if rule == 'scale':
        component_df.loc[target_df.index, attribute] = target_df[attribute] * weights
        print(f"[info]   {component_name}.{attribute} ({scope}): scaled by {weights}")

    elif rule == 'fixed':
        fixed_value = rule_row.get('value')
        if fixed_value is not None:
            component_df.loc[target_df.index, attribute] = fixed_value
            print(f"[info]   {component_name}.{attribute} ({scope}): set to {fixed_value}")
        else:
            print(f"[warn] {component_name}.{attribute} ({scope}): rule='fixed' but no value provided")

    elif rule == 'max':
        max_value = target_df[attribute].max()
        component_df.loc[target_df.index, attribute] = max_value
        print(f"[info]   {component_name}.{attribute} ({scope}): set to max value {max_value}")

    elif rule == 'min':
        min_value = target_df[attribute].min()
        component_df.loc[target_df.index, attribute] = min_value
        print(f"[info]   {component_name}.{attribute} ({scope}): set to min value {min_value}")

    elif rule == 'default':
        # Reset the attribute to PyPSA's default value
        # Get the default from PyPSA's component definitions - NO HARDCODED FALLBACKS
        from pypsa import Network

        temp_network = Network()
        component_class = getattr(temp_network.components, component_name)
        default_value = component_class.defaults.loc[attribute, 'default']

        # Handle inf/-inf if they come as strings from PyPSA
        if isinstance(default_value, str):
            if default_value == 'inf':
                default_value = float('inf')
            elif default_value == '-inf':
                default_value = float('-inf')

        component_df.loc[target_df.index, attribute] = default_value
        print(f"[info]   {component_name}.{attribute} ({scope}): reset to PyPSA default ({default_value})")

    else:
        print(f"[warn] Unknown rule '{rule}' for {component_name}.{attribute} ({scope})")


def get_optimization_snapshots(network, snapshot_start=0, snapshot_end=None, weights=1):
    """
    Get the snapshot range for optimization, accounting for resampling.

    Parameters:
    -----------
    network : pypsa.Network
        The network (should already be resampled if weights > 1)
    snapshot_start : int
        Starting snapshot index (in original resolution)
    snapshot_end : int or None
        Ending snapshot index (in original resolution). If None, uses all snapshots.
    weights : int
        Temporal aggregation factor used for resampling

    Returns:
    --------
    pd.DatetimeIndex
        The snapshots to use for optimization

    Examples:
    ---------
    >>> # Get first 480 hours with 4-hour resampling
    >>> snapshots = get_optimization_snapshots(network, 0, 480, weights=4)
    >>> # Returns 120 snapshots (480 / 4)
    """
    if snapshot_end is None:
        snapshot_end = len(network.snapshots) * weights

    if weights > 1:
        # Adjust snapshot indices for resampled data
        adjusted_start = snapshot_start // weights
        adjusted_end = snapshot_end // weights
        optimization_snapshots = network.snapshots[adjusted_start:adjusted_end]
        print(f"[info] Using snapshots {snapshot_start}:{snapshot_end} (original) = "
              f"{adjusted_start}:{adjusted_end} (resampled, {len(optimization_snapshots)} snapshots)")
    else:
        optimization_snapshots = network.snapshots[snapshot_start:snapshot_end]
        print(f"[info] Using snapshots {snapshot_start}:{snapshot_end} ({len(optimization_snapshots)} snapshots)")

    return optimization_snapshots
