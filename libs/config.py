"""
Configuration management for PyPSA analysis.
"""
import yaml


def load_config(config_path="config.yaml"):
    """
    Load configuration from YAML file.

    Parameters:
    -----------
    config_path : str
        Path to the configuration YAML file

    Returns:
    --------
    dict : Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config
