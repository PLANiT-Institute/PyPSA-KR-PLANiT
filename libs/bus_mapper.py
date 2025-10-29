"""
Bus mapping functions for PyPSA networks.
"""


def map_buses(network, config, mapping_type='single', region_column='region'):
    """
    Map network components to buses based on mapping type.

    This function maps all network components to buses. It handles both single-bus
    mapping (all components to one national bus) and regional mapping (components
    grouped by region column). After remapping, old buses are removed.

    Parameters:
    -----------
    network : pypsa.Network
        Network to map
    config : dict
        Configuration dictionary containing regional_settings
    mapping_type : str
        Type of mapping: 'single' for single national bus, or a column name like
        'region', 'province', 'state' for regional mapping
    region_column : str
        (Deprecated - use mapping_type instead) Column name for regional mapping

    Returns:
    --------
    pypsa.Network : Mapped network (modified in-place and returned)
    """
    print(f"Original number of buses: {len(network.buses)}")

    # Store old buses to remove later
    old_buses = list(network.buses.index)

    if mapping_type == 'single':
        # Map all components to single national bus
        target_bus = config['regional_settings']['national_region']
        print(f"Mapping all components to single national bus: {target_bus}")

        # Map all components to the target bus
        for component in network.iterate_components():
            if component.name == 'Bus':
                continue
            if 'bus' in component.df.columns:
                component.df['bus'] = target_bus
            if 'bus0' in component.df.columns:
                component.df['bus0'] = target_bus
            if 'bus1' in component.df.columns:
                component.df['bus1'] = target_bus

        # Add the target bus if it doesn't exist
        if target_bus not in network.buses.index:
            network.add("Bus", target_bus)

        # Remove all old buses except target_bus
        buses_to_remove = [bus for bus in old_buses if bus != target_bus]
        if buses_to_remove:
            network.mremove("Bus", buses_to_remove)

        print(f"All components mapped to single bus: {target_bus}")
        print(f"Final number of buses: {len(network.buses)}")

    else:
        # Map components to regional buses based on region column
        region_col = mapping_type
        print(f"Mapping network buses by region column: '{region_col}'")

        # Collect all unique regions from components
        regions = set()
        for component in network.iterate_components():
            if component.name == 'Bus':
                continue
            if region_col in component.df.columns:
                component_regions = component.df[region_col].dropna().unique()
                regions.update(component_regions)

        regions = sorted(list(regions))
        print(f"Found {len(regions)} unique regions: {regions}")

        # Map components to regional buses
        for component in network.iterate_components():
            if component.name == 'Bus':
                continue
            if region_col not in component.df.columns:
                print(f"Warning: Component '{component.name}' does not have '{region_col}' column, skipping")
                continue

            # For components with 'bus' column
            if 'bus' in component.df.columns:
                component.df['bus'] = component.df[region_col]

            # For components with 'bus0' and 'bus1' (like lines, links)
            if 'bus0' in component.df.columns:
                component.df['bus0'] = component.df[region_col]
            if 'bus1' in component.df.columns:
                component.df['bus1'] = component.df[region_col]

        # Add new regional buses
        for region in regions:
            if region not in network.buses.index:
                network.add("Bus", region)

        # Remove old buses
        buses_to_remove = [bus for bus in old_buses if bus not in regions]
        if buses_to_remove:
            network.mremove("Bus", buses_to_remove)

        print(f"Network buses mapped to {len(regions)} regional buses")
        print(f"Final number of buses: {len(network.buses)}")

    return network
