import pandas as pd
import numpy as np
from pathlib import Path


def generator_converter(inputpath, outputpath):
    """
    Convert an Excel file containing generator data to PyPSA-compatible format.
    
    Parameters:
    -----------
    inputpath : str
        Path to the input Excel file
    outputpath : str
        Path to the output directory where generators.csv will be saved
    
    Returns:
    --------
    None
        Saves the converted data as generators.csv in the specified output directory
    """
    
    # Read the Excel file
    try:
        df = pd.read_excel(inputpath)
        print(f"Successfully loaded data from {inputpath}")
        print(f"Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Create output directory if it doesn't exist
    output_dir = Path(outputpath)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to PyPSA generator format
    # PyPSA generators.csv typically needs these columns:
    # name, bus, control, p_nom, marginal_cost, capital_cost, efficiency, etc.
    
    # Create a basic PyPSA generator dataframe
    generators_df = pd.DataFrame()
    
    # Map common column names to PyPSA format
    column_mapping = {
        'name': ['name', 'generator_name', 'id', 'generator_id'],
        'bus': ['bus', 'bus_id', 'node', 'node_id'],
        'p_nom': ['capacity', 'p_nom', 'max_power', 'rated_power', 'mw'],
        'marginal_cost': ['marginal_cost', 'variable_cost', 'fuel_cost', 'cost'],
        'capital_cost': ['capital_cost', 'investment_cost', 'capex'],
        'efficiency': ['efficiency', 'eta', 'conversion_efficiency']
    }
    
    # Try to map existing columns to PyPSA format
    for pypsa_col, possible_names in column_mapping.items():
        for possible_name in possible_names:
            if possible_name.lower() in [col.lower() for col in df.columns]:
                # Find the actual column name (case-insensitive)
                actual_col = next(col for col in df.columns if col.lower() == possible_name.lower())
                generators_df[pypsa_col] = df[actual_col]
                break
    
    # If no name column found, create one
    if 'name' not in generators_df.columns:
        generators_df['name'] = [f"gen_{i}" for i in range(len(df))]
    
    # If no bus column found, create a default one
    if 'bus' not in generators_df.columns:
        generators_df['bus'] = 'bus_0'  # Default bus
    
    # Set default values for missing PyPSA columns
    if 'p_nom' not in generators_df.columns:
        generators_df['p_nom'] = 100.0  # Default capacity in MW
    
    if 'marginal_cost' not in generators_df.columns:
        generators_df['marginal_cost'] = 50.0  # Default marginal cost in €/MWh
    
    if 'capital_cost' not in generators_df.columns:
        generators_df['capital_cost'] = 1000000.0  # Default capital cost in €/MW
    
    if 'efficiency' not in generators_df.columns:
        generators_df['efficiency'] = 0.4  # Default efficiency
    
    # Add other common PyPSA generator columns with defaults
    generators_df['control'] = 'PQ'  # Default control type
    generators_df['p_min_pu'] = 0.0  # Minimum power output (per unit)
    generators_df['p_max_pu'] = 1.0  # Maximum power output (per unit)
    generators_df['ramp_limit_up'] = 1.0  # Ramp up limit (per unit)
    generators_df['ramp_limit_down'] = 1.0  # Ramp down limit (per unit)
    generators_df['min_up_time'] = 0  # Minimum up time (hours)
    generators_df['min_down_time'] = 0  # Minimum down time (hours)
    
    # Save to CSV
    output_file = output_dir / 'generators.csv'
    generators_df.to_csv(output_file, index=False)
    
    print(f"Successfully converted and saved generators data to {output_file}")
    print(f"Generated {len(generators_df)} generators")
    print(f"Columns in output: {list(generators_df.columns)}")
    
    return generators_df


# Example usage (commented out)
if __name__ == "__main__":
    # Example usage:
    # input_file = "path/to/your/generators.xlsx"
    # output_dir = "path/to/output/directory"
    # generator_converter(input_file, output_dir)
    pass

