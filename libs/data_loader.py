"""
Data loading functions for PyPSA networks and monthly cost data.
"""
import pypsa
import pandas as pd
from pathlib import Path
from libs.leapyear_handler import adjust_year_with_leap_handling
from libs.load_scaler import scale_loads_to_target


def load_network(config):
    """
    Load PyPSA network from CSV folder and manually load loads_t data.

    PyPSA's automatic import sometimes fails to load time-series data when
    snapshots are stored as strings, so we load loads_t.p_set manually.

    Parameters:
    -----------
    config : dict
        Configuration dictionary containing Base_year settings

    Returns:
    --------
    pypsa.Network : Loaded network
    """
    data_path = config['Base_year']['file_path']

    network = pypsa.Network()

    # Import network from CSV folder
    # PyPSA will use pandas read_csv internally, which already treats empty strings as NaN
    # by default (keep_default_na=True)
    network.import_from_csv_folder(data_path)

    # Clean up any empty strings that might have slipped through
    # Convert empty strings to NaN in generators DataFrame
    if hasattr(network, 'generators') and 'cc_group' in network.generators.columns:
        # Replace empty strings with NaN
        network.generators['cc_group'] = network.generators['cc_group'].replace('', pd.NA)
        network.generators['cc_group'] = network.generators['cc_group'].replace(' ', pd.NA)

    # Fix snapshots and all time-series indices to use dayfirst format
    # IMPORTANT: Convert time-series indices FIRST, then convert network.snapshots
    # Otherwise PyPSA will reindex and cause data loss!

    # Step 1: Convert all time-series component indices FIRST
    for attr in dir(network):
        if not attr.endswith('_t'):
            continue
        component_t = getattr(network, attr)
        if component_t is None:
            continue

        for ts_attr in dir(component_t):
            if ts_attr.startswith('_'):
                continue
            df = getattr(component_t, ts_attr)
            if isinstance(df, pd.DataFrame) and not df.empty:
                if not isinstance(df.index, pd.DatetimeIndex):
                    # Convert index in-place to DatetimeIndex with dayfirst
                    df.index = pd.to_datetime(df.index, dayfirst=True)
                    df.index.name = 'snapshot'

    # Step 2: Now convert network.snapshots to match
    if not isinstance(network.snapshots, pd.DatetimeIndex):
        network.snapshots = pd.to_datetime(network.snapshots, dayfirst=True)
        print(f"[info] Converted snapshots to DatetimeIndex with day-first format")

    # Step 2.5: Filter ALL components for target_year (build_year <= target_year < close_year)
    base_year = config.get('Base_year', {}).get('year')
    target_year = config.get('modelling_setting', {}).get('target_year')

    if base_year and target_year:
        # PyPSA component types that might have build_year/close_year
        component_types = [
            'generators', 'storage_units', 'stores', 'loads', 'lines', 'links',
            'transformers', 'buses', 'shunt_impedances', 'carriers'
        ]

        for comp_type in component_types:
            if not hasattr(network, comp_type):
                continue

            component = getattr(network, comp_type)
            if component.empty or 'build_year' not in component.columns:
                continue

            # Keep components built by target_year
            keep_mask = component['build_year'] <= target_year

            # AND still operating (close_year > target_year OR close_year is NaN)
            if 'close_year' in component.columns:
                keep_mask = keep_mask & ((component['close_year'] > target_year) | component['close_year'].isna())

            # Remove components that don't meet criteria
            items_to_remove = component.index[~keep_mask].tolist()
            if items_to_remove:
                comp_name_singular = comp_type.rstrip('s').capitalize() if comp_type.endswith('s') else comp_type.capitalize()
                for item in items_to_remove:
                    network.remove(comp_name_singular, item)
                print(f"[info] Filtered {comp_type} for year {target_year}: kept {keep_mask.sum()}, removed {len(items_to_remove)}")

    # Step 3: Apply leap year handling (handler decides if needed)

    # IMPORTANT: Adjust all time-series component data FIRST, before changing network.snapshots
    # If we change network.snapshots first, PyPSA will reindex time-series data and clear them!
    for attr in dir(network):
        if not attr.endswith('_t'):
            continue
        component_t = getattr(network, attr)
        if component_t is None:
            continue

        for ts_attr in dir(component_t):
            if ts_attr.startswith('_'):
                continue
            df = getattr(component_t, ts_attr)
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Adjust the datetime index
                adjusted_df = adjust_year_with_leap_handling(df, base_year, target_year, datetime_col=None)
                setattr(component_t, ts_attr, adjusted_df)

    # NOW adjust network snapshots to match
    snapshot_df = pd.DataFrame(index=network.snapshots)
    snapshot_df = adjust_year_with_leap_handling(snapshot_df, base_year, target_year, datetime_col=None)
    network.snapshots = snapshot_df.index

    if base_year and target_year and base_year != target_year:
        print(f"[info] Temporal data adjusted from year {base_year} to {target_year}")

    # Step 4: Scale loads to target total load (only if target_load is specified)
    target_load = config.get('modelling_setting', {}).get('target_load')
    if target_load:
        network = scale_loads_to_target(network, target_load)

    print(f"Network loaded from {data_path}")
    return network


def load_monthly_data(config):
    """
    Load monthly data from CSV and parse dates.
    Changes year from base_year to target_year (no leap year handling needed for monthly data).

    Parameters:
    -----------
    config : dict
        Configuration dictionary containing monthly_data settings

    Returns:
    --------
    pd.DataFrame : Monthly data with parsed datetime
    """
    monthly_file = config['monthly_data']['file_path']
    df = pd.read_csv(monthly_file)

    # Parse snapshot column as datetime (dayfirst format)
    df['snapshot'] = pd.to_datetime(df['snapshot'], dayfirst=True)

    # Filter for base_year data and change to target_year
    base_year = config.get('Base_year', {}).get('year')
    target_year = config.get('modelling_setting', {}).get('target_year')

    if base_year and target_year:
        # Keep only base_year data
        df = df[df['snapshot'].dt.year == base_year].copy()
        # Change year to target_year
        if base_year != target_year:
            df['snapshot'] = df['snapshot'].apply(lambda x: x.replace(year=target_year))

    return df


def load_snapshot_data(config):
    """
    Load snapshot-level data from CSV and parse dates.
    Adjusts year from base_year to target_year if they differ.

    Parameters:
    -----------
    config : dict
        Configuration dictionary containing snapshot_data settings

    Returns:
    --------
    pd.DataFrame : Snapshot data with parsed datetime
    """
    snapshot_file = config['snapshot_data']['file_path']
    df = pd.read_csv(snapshot_file, low_memory=False)

    # Parse snapshot column as datetime (dayfirst format)
    df['snapshot'] = pd.to_datetime(df['snapshot'], dayfirst=True)

    # Filter for base_year data and apply leap year handling
    base_year = config.get('Base_year', {}).get('year')
    target_year = config.get('modelling_setting', {}).get('target_year')

    if base_year and target_year:
        # Keep only base_year data
        df = df[df['snapshot'].dt.year == base_year].copy()

    # Change year with leap year handling
    df = adjust_year_with_leap_handling(df, base_year, target_year, datetime_col='snapshot')

    return df
