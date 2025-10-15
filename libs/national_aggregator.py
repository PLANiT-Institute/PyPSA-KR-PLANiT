"""
National aggregation functions for PyPSA networks.
"""


def aggregate_to_national_level(network):
    """
    Aggregate multi-regional network to national level by consolidating all components to one bus.

    Parameters:
    -----------
    network : pypsa.Network
        Network to aggregate

    Returns:
    --------
    pypsa.Network : Aggregated network (modified in-place and returned)
    """
    # Get the single bus to use for the entire network
    national_bus = network.buses.index[0]
    print(f"Aggregating network to national level using bus: {national_bus}")

    # Convert all components to use the national bus
    for component in network.iterate_components():
        if 'bus' in component.df.columns:
            component.df['bus'] = national_bus
        if 'bus0' in component.df.columns:
            component.df['bus0'] = national_bus
        if 'bus1' in component.df.columns:
            component.df['bus1'] = national_bus

    print("Network aggregated to national level")
    return network
