# import_singlenode.py
# This module handles importing single node data for PyPSA analysis

import pandas as pd
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
    data_path = Path(f"data/{year}")
    
    # Import snapshots (time series data)
    snapshots_file = data_path / "snapshots.csv"
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
    generators_file = data_path / "generators.csv"
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
    carriers_file = data_path / "carriers.csv"
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
    
    print(f"\nNetwork '{network_name}' created successfully!")
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
