"""
Load scaling function to adjust loads based on target total load.
"""
import pandas as pd


def scale_loads_to_target(network, target_load):
    """
    Scale all loads proportionally to match target total load.

    Formula: new_load = (target_load / current_total_load) * current_load

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with loads
    target_load : float or None
        Target total load (sum of all loads across all snapshots)
        If None, no scaling is applied

    Returns:
    --------
    pypsa.Network : Modified network with scaled loads
    """
    if target_load is None or target_load <= 0:
        print("[info] No target_load specified or invalid value, skipping load scaling")
        return network

    if not hasattr(network, 'loads_t') or not hasattr(network.loads_t, 'p_set'):
        print("[warn] No loads_t.p_set found in network, skipping load scaling")
        return network

    loads_p_set = network.loads_t.p_set

    if loads_p_set.empty:
        print("[warn] loads_t.p_set is empty, skipping load scaling")
        return network

    # Calculate current total load
    current_total_load = loads_p_set.sum().sum()

    if current_total_load == 0:
        print("[warn] Current total load is zero, cannot scale")
        return network

    # Calculate scaling factor
    scaling_factor = target_load / current_total_load

    # Scale all loads
    network.loads_t.p_set = loads_p_set * scaling_factor

    print(f"[info] Scaled loads from {current_total_load:,.0f} to {target_load:,.0f} (factor: {scaling_factor:.4f})")

    return network
