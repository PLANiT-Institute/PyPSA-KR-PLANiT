"""
Data mapping functions to apply monthly and snapshot data to network components.
"""
import pandas as pd


def apply_monthly_data_to_network(network, config, monthly_df):
    """
    Apply monthly data to network components dynamically.
    Uses snapshot, carrier, components, components_t, attribute, value, and status columns from monthly_df.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object
    config : dict
        Configuration dictionary
    monthly_df : pd.DataFrame
        Monthly data with columns: snapshot, carrier, components, components_t, attribute, value, status
    """
    carrier_mapping = config['carrier_mapping']

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

    # Group by components, components_t, and attribute
    for (component_name, component_t_name, attribute), group in active_df.groupby(['components', 'components_t', 'attribute']):

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
            monthly_carrier = carrier_mapping.get(item_carrier)

            if monthly_carrier:
                carrier_data = group[group['carrier'] == monthly_carrier]
                if not carrier_data.empty:
                    merged = snapshot_months.merge(
                        carrier_data[['year_month', 'value']],
                        on='year_month',
                        how='left'
                    )
                    merged['value'] = merged['value'].ffill()
                    columns_data[item_idx] = merged['value'].values

        # Create the DataFrame all at once
        if columns_data:
            attr_df = pd.DataFrame(columns_data, index=snapshots)
            setattr(component_t, attribute, attr_df)


def apply_snapshot_data_to_network(network, config, snapshot_df):
    """
    Apply snapshot-level data to network components with regional aggregation.
    Uses snapshot, carrier, region, aggregation, components, components_t, attribute, value, and status columns.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object
    config : dict
        Configuration dictionary with regional_aggregation settings
    snapshot_df : pd.DataFrame
        Snapshot data with columns: snapshot, carrier, region, aggregation, components, components_t, attribute, value, status
    """
    carrier_mapping = config['carrier_mapping']
    regional_agg_config = config['regional_aggregation']
    national_region = regional_agg_config['national_region']
    agg_methods = regional_agg_config['aggregation_methods']

    # Filter only active (TRUE) status records
    active_df = snapshot_df[snapshot_df['status'] == True].copy()

    # Get network snapshots
    snapshots = network.snapshots

    # Group by components, components_t, attribute, and aggregation level
    for (component_name, component_t_name, attribute, aggregation_level), group in active_df.groupby(['components', 'components_t', 'attribute', 'aggregation']):

        # Get the component objects directly from network
        component = getattr(network, component_name, None)
        component_t = getattr(network, component_t_name, None)

        if component is None or component_t is None:
            print(f"Component '{component_name}' or '{component_t_name}' not found in network")
            continue

        # Determine aggregation method
        agg_key = f"{component_name}.{attribute}"
        agg_method = agg_methods[agg_key]

        # Collect all columns data first
        columns_data = {}

        # Process each item in the component
        for item_idx in component.index:
            item_carrier = component.loc[item_idx, 'carrier']
            mapped_carrier = carrier_mapping.get(item_carrier)

            if mapped_carrier:
                carrier_data = group[group['carrier'] == mapped_carrier]
                if not carrier_data.empty:
                    if aggregation_level == 'national':
                        national_data = carrier_data[carrier_data['region'] == national_region]
                        if not national_data.empty:
                            merged = pd.DataFrame({'snapshot': snapshots}).merge(
                                national_data[['snapshot', 'value']],
                                on='snapshot',
                                how='left'
                            )
                            columns_data[item_idx] = merged['value'].values
                    else:
                        if agg_method == 'sum':
                            agg_data = carrier_data.groupby('snapshot')['value'].sum().reset_index()
                        elif agg_method == 'mean':
                            agg_data = carrier_data.groupby('snapshot')['value'].mean().reset_index()
                        elif agg_method == 'median':
                            agg_data = carrier_data.groupby('snapshot')['value'].median().reset_index()
                        else:
                            agg_data = None

                        if agg_data is not None:
                            merged = pd.DataFrame({'snapshot': snapshots}).merge(
                                agg_data,
                                on='snapshot',
                                how='left'
                            )
                            columns_data[item_idx] = merged['value'].values

        # Create the DataFrame all at once
        if columns_data:
            attr_df = pd.DataFrame(columns_data, index=snapshots)
            setattr(component_t, attribute, attr_df)
