"""
Data loading functions for PyPSA networks and monthly cost data.
"""
import pypsa
import pandas as pd
from pathlib import Path


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

    print(f"Network loaded from {data_path}")
    return network


def load_monthly_data(config):
    """
    Load monthly data from CSV and parse dates.

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

    return df


def load_snapshot_data(config):
    """
    Load snapshot-level data from CSV and parse dates.

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

    return df
