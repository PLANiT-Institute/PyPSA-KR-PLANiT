"""
Functions to apply energy constraints based on capacity factors.

This module converts capacity factor limits (max_cf, min_cf) into
energy sum constraints (e_sum_max, e_sum_min) for generators.
"""
import pandas as pd


def apply_cf_energy_constraints(network, generator_attributes, snapshots=None):
    """
    Apply energy sum constraints based on capacity factor limits.

    Converts max_cf and min_cf from generator_attributes into e_sum_max and e_sum_min
    for the specified snapshots.

    Formula:
    --------
    e_sum_max = p_nom × max_cf × num_hours
    e_sum_min = p_nom × min_cf × num_hours

    Where num_hours is the number of snapshots (assuming hourly resolution).

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    generator_attributes : dict
        Generator attributes from config, containing max_cf and min_cf by carrier
    snapshots : pd.Index or None
        Snapshots for which to calculate energy constraints.
        If None, uses all network snapshots.

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

    # Number of hours in the snapshot period (assuming hourly resolution)
    num_hours = len(snapshots)

    print(f"[info] Applying capacity factor energy constraints for {num_hours} snapshots...")

    # Initialize columns if they don't exist
    if 'e_sum_max' not in network.generators.columns:
        network.generators['e_sum_max'] = float('inf')
    if 'e_sum_min' not in network.generators.columns:
        network.generators['e_sum_min'] = 0.0

    # Track statistics
    constraints_applied = []

    # Process each carrier
    for carrier, attributes in generator_attributes.items():
        if carrier == 'default':
            continue

        # Get generators for this carrier
        carrier_gens = network.generators[network.generators['carrier'] == carrier].index

        if len(carrier_gens) == 0:
            continue

        # Apply max_cf constraint
        if 'max_cf' in attributes and pd.notna(attributes['max_cf']):
            max_cf = attributes['max_cf']
            for gen in carrier_gens:
                p_nom = network.generators.loc[gen, 'p_nom']
                e_sum_max = p_nom * max_cf * num_hours
                network.generators.loc[gen, 'e_sum_max'] = e_sum_max

            total_p_nom = network.generators.loc[carrier_gens, 'p_nom'].sum()
            total_e_max = total_p_nom * max_cf * num_hours
            constraints_applied.append(f"  {carrier}: max_cf={max_cf:.2f} → e_sum_max={total_e_max:.0f} MWh total")

        # Apply min_cf constraint
        if 'min_cf' in attributes and pd.notna(attributes['min_cf']):
            min_cf = attributes['min_cf']
            for gen in carrier_gens:
                p_nom = network.generators.loc[gen, 'p_nom']
                e_sum_min = p_nom * min_cf * num_hours
                network.generators.loc[gen, 'e_sum_min'] = e_sum_min

            total_p_nom = network.generators.loc[carrier_gens, 'p_nom'].sum()
            total_e_min = total_p_nom * min_cf * num_hours
            constraints_applied.append(f"  {carrier}: min_cf={min_cf:.2f} → e_sum_min={total_e_min:.0f} MWh total")

    if constraints_applied:
        print(f"[info] Applied energy constraints to {len(constraints_applied)} carrier groups:")
        for msg in constraints_applied:
            print(msg)
    else:
        print("[info] No capacity factor energy constraints found in generator_attributes")

    return network
