"""
Data mapping functions to apply monthly and snapshot data to network components.
"""
import pandas as pd


def standardize_carrier_names(network, carrier_mapping):
    """
    Standardize carrier names across all network components using carrier mapping.

    This ensures all components use consistent carrier names from the config.
    Updates:
    - network.generators['carrier']
    - network.carriers (adds new carriers, removes unused old ones)
    - Any other components with 'carrier' column

    Should be called BEFORE applying monthly/snapshot data or regional aggregation.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    carrier_mapping : dict
        Mapping from old carrier names to new carrier names (from config)

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    if not carrier_mapping:
        print("[warn] No carrier_mapping provided, skipping carrier standardization")
        return network

    print(f"[info] Standardizing carrier names across all network components...")

    # Collect all unique carriers from the mapping
    old_carriers_in_mapping = set(carrier_mapping.keys())
    new_carriers_in_mapping = set(carrier_mapping.values())

    # Step 1: Update all components with 'carrier' column
    components_updated = {}

    for component_name in ['generators', 'loads', 'storage_units', 'stores', 'links', 'buses']:
        component = getattr(network, component_name, None)
        if component is None or not hasattr(component, 'columns'):
            continue

        if 'carrier' not in component.columns:
            continue

        if len(component) == 0:
            continue

        updated_count = 0
        for idx in component.index:
            old_carrier = component.loc[idx, 'carrier']
            if pd.notna(old_carrier) and old_carrier != '':
                new_carrier = carrier_mapping.get(old_carrier, old_carrier)
                if new_carrier != old_carrier:
                    component.loc[idx, 'carrier'] = new_carrier
                    updated_count += 1

        if updated_count > 0:
            components_updated[component_name] = updated_count

    # Step 2: Update network.carriers table
    # Get all carriers actually used in the network after mapping
    carriers_in_use = set()

    for component_name in ['generators', 'loads', 'storage_units', 'stores', 'links', 'buses']:
        component = getattr(network, component_name, None)
        if component is None or not hasattr(component, 'columns'):
            continue
        if 'carrier' not in component.columns or len(component) == 0:
            continue

        component_carriers = component['carrier'].dropna()
        component_carriers = component_carriers[component_carriers != '']
        carriers_in_use.update(component_carriers.unique())

    # Add new carriers that don't exist yet
    carriers_to_add = carriers_in_use - set(network.carriers.index)
    for carrier in carriers_to_add:
        print(f"[info] Adding new carrier '{carrier}' to network.carriers")
        network.add("Carrier", carrier)

    # Remove old carriers that are no longer used
    carriers_to_remove = set(network.carriers.index) - carriers_in_use
    # Don't remove carriers if they're still referenced (safety check)
    carriers_to_remove = carriers_to_remove & old_carriers_in_mapping

    for carrier in carriers_to_remove:
        if carrier in network.carriers.index:
            print(f"[info] Removing unused carrier '{carrier}' from network.carriers")
            network.remove("Carrier", carrier)

    # Print summary
    print(f"[info] Carrier standardization complete:")
    for component_name, count in components_updated.items():
        print(f"  - Updated {count} {component_name}")
    print(f"  - network.carriers now has: {sorted(network.carriers.index)}")

    return network


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
