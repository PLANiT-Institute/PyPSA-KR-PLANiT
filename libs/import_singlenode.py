# import_singlenode.py
# This module handles importing single node data for PyPSA analysis

import pandas as pd
import numpy as np
import pypsa
from pathlib import Path


def import_base_model(year=2024, network_name='kr_grid', bus_name='kr_bus'):
    """
    Import base PyPSA model for single node analysis.
    
    Parameters:
    -----------
    year : int, default 2024
        Year for data import (snapshot year)
    network_name : str, default 'kr_grid'
        Name of the PyPSA network
    bus_name : str, default 'kr_bus'
        Name of the single bus in the network
        
    Returns:
    --------
    pypsa.Network
        PyPSA network object with imported data
    """
    
    # Create PyPSA network
    network = pypsa.Network(name=network_name)
    
    # Set up data path
    data_path = f"data/{year}"
    
    print(f"Importing all CSV files from {data_path}...")
    
    # Import all CSV files from the folder using PyPSA's built-in function
    try:
        network.import_from_csv_folder(data_path)
        print(f"Successfully imported all CSV files from {data_path}")
    except Exception as e:
        print(f"Error importing from CSV folder: {e}")
        print("Falling back to manual import...")
        return _manual_import_fallback(network, data_path, bus_name, year)
    
    # Filter to keep only required components
    print("Filtering network to single node configuration...")
    
    # Get all existing buses and remove them except create our single bus
    existing_buses = list(network.buses.index)
    for bus in existing_buses:
        network.remove("Bus", bus)
    
    # Create single bus
    network.add("Bus", bus_name)
    print(f"Created single bus: {bus_name}")
    
    # Update all generators to connect to the single bus
    if len(network.generators) > 0:
        network.generators['bus'] = bus_name
        print(f"Connected {len(network.generators)} generators to {bus_name}")
    
    # Update all loads to connect to the single bus
    if len(network.loads) > 0:
        network.loads['bus'] = bus_name
        print(f"Connected {len(network.loads)} loads to {bus_name}")
    
    # Add marginal costs to generators if not present
    if len(network.generators) > 0:
        for idx, gen in network.generators.iterrows():
            if pd.isna(gen.get('marginal_cost', np.nan)):
                carrier = gen.get('carrier', 'unknown')
                # Set marginal cost based on carrier type
                if carrier == 'LNG':
                    marginal_cost = 50.0  # €/MWh
                elif carrier == 'coal':
                    marginal_cost = 30.0  # €/MWh
                elif carrier == 'nuclear':
                    marginal_cost = 10.0  # €/MWh
                elif carrier == 'renewable':
                    marginal_cost = 0.0   # €/MWh
                elif carrier == 'hydro':
                    marginal_cost = 0.0   # €/MWh
                else:
                    marginal_cost = 40.0  # Default €/MWh
                
                network.generators.at[idx, 'marginal_cost'] = marginal_cost
        
        print("Added marginal costs to generators")
    
    # Add a load if none exists (required for optimization)
    if len(network.loads) == 0:
        network.add("Load", 
                    name="load_1", 
                    bus=bus_name, 
                    p_set=50000)  # 50 GW load
        print(f"Added default load to {bus_name}")
    
    # Remove any links, lines, or transformers (keep only single node)
    if len(network.links) > 0:
        network.remove("Link", network.links.index)
        print("Removed all links")
    
    if len(network.lines) > 0:
        network.remove("Line", network.lines.index)
        print("Removed all lines")
    
    if len(network.transformers) > 0:
        network.remove("Transformer", network.transformers.index)
        print("Removed all transformers")
    
    # Keep only snapshots (time series data)
    if len(network.snapshots) > 0:
        print(f"Kept {len(network.snapshots)} snapshots")
    else:
        # Create default snapshots if none exist
        network.set_snapshots([f"{year}-01-01 00:00:00"])
        print("Created default snapshot")
    
    print(f"\nNetwork '{network_name}' created successfully!")
    print(f"- Year: {year}")
    print(f"- Bus: {bus_name}")
    print(f"- Snapshots: {len(network.snapshots)}")
    print(f"- Generators: {len(network.generators)}")
    print(f"- Carriers: {len(network.carriers)}")
    
    return network


def _manual_import_fallback(network, data_path, bus_name, year):
    """
    Fallback function for manual import if CSV folder import fails
    """
    print("Using manual import fallback...")
    
    # Clear the network completely and start fresh
    network = pypsa.Network(name=network.name)
    
    # Import snapshots (time series data)
    snapshots_file = Path(data_path) / "snapshots.csv"
    if snapshots_file.exists():
        snapshots_df = pd.read_csv(snapshots_file)
        # Set snapshots for the network - use 'snapshot' column
        network.set_snapshots(snapshots_df['snapshot'].tolist())
        print(f"Imported {len(network.snapshots)} snapshots for year {year}")
    else:
        print(f"Warning: snapshots.csv not found in {data_path}")
        # Create default snapshots if file doesn't exist
        network.set_snapshots([f"{year}-01-01 00:00:00"])
    
    # Create single bus
    network.add("Bus", bus_name)
    print(f"Created bus: {bus_name}")
    
    # Add a load to the bus (required for optimization)
    network.add("Load", 
                name="load_1", 
                bus=bus_name, 
                p_set=50000)  # 50 GW load
    print(f"Added load to {bus_name}")
    
    # Import generators and connect them to the single bus
    generators_file = Path(data_path) / "generators.csv"
    if generators_file.exists():
        try:
            generators_df = pd.read_csv(generators_file, encoding='utf-8-sig')
        except UnicodeDecodeError:
            try:
                generators_df = pd.read_csv(generators_file, encoding='cp949')
            except UnicodeDecodeError:
                generators_df = pd.read_csv(generators_file, encoding='latin-1')
        
        # Update all generators to connect to the single bus
        generators_df['bus'] = bus_name
        
        # Add generators to network
        for idx, gen in generators_df.iterrows():
            # Handle missing values with defaults
            p_nom = gen.get('p_nom', 100.0) if pd.notna(gen.get('p_nom')) else 100.0
            carrier = gen.get('carrier', 'unknown') if pd.notna(gen.get('carrier')) else 'unknown'
            control = gen.get('control', 'PQ') if pd.notna(gen.get('control')) else 'PQ'
            p_min_pu = gen.get('p_min_pu', 0.0) if pd.notna(gen.get('p_min_pu')) else 0.0
            p_max_pu = gen.get('p_max_pu', 1.0) if pd.notna(gen.get('p_max_pu')) else 1.0
            
            # Set marginal cost based on carrier type
            if carrier == 'LNG':
                marginal_cost = 50.0  # €/MWh
            elif carrier == 'coal':
                marginal_cost = 30.0  # €/MWh
            elif carrier == 'nuclear':
                marginal_cost = 10.0  # €/MWh
            elif carrier == 'renewable':
                marginal_cost = 0.0   # €/MWh
            elif carrier == 'hydro':
                marginal_cost = 0.0   # €/MWh
            else:
                marginal_cost = 40.0  # Default €/MWh
            
            # Add generator with basic parameters
            network.add("Generator",
                       name=gen['name'],
                       bus=bus_name,
                       p_nom=p_nom,
                       carrier=carrier,
                       control=control,
                       p_min_pu=p_min_pu,
                       p_max_pu=p_max_pu,
                       marginal_cost=marginal_cost)
        
        print(f"Imported {len(generators_df)} generators connected to {bus_name}")
    else:
        print(f"Warning: generators.csv not found in {data_path}")
    
    # Import carriers (energy carriers)
    carriers_file = Path(data_path) / "carriers.csv"
    if carriers_file.exists():
        try:
            carriers_df = pd.read_csv(carriers_file, encoding='utf-8-sig')
        except UnicodeDecodeError:
            try:
                carriers_df = pd.read_csv(carriers_file, encoding='cp949')
            except UnicodeDecodeError:
                carriers_df = pd.read_csv(carriers_file, encoding='latin-1')
        
        # Add carriers to network
        for idx, carrier in carriers_df.iterrows():
            network.add("Carrier", name=carrier['name'])
        
        print(f"Imported {len(carriers_df)} carriers")
    else:
        print(f"Warning: carriers.csv not found in {data_path}")
    
    print(f"\nNetwork created successfully using fallback method!")
    print(f"- Year: {year}")
    print(f"- Bus: {bus_name}")
    print(f"- Snapshots: {len(network.snapshots)}")
    print(f"- Generators: {len(network.generators)}")
    print(f"- Carriers: {len(network.carriers)}")
    
    return network


def main():
    """
    Main function for importing single node data
    """
    # Import base model with default parameters
    network = import_base_model()
    
    # Display network summary
    print("\n" + "="*50)
    print("NETWORK SUMMARY")
    print("="*50)
    print(network)
    
    return network


if __name__ == "__main__":
    main()
