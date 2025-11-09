"""
Functions to set generator dispatch (p_set) based on p_nom and p_max_pu.

This creates a fixed dispatch profile for generators instead of optimizing.
Useful for scenarios where generation is predetermined (e.g., must-run contracts,
renewable curtailment analysis, or validating against historical dispatch).
"""
import pandas as pd


def set_generator_p_set(network, carrier_list=None, snapshots=None):
    """
    Set generator p_set (fixed dispatch) by multiplying p_nom × p_max_pu.

    Only sets p_set for generators that have time-varying p_max_pu data
    (i.e., generators_t.p_max_pu). Static p_max_pu is ignored.

    Formula:
        p_set[generator, snapshot] = p_nom[generator] × generators_t.p_max_pu[generator, snapshot]

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    carrier_list : list of str or None
        List of carrier names to set p_set for. If None, applies to ALL generators
        that have time-varying p_max_pu.
        Example: ['solar', 'wind'] for renewables only
    snapshots : pd.Index or None
        Snapshots to apply p_set to. If None, uses all network snapshots.

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)

    Notes:
    ------
    - Only generators with time-varying p_max_pu (generators_t.p_max_pu) get p_set
    - Static p_max_pu (generators.p_max_pu) is NOT used
    - Generators with p_set become must-run (not optimized)
    - p_max_pu columns are removed for generators that get p_set

    Examples:
    --------
    >>> # Set p_set for ALL generators with time-varying p_max_pu
    >>> network = set_generator_p_set(network)
    >>>
    >>> # Set p_set only for solar and wind (if they have p_max_pu data)
    >>> network = set_generator_p_set(network, carrier_list=['solar', 'wind'])
    """
    if snapshots is None:
        snapshots = network.snapshots

    # Check if time-varying p_max_pu exists
    if not hasattr(network.generators_t, 'p_max_pu') or network.generators_t.p_max_pu is None:
        print("[warn] No generators_t.p_max_pu found. No p_set will be created.")
        print("[warn] Note: Static p_max_pu (generators.p_max_pu) is not used by this function.")
        return network

    p_max_pu = network.generators_t.p_max_pu.loc[snapshots]

    if p_max_pu.empty or len(p_max_pu.columns) == 0:
        print("[warn] generators_t.p_max_pu has no columns. No p_set will be created.")
        return network

    # Determine which generators to process
    if carrier_list is None:
        # Use ALL generators that have p_max_pu data
        selected_gens = [gen for gen in p_max_pu.columns if gen in network.generators.index]
        print(f"[info] Setting p_set for ALL generators with time-varying p_max_pu...")
    else:
        # Filter by carrier AND must have p_max_pu data
        carrier_gens = network.generators[
            network.generators['carrier'].isin(carrier_list)
        ].index
        selected_gens = [gen for gen in carrier_gens if gen in p_max_pu.columns]
        print(f"[info] Setting p_set for carriers: {carrier_list}")

    if len(selected_gens) == 0:
        if carrier_list is None:
            print("[warn] No generators found with time-varying p_max_pu")
        else:
            print(f"[warn] No generators found for carriers {carrier_list} with time-varying p_max_pu")
        return network

    print(f"[info] Found {len(selected_gens)} generators with time-varying p_max_pu")

    # Get p_nom for selected generators
    p_nom = network.generators.loc[selected_gens, 'p_nom']

    # Calculate p_set = p_nom × p_max_pu
    p_set_data = pd.DataFrame(
        index=snapshots,
        columns=selected_gens,
        dtype=float
    )

    for gen in selected_gens:
        p_set_data[gen] = p_nom[gen] * p_max_pu[gen]

    # Initialize or update p_set
    if not hasattr(network.generators_t, 'p_set') or network.generators_t.p_set is None:
        # Create new p_set with NaN for non-selected generators
        network.generators_t.p_set = pd.DataFrame(
            index=snapshots,
            columns=network.generators.index,
            dtype=float
        )

    # Update p_set for selected generators
    network.generators_t.p_set.loc[snapshots, selected_gens] = p_set_data

    # Remove p_max_pu columns for generators with p_set (p_set takes precedence)
    cols_to_drop = [gen for gen in selected_gens if gen in network.generators_t.p_max_pu.columns]
    if cols_to_drop:
        network.generators_t.p_max_pu = network.generators_t.p_max_pu.drop(columns=cols_to_drop)
        print(f"[info] Removed p_max_pu for {len(cols_to_drop)} generators (p_set takes precedence)")

    # Show breakdown by carrier
    if carrier_list is not None:
        print(f"[info] Breakdown by carrier:")
        for carrier in carrier_list:
            carrier_gens_with_pset = network.generators[
                (network.generators['carrier'] == carrier) &
                (network.generators.index.isin(selected_gens))
            ]
            if len(carrier_gens_with_pset) > 0:
                total_capacity = carrier_gens_with_pset['p_nom'].sum()
                print(f"  - {carrier}: {len(carrier_gens_with_pset)} generators, {total_capacity:.2f} MW total")

    # Show summary statistics
    mean_dispatch = p_set_data.mean().mean()
    max_dispatch = p_set_data.max().max()
    min_dispatch = p_set_data.min().min()

    print(f"[info] Created p_set for {len(selected_gens)} generators × {len(snapshots)} snapshots")
    print(f"[info] Dispatch statistics:")
    print(f"  - Mean: {mean_dispatch:.2f} MW")
    print(f"  - Max:  {max_dispatch:.2f} MW")
    print(f"  - Min:  {min_dispatch:.2f} MW")

    return network


def clear_generator_p_set(network):
    """
    Remove p_set from generators, making them dispatchable again.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    if hasattr(network.generators_t, 'p_set') and network.generators_t.p_set is not None:
        print("[info] Removing generators_t.p_set")
        network.generators_t.p_set = None
        print("[info] All generators are now dispatchable (optimizable)")
    else:
        print("[info] No p_set to remove")

    return network
