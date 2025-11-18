"""
Functions to apply energy constraints based on capacity factors.

This module converts capacity factor limits (max_cf, min_cf) into
energy sum constraints (e_sum_max, e_sum_min) for generators.
"""
import pandas as pd


def apply_cf_energy_constraints(network, generator_attributes, snapshots=None, snapshot_weightings=None):
    """
    Apply energy sum constraints based on capacity factor limits.

    Converts max_cf and min_cf from generator_attributes into e_sum_max and e_sum_min
    for the specified snapshots.

    Formula:
    --------
    e_sum_max = p_nom × max_cf × total_hours
    e_sum_min = p_nom × min_cf × total_hours

    Where total_hours is calculated from snapshot weightings (duration of each snapshot).

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    generator_attributes : dict
        Generator attributes from config, containing max_cf and min_cf by carrier
    snapshots : pd.Index or None
        Snapshots for which to calculate energy constraints.
        If None, uses all network snapshots.
    snapshot_weightings : pd.Series or None
        Duration of each snapshot in hours. If None, infers from snapshot frequency.

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)

    Example:
    --------
    >>> # After defining optimization_snapshots
    >>> network = apply_cf_energy_constraints(network, generator_attributes, optimization_snapshots)
    """
    if snapshots is None:
        snapshots = network.snapshots

    # Calculate total hours from snapshot weightings
    if snapshot_weightings is not None:
        total_hours = snapshot_weightings.sum()
    elif hasattr(network, 'snapshot_weightings') and not network.snapshot_weightings.empty:
        # Use network's snapshot weightings if available
        total_hours = network.snapshot_weightings.loc[snapshots, 'generators'].sum()
    else:
        # Infer from snapshot frequency (time between snapshots)
        if len(snapshots) > 1:
            # Calculate time difference between first two snapshots
            freq = (snapshots[1] - snapshots[0]).total_seconds() / 3600  # convert to hours
            total_hours = len(snapshots) * freq
        else:
            # Single snapshot, assume 1 hour
            total_hours = 1.0

    print(f"[info] Applying capacity factor energy constraints for {len(snapshots)} snapshots ({total_hours:.1f} total hours)...")

    # Initialize columns if they don't exist
    if 'e_sum_max' not in network.generators.columns:
        network.generators['e_sum_max'] = float('inf')
    if 'e_sum_min' not in network.generators.columns:
        network.generators['e_sum_min'] = 0.0

    generator_attributes = generator_attributes or {}
    default_attrs = generator_attributes.get('default') or {}

    def _resolve_cf(primary, fallback):
        if primary is not None and pd.notna(primary):
            return primary, 'carrier'
        if fallback is not None and pd.notna(fallback):
            return fallback, 'default'
        return None, None

    # Track statistics
    constraints_applied = []

    # Process each carrier that actually exists in the network
    carriers_in_network = [
        carrier for carrier in network.generators['carrier'].unique()
        if pd.notna(carrier)
    ]

    for carrier in carriers_in_network:
        attributes = generator_attributes.get(carrier, {})

        # Get generators for this carrier
        carrier_gens = network.generators[network.generators['carrier'] == carrier].index

        if len(carrier_gens) == 0:
            continue

        max_cf, max_source = _resolve_cf(attributes.get('max_cf'), default_attrs.get('max_cf'))
        min_cf, min_source = _resolve_cf(attributes.get('min_cf'), default_attrs.get('min_cf'))

        if max_cf is not None:
            for gen in carrier_gens:
                p_nom = network.generators.loc[gen, 'p_nom']
                e_sum_max = p_nom * max_cf * total_hours
                network.generators.loc[gen, 'e_sum_max'] = e_sum_max

            total_p_nom = network.generators.loc[carrier_gens, 'p_nom'].sum()
            total_e_max = total_p_nom * max_cf * total_hours
            source_label = 'carrier-specific' if max_source == 'carrier' else 'default'
            constraints_applied.append(
                f"  {carrier}: max_cf={max_cf:.2f} ({source_label}) → e_sum_max={total_e_max:.0f} MWh total"
            )

        if min_cf is not None:
            for gen in carrier_gens:
                p_nom = network.generators.loc[gen, 'p_nom']
                e_sum_min = p_nom * min_cf * total_hours
                network.generators.loc[gen, 'e_sum_min'] = e_sum_min

            total_p_nom = network.generators.loc[carrier_gens, 'p_nom'].sum()
            total_e_min = total_p_nom * min_cf * total_hours
            source_label = 'carrier-specific' if min_source == 'carrier' else 'default'
            constraints_applied.append(
                f"  {carrier}: min_cf={min_cf:.2f} ({source_label}) → e_sum_min={total_e_min:.0f} MWh total"
            )

    if constraints_applied:
        print(f"[info] Applied energy constraints to {len(constraints_applied)} carrier groups:")
        for msg in constraints_applied:
            print(msg)
    else:
        print("[info] No capacity factor energy constraints found in generator_attributes")

    return network
