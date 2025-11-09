"""
Functions to apply temporal (time-varying) data to network components.

This module handles loading and applying monthly and snapshot-level
time-series data to PyPSA network components.
"""
import pandas as pd


def apply_monthly_data_to_network(network, config, monthly_df):
    """
    Apply monthly data to network components dynamically.
    Matches generators by carrier and region/province/name based on aggregation level.
    Uses snapshot, carrier, components, components_t, attribute, value, status, region, aggregation columns.

    This function does NOT modify carrier names - it matches carriers AS-IS.
    Both network and data should have the same carrier names (original names from data files).

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    config : dict
        Configuration dictionary
    monthly_df : pd.DataFrame
        Monthly data with columns: snapshot, carrier, components, components_t, attribute, value, status, region, aggregation

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    national_region = config['regional_settings']['national_region']

    # Filter only active (TRUE) status records
    active_df = monthly_df[monthly_df['status'] == True].copy()

    # Get network snapshots and create year-month mapping
    snapshots = network.snapshots

    # Convert snapshots to datetime if they're strings, otherwise use as-is
    if isinstance(snapshots[0], str):
        snapshots_dt = pd.to_datetime(snapshots, dayfirst=True)
    else:
        snapshots_dt = pd.DatetimeIndex(snapshots)

    snapshot_months = pd.DataFrame({
        'snapshot': snapshots,
        'year_month': snapshots_dt.to_period('M')
    })

    # Add year-month to monthly data
    active_df['year_month'] = active_df['snapshot'].dt.to_period('M')

    # Group by components, components_t, attribute, and aggregation
    for (component_name, component_t_name, attribute, aggregation_level), group in active_df.groupby(['components', 'components_t', 'attribute', 'aggregation']):

        # Get the component objects directly from network
        component = getattr(network, component_name, None)
        component_t = getattr(network, component_t_name, None)

        if component is None or component_t is None:
            print(f"Component '{component_name}' or '{component_t_name}' not found in network")
            continue

        # Collect all columns data first
        columns_data = {}

        # Process each item in the component
        for item_idx in component.index:
            item_carrier = component.loc[item_idx, 'carrier']
            item_province = component.loc[item_idx, 'province'] if 'province' in component.columns else None

            # Match carrier directly (no mapping)
            carrier_data = group[group['carrier'] == item_carrier].copy()

            if not carrier_data.empty:
                region_data = pd.DataFrame()

                if aggregation_level == 'national':
                    # Use national-level data
                    region_data = carrier_data[carrier_data['region'] == national_region]
                elif aggregation_level == 'province':
                    # Match by province
                    if item_province:
                        region_data = carrier_data[carrier_data['region'] == item_province]
                elif aggregation_level == 'generator':
                    # Match by generator name
                    if 'name' in carrier_data.columns:
                        generator_data = carrier_data[carrier_data['name'] == item_idx]
                        if not generator_data.empty:
                            region_data = generator_data
                        elif item_province:
                            # Fallback to province
                            region_data = carrier_data[carrier_data['region'] == item_province]

                if not region_data.empty:
                    merged = snapshot_months.merge(
                        region_data[['year_month', 'value']],
                        on='year_month',
                        how='left'
                    )
                    merged['value'] = merged['value'].ffill()
                    columns_data[item_idx] = merged['value'].values

        # Create the DataFrame all at once
        if columns_data:
            attr_df = pd.DataFrame(columns_data, index=snapshots)
            attr_df.index.name = 'snapshot'
            setattr(component_t, attribute, attr_df)

    return network


def apply_snapshot_data_to_network(network, config, snapshot_df):
    """
    Apply snapshot-level data to network components.
    Matches generators by carrier and region/province/name based on aggregation level.
    Uses snapshot, carrier, region, aggregation, components, components_t, attribute, value, status columns.

    This function does NOT modify carrier names - it matches carriers AS-IS.
    Both network and data should have the same carrier names (original names from data files).

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    config : dict
        Configuration dictionary
    snapshot_df : pd.DataFrame
        Snapshot data with columns: snapshot, carrier, region, aggregation, components, components_t, attribute, value, status

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    national_region = config['regional_settings']['national_region']

    # Filter only active (TRUE) status records
    active_df = snapshot_df[snapshot_df['status'] == True].copy()

    # Get network snapshots and ensure they're datetime
    snapshots = network.snapshots
    if isinstance(snapshots[0], str):
        snapshots_dt = pd.to_datetime(snapshots, dayfirst=True)
    else:
        snapshots_dt = pd.DatetimeIndex(snapshots)

    # Group by components, components_t, attribute, and aggregation level
    for (component_name, component_t_name, attribute, aggregation_level), group in active_df.groupby(['components', 'components_t', 'attribute', 'aggregation']):

        # Get the component objects directly from network
        component = getattr(network, component_name, None)
        component_t = getattr(network, component_t_name, None)

        if component is None or component_t is None:
            print(f"Component '{component_name}' or '{component_t_name}' not found in network")
            continue

        # Collect all columns data first
        columns_data = {}

        # Process each item in the component
        for item_idx in component.index:
            item_carrier = component.loc[item_idx, 'carrier']
            item_province = component.loc[item_idx, 'province'] if 'province' in component.columns else None

            # Match carrier directly (no mapping)
            carrier_data = group[group['carrier'] == item_carrier]

            if not carrier_data.empty:
                region_data = pd.DataFrame()

                if aggregation_level == 'national':
                    # Use national-level data
                    region_data = carrier_data[carrier_data['region'] == national_region]
                elif aggregation_level == 'province':
                    # Match by province
                    if item_province:
                        region_data = carrier_data[carrier_data['region'] == item_province]
                elif aggregation_level == 'generator':
                    # Match by generator name
                    if 'name' in carrier_data.columns:
                        generator_data = carrier_data[carrier_data['name'] == item_idx]
                        if not generator_data.empty:
                            region_data = generator_data
                        elif item_province:
                            # Fallback to province
                            region_data = carrier_data[carrier_data['region'] == item_province]

                if not region_data.empty:
                    merged = pd.DataFrame({'snapshot': snapshots_dt}).merge(
                        region_data[['snapshot', 'value']],
                        on='snapshot',
                        how='left'
                    )
                    columns_data[item_idx] = merged['value'].values

        # Create the DataFrame all at once
        if columns_data:
            attr_df = pd.DataFrame(columns_data, index=snapshots)
            attr_df.index.name = 'snapshot'
            setattr(component_t, attribute, attr_df)

    return network
