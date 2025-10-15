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
    network.import_from_csv_folder(data_path)

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
