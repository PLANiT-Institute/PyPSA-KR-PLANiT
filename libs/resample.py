"""
Temporal resampling utilities for PyPSA networks.

This module provides functions to resample PyPSA networks to different temporal resolutions
(e.g., from 1-hour to 4-hour snapshots) to reduce computational complexity.
"""
import pypsa


def resample_network(network, weights=1):
    """
    Resample network to coarser temporal resolution using pandas resample.

    This function reduces the temporal resolution of a PyPSA network by resampling
    all time-series data using pandas resample() method. It automatically applies
    appropriate aggregation methods (mean for ratios/prices, sum for energy).

    Parameters:
    -----------
    network : pypsa.Network
        The network to resample
    weights : int
        Temporal aggregation factor in hours. For example:
        - weights=1: No resampling (1-hour snapshots)
        - weights=4: Resample to 4-hour snapshots
        - weights=24: Resample to daily snapshots

    Returns:
    --------
    pypsa.Network
        The resampled network (modified in place, but also returned)

    Examples:
    ---------
    >>> # Resample to 4-hour snapshots
    >>> network = resample_network(network, weights=4)
    >>> # 8760 hourly snapshots -> 2190 4-hourly snapshots

    Notes:
    ------
    - The function modifies the network in place
    - All time-series data is automatically resampled using appropriate aggregation
    - Ratios and per-unit values use mean aggregation
    - Energy and power values use mean aggregation (representing average over period)
    - Costs use mean aggregation
    """
    if weights <= 1:
        # No resampling needed
        return network

    print(f"[info] Resampling network to {weights}-hour snapshots")
    print(f"[info]   Original snapshots: {len(network.snapshots)}")

    # Define resampling rule (e.g., '4H' for 4 hours)
    resample_rule = f'{weights}H'

    # Resample the network snapshots first
    # Convert to DatetimeIndex if it isn't already
    import pandas as pd
    if not isinstance(network.snapshots, pd.DatetimeIndex):
        # If snapshots are just integers or another index type, convert to datetime
        network.snapshots = pd.DatetimeIndex(network.snapshots)

    network.snapshots = network.snapshots.to_series().resample(resample_rule).first().index
    print(f"[info]   Resampled snapshots: {len(network.snapshots)}")

    # Resample all time-series data for generators
    if hasattr(network, 'generators_t'):
        for attr in dir(network.generators_t):
            if not attr.startswith('_'):
                df = getattr(network.generators_t, attr)
                if hasattr(df, 'empty') and not df.empty:
                    # Use mean for all generator time-series attributes
                    setattr(network.generators_t, attr, df.resample(resample_rule).mean())

    # Resample all time-series data for loads
    if hasattr(network, 'loads_t'):
        for attr in dir(network.loads_t):
            if not attr.startswith('_'):
                df = getattr(network.loads_t, attr)
                if hasattr(df, 'empty') and not df.empty:
                    # Use mean for load attributes (represents average power over period)
                    setattr(network.loads_t, attr, df.resample(resample_rule).mean())

    # Resample all time-series data for storage units
    if hasattr(network, 'storage_units_t') and len(network.storage_units) > 0:
        for attr in dir(network.storage_units_t):
            if not attr.startswith('_'):
                df = getattr(network.storage_units_t, attr)
                if hasattr(df, 'empty') and not df.empty:
                    setattr(network.storage_units_t, attr, df.resample(resample_rule).mean())

    # Resample all time-series data for stores
    if hasattr(network, 'stores_t') and len(network.stores) > 0:
        for attr in dir(network.stores_t):
            if not attr.startswith('_'):
                df = getattr(network.stores_t, attr)
                if hasattr(df, 'empty') and not df.empty:
                    setattr(network.stores_t, attr, df.resample(resample_rule).mean())

    # Resample all time-series data for links
    if hasattr(network, 'links_t') and len(network.links) > 0:
        for attr in dir(network.links_t):
            if not attr.startswith('_'):
                df = getattr(network.links_t, attr)
                if hasattr(df, 'empty') and not df.empty:
                    setattr(network.links_t, attr, df.resample(resample_rule).mean())

    # Resample all time-series data for lines
    if hasattr(network, 'lines_t') and len(network.lines) > 0:
        for attr in dir(network.lines_t):
            if not attr.startswith('_'):
                df = getattr(network.lines_t, attr)
                if hasattr(df, 'empty') and not df.empty:
                    setattr(network.lines_t, attr, df.resample(resample_rule).mean())

    # Scale ramp limits by temporal resolution factor
    # Ramp limits are per unit change per time period, so they need to be scaled
    # when the time period changes (e.g., 1h → 4h means ramp limit should be 4× larger)
    ramp_attributes = ['ramp_limit_up', 'ramp_limit_down', 'ramp_limit_start_up', 'ramp_limit_shut_down']

    if len(network.generators) > 0:
        for attr in ramp_attributes:
            if attr in network.generators.columns:
                # Scale ramp limits by weights factor
                network.generators[attr] = network.generators[attr] * weights
                print(f"[info]   Scaled generator {attr} by factor of {weights}")

    if len(network.storage_units) > 0:
        for attr in ramp_attributes:
            if attr in network.storage_units.columns:
                # Scale ramp limits by weights factor
                network.storage_units[attr] = network.storage_units[attr] * weights
                print(f"[info]   Scaled storage_unit {attr} by factor of {weights}")

    print(f"[info] Resampling complete")

    return network


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
