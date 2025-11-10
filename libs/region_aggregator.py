"""
Region-based network aggregation functions.

Aggregates PyPSA network components (buses, generators, lines, loads) by geographical regions.
"""

import pandas as pd
import numpy as np
from pathlib import Path


# Mapping of component table attributes to the dimension names expected by PyPSA.
# PyPSA 1.0+ uses "name" for component indices
_COMPONENT_INDEX_NAME = "name"

# But time-series columns still use component-specific names
_COMPONENT_TS_COLUMN_NAMES = {
    "buses": "Bus",
    "loads": "Load",
    "generators": "Generator",
    "lines": "Line",
    "links": "Link",
    "stores": "Store",
    "storage_units": "StorageUnit",
    "transformers": "Transformer",
    "shunt_impedances": "ShuntImpedance",
    "global_constraints": "GlobalConstraint",
}


def _ensure_named_dimensions(network):
    """
    Ensure component indices and snapshots carry explicit dimension names.

    PyPSA 1.0+ requires:
    - Component static indices to have name="name"
    - Time-series indices to have name="snapshot"
    - Time-series columns to have component-specific names (e.g., "Generator", "Load")
    """

    # Ensure snapshot index is named - PyPSA defaults to 'snapshot'
    if hasattr(network.snapshots, "name") and not network.snapshots.name:
        network.snapshots.name = "snapshot"

    # Snapshot weightings should mirror snapshot naming for consistency
    if hasattr(network.snapshot_weightings.index, "name") and not network.snapshot_weightings.index.name:
        network.snapshot_weightings.index.name = "snapshot"

    # Restore the canonical index name for each component table
    for attr in _COMPONENT_TS_COLUMN_NAMES.keys():
        component_df = getattr(network, attr, None)
        if component_df is None:
            continue
        index = getattr(component_df, "index", None)
        if index is None:
            continue
        # PyPSA 1.0+ uses "name" for all component indices
        if index.name != _COMPONENT_INDEX_NAME:
            component_df.index.name = _COMPONENT_INDEX_NAME

        # Also ensure time-series data for this component has proper dimension names
        component_t = getattr(network, f"{attr}_t", None)
        if component_t is None:
            continue

        # Get the column name for this component type
        ts_col_name = _COMPONENT_TS_COLUMN_NAMES[attr]

        # Check all time-series attributes for this component
        for ts_attr in dir(component_t):
            if ts_attr.startswith('_'):
                continue
            ts_df = getattr(component_t, ts_attr, None)
            if ts_df is None or not hasattr(ts_df, 'index'):
                continue

            # Ensure index (snapshot) has name
            if not ts_df.index.name:
                ts_df.index.name = 'snapshot'

            # Ensure columns (component) has name
            if hasattr(ts_df, 'columns') and not ts_df.columns.name:
                ts_df.columns.name = ts_col_name


def load_province_mapping(mapping_file='data/others/province_mapping.csv', mapping_data=None):
    """
    Load province mapping for converting official names to short names.

    Parameters:
    -----------
    mapping_file : str
        Path to province mapping CSV file
    mapping_data : dict or DataFrame, optional
        Mapping data already loaded in memory (e.g., from config)

    Returns:
    --------
    dict : Mapping from both official and short names to short names
    """
    mapping = {}

    # Prefer mapping data provided directly by the configuration
    if mapping_data is not None:
        if isinstance(mapping_data, pd.DataFrame):
            records = mapping_data.to_dict('records')
        elif isinstance(mapping_data, dict):
            records = [{'official': official, 'short': short}
                       for official, short in mapping_data.items()]
        else:
            # Assume iterable of dict-like rows
            records = list(mapping_data)

        for row in records:
            short_raw = row.get('short')
            official_raw = row.get('official')
            short = None if pd.isna(short_raw) else str(short_raw).strip()
            official = None if pd.isna(official_raw) else str(official_raw).strip()
            if not short:
                continue
            if official:
                mapping[official] = short
            mapping[short] = short

    if mapping:
        return mapping

    # Fall back to reading from file when config data is unavailable
    try:
        df = pd.read_csv(mapping_file, encoding='utf-8-sig')
        for _, row in df.iterrows():
            short = str(row['short']).strip()
            official = str(row['official']).strip()
            mapping[official] = short
            mapping[short] = short
        return mapping
    except Exception:
        return {}


def standardize_region_name(region_name, mapping):
    """
    Standardize region name using mapping.

    Parameters:
    -----------
    region_name : str
        Original region name
    mapping : dict
        Province mapping dictionary

    Returns:
    --------
    str : Standardized region name
    """
    if not mapping or pd.isna(region_name):
        return region_name

    region_str = str(region_name).strip()
    return mapping.get(region_str, region_str)


def _clean_duplicate_columns(network):
    """Remove duplicate columns like 'country.1' from bus data."""
    duplicate_cols = [col for col in network.buses.columns if col.endswith('.1')]
    if duplicate_cols:
        print(f"[info] Removing duplicate columns from buses: {duplicate_cols}")
        network.buses.drop(columns=duplicate_cols, inplace=True)


def _create_bus_to_region_mapping(network, region_column, province_mapping):
    """
    Create mapping from old bus names to regional bus names.

    This is called BEFORE aggregating buses, so we can update components
    that reference buses before the old buses are removed.
    """
    print(f"[info] Creating bus-to-region mapping from '{region_column}'...")

    # Create mapping from old bus to region (using standardized short names)
    bus_to_region = {}
    for bus_name, region_name in network.buses[region_column].items():
        if pd.notna(region_name):
            # Standardize to short name (e.g., '강원특별자치도' -> '강원')
            standardized = standardize_region_name(region_name, province_mapping)
            bus_to_region[bus_name] = standardized

    # Get unique standardized regions
    regions = set(bus_to_region.values())
    print(f"[info] Found {len(regions)} unique regions: {sorted(regions)}")

    return bus_to_region, regions


def _aggregate_buses_by_region(network, region_column, regions, bus_to_region):
    """
    Aggregate buses by region, creating one bus per region.

    This should be called AFTER components (lines, generators, etc.) have been
    updated to reference regional buses.

    Parameters:
    -----------
    network : pypsa.Network
        Network object
    region_column : str
        Name of the column containing region information
    regions : set
        Set of unique region names (standardized short names)
    bus_to_region : dict
        Mapping from old bus names to standardized region names
    """
    print(f"[info] Aggregating {len(network.buses)} buses by '{region_column}'...")

    # Get country from existing bus data
    country = network.buses['country'].iloc[0] if 'country' in network.buses.columns else 'KR'
    carrier = network.buses['carrier'].iloc[0] if 'carrier' in network.buses.columns else 'AC'

    # Ensure 'AC' carrier exists in carriers table
    if carrier not in network.carriers.index:
        network.add("Carrier", carrier)

    # Store old buses for removal
    old_buses = network.buses.index.tolist()

    # Create one bus per region (using average coordinates)
    for region in regions:
        # Get all buses that map to this region
        buses_in_region = [bus_name for bus_name, reg in bus_to_region.items() if reg == region]
        region_buses = network.buses.loc[buses_in_region]

        # Calculate average coordinates
        avg_x = region_buses['x'].mean()
        avg_y = region_buses['y'].mean()

        # Get average voltage (or max)
        v_nom = region_buses['v_nom'].max() if 'v_nom' in region_buses.columns else 345000.0

        # Add regional bus (only with standard PyPSA attributes)
        network.add(
            "Bus",
            region,
            x=avg_x,
            y=avg_y,
            v_nom=v_nom,
            carrier=carrier
        )

        # Add custom attributes directly to DataFrame
        network.buses.loc[region, 'country'] = country
        network.buses.loc[region, 'province'] = region

    # Remove old buses
    for old_bus in old_buses:
        network.remove("Bus", old_bus)

    print(f"[info] Created {len(regions)} regional buses")


def _map_generators_to_regional_buses(network, region_column, province_mapping):
    """Map generators from old buses to regional buses based on province column."""
    print(f"[info] Mapping {len(network.generators)} generators to regional buses...")

    mapped_count = 0
    unmapped_count = 0

    for gen_name in network.generators.index:
        if region_column in network.generators.columns:
            region = network.generators.loc[gen_name, region_column]
            if pd.notna(region):
                # Standardize region name using mapping
                standardized_region = standardize_region_name(region, province_mapping)
                if standardized_region in network.buses.index:
                    # Set the generator's bus to the regional bus
                    network.generators.loc[gen_name, 'bus'] = standardized_region
                    mapped_count += 1
                else:
                    unmapped_count += 1
            else:
                unmapped_count += 1
        else:
            unmapped_count += 1

    print(f"[info] Mapped {mapped_count} generators to regional buses, {unmapped_count} unmapped")


def _aggregate_lines_by_region(network, region_column, line_config, bus_to_region):
    """Aggregate lines by region pairs."""
    print(f"[info] Aggregating {len(network.lines)} lines by region pairs...")

    if len(network.lines) == 0:
        return

    # Map line endpoints to regions
    network.lines['region0'] = network.lines['bus0'].map(bus_to_region)
    network.lines['region1'] = network.lines['bus1'].map(bus_to_region)

    # Remove lines with unmapped buses
    valid_mask = network.lines['region0'].notna() & network.lines['region1'].notna()
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        print(f"[warn] Removing {invalid_count} lines with unmapped buses")
    network.lines = network.lines[valid_mask].copy()

    # Remove self-loops if configured
    if line_config.get('remove_self_loops', True):
        self_loop_mask = network.lines['region0'] != network.lines['region1']
        removed = (~self_loop_mask).sum()
        network.lines = network.lines[self_loop_mask].copy()
        print(f"[info] Removed {removed} self-loop lines")

    # Group by region pairs
    grouping = line_config.get('grouping', 'by_voltage')
    if grouping == 'by_voltage' and 'v_nom' in network.lines.columns:
        group_cols = ['region0', 'region1', 'v_nom']
    else:
        group_cols = ['region0', 'region1']

    # Store old lines
    old_lines = []
    grouped_lines = []

    for group_key, group in network.lines.groupby(group_cols):
        old_lines.extend(group.index.tolist())

        # Aggregate line properties
        agg_line = {
            'bus0': group_key[0] if len(group_key) >= 1 else None,
            'bus1': group_key[1] if len(group_key) >= 2 else None,
        }

        # Add v_nom if grouping by voltage
        if len(group_key) >= 3:
            agg_line['v_nom'] = group_key[2]

        # Aggregate circuits
        circuits_rule = line_config.get('circuits', 'sum')
        if circuits_rule == 'sum':
            total_circuits = group['circuits'].sum()
        elif circuits_rule == 'max':
            total_circuits = group['circuits'].max()
        elif circuits_rule == 'mean':
            total_circuits = group['circuits'].mean()
        else:
            total_circuits = group['circuits'].sum()

        agg_line['num_parallel'] = total_circuits

        # Aggregate s_nom
        s_nom_rule = line_config.get('s_nom', 'keep_original')
        if s_nom_rule == 'sum':
            agg_line['s_nom'] = group['s_nom'].sum()
        elif s_nom_rule == 'max':
            agg_line['s_nom'] = group['s_nom'].max()
        elif s_nom_rule == 'scale_by_circuits':
            agg_line['s_nom'] = group['s_nom'].iloc[0] * total_circuits
        else:  # keep_original
            agg_line['s_nom'] = group['s_nom'].iloc[0]

        # Aggregate impedances (r, x, b)
        impedance_rule = line_config.get('impedance', 'weighted_by_circuits')
        if impedance_rule == 'weighted_by_circuits':
            # Weighted average by circuits
            weights = group['circuits']
            weight_sum = weights.sum()
            if weight_sum > 0:
                agg_line['r'] = (group['r'] * weights).sum() / weight_sum
                agg_line['x'] = (group['x'] * weights).sum() / weight_sum
                agg_line['b'] = (group['b'] * weights).sum() / weight_sum
            else:
                agg_line['r'] = group['r'].mean()
                agg_line['x'] = group['x'].mean()
                agg_line['b'] = group['b'].mean()
        elif impedance_rule == 'mean':
            agg_line['r'] = group['r'].mean()
            agg_line['x'] = group['x'].mean()
            agg_line['b'] = group['b'].mean()
        elif impedance_rule == 'min':
            agg_line['r'] = group['r'].min()
            agg_line['x'] = group['x'].min()
            agg_line['b'] = group['b'].min()
        elif impedance_rule == 'max':
            agg_line['r'] = group['r'].max()
            agg_line['x'] = group['x'].max()
            agg_line['b'] = group['b'].max()

        # Aggregate length
        if 'length' in group.columns:
            length_rule = line_config.get('length', 'mean')
            if length_rule == 'mean':
                agg_line['length'] = group['length'].mean()
            elif length_rule == 'max':
                agg_line['length'] = group['length'].max()
            elif length_rule == 'min':
                agg_line['length'] = group['length'].min()

        # Copy other fields if they exist
        for field in ['type', 'terrain_factor']:
            if field in group.columns:
                value = group[field].iloc[0]
                if pd.notna(value) and value != '':
                    agg_line[field] = value

        grouped_lines.append(agg_line)

    # Remove old lines (and their time-series data)
    for line_name in old_lines:
        network.remove("Line", line_name)

    # Add aggregated lines
    for i, line_data in enumerate(grouped_lines):
        line_name = f"line_{line_data['bus0']}_{line_data['bus1']}_{i}"
        bus0 = line_data.pop('bus0')
        bus1 = line_data.pop('bus1')

        network.add("Line", line_name, bus0=bus0, bus1=bus1, **line_data)

    # Ensure time-series data has proper dimension names
    if hasattr(network.lines_t, 'p0') and network.lines_t.p0 is not None:
        if not network.lines_t.p0.index.name:
            network.lines_t.p0.index.name = 'snapshot'
        if not network.lines_t.p0.columns.name:
            network.lines_t.p0.columns.name = 'Line'

    if hasattr(network.lines_t, 'p1') and network.lines_t.p1 is not None:
        if not network.lines_t.p1.index.name:
            network.lines_t.p1.index.name = 'snapshot'
        if not network.lines_t.p1.columns.name:
            network.lines_t.p1.columns.name = 'Line'

    print(f"[info] Aggregated into {len(grouped_lines)} regional lines")


def _aggregate_links_by_region(network, region_column, link_config, bus_to_region):
    """Aggregate links by region pairs."""
    print(f"[info] Aggregating {len(network.links)} links by region pairs...")

    if len(network.links) == 0:
        return

    # Map link endpoints to regions
    network.links['region0'] = network.links['bus0'].map(bus_to_region)
    network.links['region1'] = network.links['bus1'].map(bus_to_region)

    # Remove links with unmapped buses
    valid_mask = network.links['region0'].notna() & network.links['region1'].notna()
    network.links = network.links[valid_mask].copy()

    # Remove self-loops if configured
    if link_config.get('remove_self_loops', True):
        self_loop_mask = network.links['region0'] != network.links['region1']
        removed = (~self_loop_mask).sum()
        network.links = network.links[self_loop_mask].copy()
        print(f"[info] Removed {removed} self-loop links")

    # Group by region pairs
    grouping = link_config.get('grouping', 'ignore_voltage')
    if grouping == 'by_voltage' and 'v_nom' in network.links.columns:
        group_cols = ['region0', 'region1', 'v_nom']
    else:
        group_cols = ['region0', 'region1']

    # Store old links
    old_links = []
    grouped_links = []

    # Get efficiency setting from config (default 1.0 = 100%)
    default_efficiency = link_config.get('default_efficiency', 1.0)

    for group_key, group in network.links.groupby(group_cols):
        old_links.extend(group.index.tolist())

        # Aggregate link properties
        agg_link = {
            'bus0': group_key[0] if len(group_key) >= 1 else None,
            'bus1': group_key[1] if len(group_key) >= 2 else None,
        }

        # Aggregate p_nom
        p_nom_rule = link_config.get('p_nom', 'sum')
        if p_nom_rule == 'sum':
            agg_link['p_nom'] = group['p_nom'].sum()
        elif p_nom_rule == 'max':
            agg_link['p_nom'] = group['p_nom'].max()
        else:
            agg_link['p_nom'] = group['p_nom'].iloc[0]

        # If aggregated p_nom is 0, set to unlimited capacity
        # (large value to represent no transmission constraint)
        if agg_link['p_nom'] == 0:
            unlimited_capacity = link_config.get('unlimited_capacity', 1e6)  # Default 1,000,000 MW
            agg_link['p_nom'] = unlimited_capacity

        # Set efficiency (100% or from config)
        agg_link['efficiency'] = default_efficiency

        # Aggregate length
        if 'length' in group.columns:
            length_rule = link_config.get('length', 'mean')
            if length_rule == 'mean':
                agg_link['length'] = group['length'].mean()
            elif length_rule == 'max':
                agg_link['length'] = group['length'].max()
            elif length_rule == 'min':
                agg_link['length'] = group['length'].min()

        # Copy other common fields (skip empty carriers)
        for field in ['type']:
            if field in group.columns:
                value = group[field].iloc[0]
                if pd.notna(value) and value != '':
                    agg_link[field] = value

        # Don't copy carrier field - leave it empty/default for links
        # This avoids issues with undefined carriers

        grouped_links.append(agg_link)

    # Remove old links (and their time-series data)
    for link_name in old_links:
        network.remove("Link", link_name)

    # Add aggregated links
    for i, link_data in enumerate(grouped_links):
        link_name = f"link_{link_data['bus0']}_{link_data['bus1']}_{i}"
        bus0 = link_data.pop('bus0')
        bus1 = link_data.pop('bus1')

        network.add("Link", link_name, bus0=bus0, bus1=bus1, **link_data)

    # Ensure time-series data has proper dimension names
    if hasattr(network.links_t, 'p0') and network.links_t.p0 is not None:
        if not network.links_t.p0.index.name:
            network.links_t.p0.index.name = 'snapshot'
        if not network.links_t.p0.columns.name:
            network.links_t.p0.columns.name = 'Link'

    if hasattr(network.links_t, 'p1') and network.links_t.p1 is not None:
        if not network.links_t.p1.index.name:
            network.links_t.p1.index.name = 'snapshot'
        if not network.links_t.p1.columns.name:
            network.links_t.p1.columns.name = 'Link'

    print(f"[info] Aggregated into {len(grouped_links)} regional links")


def _create_regional_loads(network, region_column, demand_file, province_mapping, load_carrier,
                           demand_data=None):
    """
    Create regional loads based on demand data.

    Parameters
    ----------
    demand_data : pandas.DataFrame, optional
        Pre-loaded demand table from configuration (fallback to demand_file when None).
    """
    demand_source = "province_demand config sheet" if demand_data is not None else demand_file
    print(f"[info] Creating regional loads from {demand_source}...")

    # Save existing load time series BEFORE removing invalid loads
    # This preserves the temporal pattern for distribution across regions
    base_load_pattern = None
    original_total_load = 0
    if hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p_set'):
        if len(network.loads_t.p_set.columns) > 0:
            # Sum all loads to get total temporal pattern
            base_load_pattern = network.loads_t.p_set.sum(axis=1).copy()
            original_total_load = base_load_pattern.sum()
            print(f"[info] Saved original load pattern (total: {original_total_load:.0f} MW)")

    # Now fix any existing loads that point to non-existent buses
    loads_to_fix = []
    for load_name in network.loads.index.tolist():
        load_bus = network.loads.loc[load_name, 'bus']
        if load_bus not in network.buses.index:
            # Try to map to regional bus using province column if available
            if region_column in network.loads.columns:
                region = network.loads.loc[load_name, region_column]
                if pd.notna(region) and region in network.buses.index:
                    network.loads.loc[load_name, 'bus'] = region
                    print(f"[info] Fixed load '{load_name}' bus from '{load_bus}' to '{region}'")
                else:
                    loads_to_fix.append(load_name)
            else:
                loads_to_fix.append(load_name)

    # Remove unfixable loads
    for load_name in loads_to_fix:
        network.remove("Load", load_name)
        print(f"[info] Removed load '{load_name}' with invalid bus")

    # Load demand data
    try:
        if demand_data is not None:
            demand_df = demand_data.copy()
        else:
            if demand_file is None:
                raise ValueError("No demand file path provided")
            if demand_file.endswith('.xlsx'):
                demand_df = pd.read_excel(demand_file)
            else:
                demand_df = pd.read_csv(demand_file)

        if region_column not in demand_df.columns:
            raise KeyError(f"Demand data missing '{region_column}' column")

        # Standardize region names in demand file
        if region_column in demand_df.columns:
            demand_df[region_column] = demand_df[region_column].apply(
                lambda x: standardize_region_name(x, province_mapping)
            )

        # Remove "합계" (total) row if it exists
        demand_df = demand_df[demand_df[region_column] != '합계'].copy()

        print(f"[info] Loaded demand data for {len(demand_df)} regions")

        # Calculate ratios from absolute values
        total_demand = demand_df['demand'].sum()
        demand_df['ratio'] = demand_df['demand'] / total_demand

        print(f"[info] Total demand: {total_demand:.0f}, calculating regional ratios")

        # Create loads for each region using ratios
        for _, row in demand_df.iterrows():
            region = row[region_column]
            ratio = row['ratio']

            if region in network.buses.index and ratio > 0:
                load_name = f"load_{region}"

                # Calculate load value
                if base_load_pattern is not None:
                    # Use ratio to scale the base pattern
                    # The base pattern will be distributed across regions
                    load_value = base_load_pattern.mean() * ratio
                else:
                    # Use absolute value if no pattern exists
                    load_value = row['demand']

                # Only create if doesn't exist
                if load_name not in network.loads.index:
                    load_params = {
                        'bus': region,
                        'p_set': load_value,
                    }
                    if load_carrier:
                        load_params['carrier'] = load_carrier

                    network.add("Load", load_name, **load_params)

                    # If we have a base pattern, create time series for this load
                    if base_load_pattern is not None:
                        # Scale the pattern by the ratio
                        network.loads_t.p_set[load_name] = base_load_pattern * ratio

        print(f"[info] Total regional loads: {len(network.loads)}")

    except Exception as e:
        print(f"[warn] Could not load demand file: {e}")
        print("[warn] Creating equal loads for all regions...")

        # Create equal loads for all regions
        for region in network.buses.index:
            load_name = f"load_{region}"
            if load_name not in network.loads.index:
                load_params = {
                    'bus': region,
                    'p_set': 1000.0,  # Default load
                }
                if load_carrier:
                    load_params['carrier'] = load_carrier

                network.add("Load", load_name, **load_params)


def aggregate_network_by_region(network, config):
    """
    Main function to aggregate entire network by region.

    Performs all aggregation steps:
    1. Clean duplicate columns
    2. Create bus-to-region mapping
    3. Update all components to reference regional buses:
       a. Map generators to regional buses
       b. Aggregate lines by region pairs
       c. Aggregate links by region pairs
    4. Aggregate buses by region (remove old buses, create regional buses)
    5. Optionally aggregate generators by carrier and region
    6. Create regional loads from demand data

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object
    config : dict
        Configuration dictionary with regional_aggregation settings

    Returns:
    --------
    pypsa.Network : Aggregated network
    """

    # Get regional aggregation config
    regional_config = config.get('regional_aggregation', {})
    region_column = regional_config.get('region_column', 'province')
    demand_file = regional_config.get('demand_file', 'data/others/province_demand.xlsx')
    province_mapping_file = regional_config.get('province_mapping_file', 'data/others/province_mapping.csv')
    load_carrier = regional_config.get('load_carrier', None)

    # Convert empty strings to None
    if load_carrier == "":
        load_carrier = None

    # Load province mapping
    province_mapping_data = config.get('province_mapping')
    province_mapping = load_province_mapping(province_mapping_file, province_mapping_data)

    print(f"[info] Starting regional aggregation by '{region_column}'...")

    # Step 1: Clean duplicate columns
    _clean_duplicate_columns(network)

    # Step 2: Create bus-to-region mapping (BEFORE removing old buses)
    bus_to_region, regions = _create_bus_to_region_mapping(network, region_column, province_mapping)

    # Step 3: Create regional buses FIRST (so components can reference them)
    _aggregate_buses_by_region(network, region_column, regions, bus_to_region)

    # Step 4: Update all components to reference regional buses
    # (MUST be done after creating regional buses)

    # Step 4a: Map generators to regional buses
    _map_generators_to_regional_buses(network, region_column, province_mapping)

    # Step 4b: Aggregate lines by region pairs (updates bus references)
    if len(network.lines) > 0:
        _aggregate_lines_by_region(network, region_column,
                                   regional_config.get('lines', {}),
                                   bus_to_region)

    # Step 4c: Aggregate links by region pairs (updates bus references)
    if len(network.links) > 0:
        _aggregate_links_by_region(network, region_column,
                                   regional_config.get('links', {}),
                                   bus_to_region)

    # Step 5: Optionally aggregate generators by carrier and region
    if regional_config.get('aggregate_generators_by_carrier', False):
        from libs.aggregators import aggregate_generators_by_carrier_and_region
        network = aggregate_generators_by_carrier_and_region(network, config, region_column, province_mapping)

    # Step 6: Create regional loads
    _create_regional_loads(
        network,
        region_column,
        demand_file,
        province_mapping,
        load_carrier,
        demand_data=config.get('province_demand')
    )

    print("[info] Regional aggregation complete")

    # Restore dimension names in case they were dropped during aggregation
    _ensure_named_dimensions(network)

    return network
