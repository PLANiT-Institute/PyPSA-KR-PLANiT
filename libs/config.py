"""
Configuration management for PyPSA analysis.
"""
import yaml
import pandas as pd
from pathlib import Path


def load_config(config_path="config.yaml"):
    """
    Load configuration from YAML or Excel file.

    Supports both .yaml and .xlsx file formats.
    Excel files should have specific tabs as created by the config template.

    Parameters:
    -----------
    config_path : str
        Path to the configuration file (.yaml or .xlsx)

    Returns:
    --------
    dict : Configuration dictionary
    """
    config_path = Path(config_path)

    if config_path.suffix == '.xlsx':
        return load_config_from_excel(config_path)
    else:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config


def load_config_from_excel(excel_path):
    """
    Load configuration from Excel file with multiple tabs.

    Expected tabs:
    - carrier_mapping: original_carrier, mapped_carrier
    - generator_attributes: carrier, p_min_pu, p_max_pu, max_cf, etc.
    - global_constraints: carrier, min_cf, max_cf
    - file_paths: setting, value
    - regional_settings: setting, value
    - cc_merge_rules: attribute, rule
    - years: year

    Parameters:
    -----------
    excel_path : str or Path
        Path to Excel configuration file

    Returns:
    --------
    dict : Configuration dictionary
    """
    config = {}

    # Load carrier mapping
    df_carrier_mapping = pd.read_excel(excel_path, sheet_name='carrier_mapping')
    config['carrier_mapping'] = dict(zip(
        df_carrier_mapping['original_carrier'],
        df_carrier_mapping['mapped_carrier']
    ))

    # Load generator attributes
    df_gen_attrs = pd.read_excel(excel_path, sheet_name='generator_attributes')
    config['generator_attributes'] = {}
    # Handle both 'carrier' and 'carriers' column names
    carrier_col = 'carriers' if 'carriers' in df_gen_attrs.columns else 'carrier'
    for _, row in df_gen_attrs.iterrows():
        carrier = row[carrier_col]
        attrs = row.drop(carrier_col).dropna().to_dict()
        config['generator_attributes'][carrier] = attrs

    # Load global constraints
    df_global_constraints = pd.read_excel(excel_path, sheet_name='global_constraints')
    config['global_constraints'] = {}
    # Handle both 'carrier' and 'carriers' column names
    carrier_col = 'carriers' if 'carriers' in df_global_constraints.columns else 'carrier'
    for _, row in df_global_constraints.iterrows():
        carrier = row[carrier_col]
        constraints = row.drop(carrier_col).dropna().to_dict()
        config['global_constraints'][carrier] = constraints

    # Load file paths
    df_paths = pd.read_excel(excel_path, sheet_name='file_paths')
    config['monthly_data'] = {}
    config['snapshot_data'] = {}
    config['Base_year'] = {}

    for _, row in df_paths.iterrows():
        setting = row['setting']
        value = row['value']
        if setting == 'monthly_data_file':
            config['monthly_data']['file_path'] = value
        elif setting == 'snapshot_data_file':
            config['snapshot_data']['file_path'] = value
        elif setting == 'base_year':
            config['Base_year']['year'] = int(value) if pd.notna(value) else None
        elif setting == 'base_file_path':
            config['Base_year']['file_path'] = value

    # Load regional settings
    df_regional = pd.read_excel(excel_path, sheet_name='regional_settings')
    config['regional_settings'] = {}
    for _, row in df_regional.iterrows():
        config['regional_settings'][row['setting']] = row['value']

    # Load CC merge rules
    df_cc_rules = pd.read_excel(excel_path, sheet_name='cc_merge_rules')
    config['cc_merge_rules'] = dict(zip(
        df_cc_rules['attribute'],
        df_cc_rules['rule']
    ))

    # Load years
    df_years = pd.read_excel(excel_path, sheet_name='years')
    config['Years'] = df_years['year'].tolist()

    # Load carrier order
    df_carrier_order = pd.read_excel(excel_path, sheet_name='carrier_order')
    config['carriers_order'] = df_carrier_order['carriers'].tolist()

    # Load regional aggregation settings (if sheet exists)
    try:
        df_regional_agg = pd.read_excel(excel_path, sheet_name='regional_aggregation')
        config['regional_aggregation'] = {}
        for _, row in df_regional_agg.iterrows():
            setting = row['setting']
            value = row['value']
            # Convert TRUE/FALSE strings to boolean
            if isinstance(value, str) and value.upper() in ['TRUE', 'FALSE']:
                value = value.upper() == 'TRUE'
            config['regional_aggregation'][setting] = value
    except Exception:
        pass  # Sheet doesn't exist, skip

    # Load generator region aggregator rules (if sheet exists)
    try:
        df_gen_region_rules = pd.read_excel(excel_path, sheet_name='generator_region_agg_rules')
        config['generator_region_aggregator_rules'] = dict(zip(
            df_gen_region_rules['attribute'],
            df_gen_region_rules['rule']
        ))
    except Exception:
        pass  # Sheet doesn't exist, skip

    # Load generator_t aggregator rules (if sheet exists)
    try:
        df_gen_t_rules = pd.read_excel(excel_path, sheet_name='generator_t_aggregator_rules')
        config['generator_t_aggregator_rules'] = dict(zip(
            df_gen_t_rules['attribute'],
            df_gen_t_rules['rule']
        ))
    except Exception:
        pass  # Sheet doesn't exist, skip

    # Load lines config (if sheet exists)
    try:
        df_lines_config = pd.read_excel(excel_path, sheet_name='lines_config')
        lines_config = {}
        for _, row in df_lines_config.iterrows():
            setting = row['setting']
            value = row['value']
            # Convert TRUE/FALSE strings to boolean
            if isinstance(value, str) and value.upper() in ['TRUE', 'FALSE']:
                value = value.upper() == 'TRUE'
            lines_config[setting] = value
        config['regional_aggregation'] = config.get('regional_aggregation', {})
        config['regional_aggregation']['lines'] = lines_config
    except Exception:
        pass  # Sheet doesn't exist, skip

    # Load links config (if sheet exists)
    try:
        df_links_config = pd.read_excel(excel_path, sheet_name='links_config')
        links_config = {}
        for _, row in df_links_config.iterrows():
            setting = row['setting']
            value = row['value']
            # Convert TRUE/FALSE strings to boolean
            if isinstance(value, str) and value.upper() in ['TRUE', 'FALSE']:
                value = value.upper() == 'TRUE'
            # Convert numeric strings to numbers
            try:
                value = float(value)
            except:
                pass
            links_config[setting] = value
        config['regional_aggregation'] = config.get('regional_aggregation', {})
        config['regional_aggregation']['links'] = links_config
    except Exception:
        pass  # Sheet doesn't exist, skip

    # Load province mapping (if sheet exists)
    try:
        df_province_mapping = pd.read_excel(excel_path, sheet_name='province_mapping')
        # Store as DataFrame to access group columns (group1, group2)
        config['province_mapping_df'] = df_province_mapping
        # Also keep the dict mapping for backward compatibility
        config['province_mapping'] = dict(zip(
            df_province_mapping['official'],
            df_province_mapping['short']
        ))
        # Also add reverse mapping (short -> official) for display purposes
        config['province_mapping_reverse'] = dict(zip(
            df_province_mapping['short'],
            df_province_mapping['official']
        ))
    except Exception:
        pass  # Sheet doesn't exist, skip

    # Load province demand (if sheet exists)
    try:
        df_province_demand = pd.read_excel(excel_path, sheet_name='province_demand')
        # Store as DataFrame for regional load creation
        config['province_demand'] = df_province_demand
    except Exception:
        pass  # Sheet doesn't exist, skip

    return config
