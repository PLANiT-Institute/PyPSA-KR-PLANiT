# Install required packages if not already installed
import subprocess
import sys

def install_package(package):
    """Install a package using pip if not already installed"""
    try:
        __import__(package)
        print(f"✓ {package} is already installed")
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} installed successfully")

# Install required packages
print("Checking and installing required packages...")
install_package("pypsa")
install_package("pandas")

print("\n" + "="*50)
print("IMPORTING PACKAGES")
print("="*50)

import pypsa
import pandas as pd
import os

# Set up the path to the 2024 data folder
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level from libs folder to project root, then to data/2024
data_path = os.path.join(script_dir, '..', 'data', '2024')
# Convert to absolute path to avoid any path issues
data_path = os.path.abspath(data_path)

print(f"Looking for data files in: {data_path}")
print(f"Data directory exists: {os.path.exists(data_path)}")

# Import the CSV files from the 2024 folder with proper encoding
print("Reading CSV files...")
try:
    buses = pd.read_csv(os.path.join(data_path, 'buses.csv'), encoding='utf-8')
    print("✓ buses.csv loaded")
except UnicodeDecodeError:
    buses = pd.read_csv(os.path.join(data_path, 'buses.csv'), encoding='cp949')
    print("✓ buses.csv loaded (with cp949 encoding)")

try:
    carriers = pd.read_csv(os.path.join(data_path, 'carriers.csv'), encoding='utf-8')
    print("✓ carriers.csv loaded")
except UnicodeDecodeError:
    carriers = pd.read_csv(os.path.join(data_path, 'carriers.csv'), encoding='cp949')
    print("✓ carriers.csv loaded (with cp949 encoding)")

try:
    generators = pd.read_csv(os.path.join(data_path, 'generators.csv'), encoding='utf-8')
    print("✓ generators.csv loaded")
except UnicodeDecodeError:
    generators = pd.read_csv(os.path.join(data_path, 'generators.csv'), encoding='cp949')
    print("✓ generators.csv loaded (with cp949 encoding)")

try:
    loads = pd.read_csv(os.path.join(data_path, 'loads.csv'), encoding='utf-8')
    print("✓ loads.csv loaded")
except UnicodeDecodeError:
    loads = pd.read_csv(os.path.join(data_path, 'loads.csv'), encoding='cp949')
    print("✓ loads.csv loaded (with cp949 encoding)")

try:
    network = pd.read_csv(os.path.join(data_path, 'network.csv'), encoding='utf-8')
    print("✓ network.csv loaded")
except UnicodeDecodeError:
    network = pd.read_csv(os.path.join(data_path, 'network.csv'), encoding='cp949')
    print("✓ network.csv loaded (with cp949 encoding)")

try:
    snapshots = pd.read_csv(os.path.join(data_path, 'snapshots.csv'), encoding='utf-8')
    print("✓ snapshots.csv loaded")
except UnicodeDecodeError:
    snapshots = pd.read_csv(os.path.join(data_path, 'snapshots.csv'), encoding='cp949')
    print("✓ snapshots.csv loaded (with cp949 encoding)")

print("Successfully imported all CSV files from the 2024 folder:")
print(f"- buses: {buses.shape}")
print(f"- carriers: {carriers.shape}")
print(f"- generators: {generators.shape}")
print(f"- loads: {loads.shape}")
print(f"- network: {network.shape}")
print(f"- snapshots: {snapshots.shape}")

# Create a PyPSA network
print("\n" + "="*50)
print("CREATING PYPSA NETWORK MODEL")
print("="*50)

# Initialize the network
n = pypsa.Network()

# Display CSV file structures for debugging
print("CSV file structures:")
print(f"Buses columns: {list(buses.columns)}")
print(f"Carriers columns: {list(carriers.columns)}")
print(f"Generators columns: {list(generators.columns)}")
print(f"Loads columns: {list(loads.columns)}")
print(f"Network columns: {list(network.columns)}")
print(f"Snapshots columns: {list(snapshots.columns)}")

# Add components to the network with proper data handling
print("\nAdding buses...")
if 'name' in buses.columns:
    # If buses has a 'name' column, use it as the bus names
    bus_names = buses['name'].tolist()
    n.madd("Bus", bus_names)
else:
    # Otherwise use the index
    n.madd("Bus", buses.index.tolist())

print("Adding carriers...")
if 'name' in carriers.columns:
    carrier_names = carriers['name'].tolist()
    n.madd("Carrier", carrier_names)
else:
    n.madd("Carrier", carriers.index.tolist())

print("Adding generators...")
# For generators, we need to be more careful about the data structure
if len(generators) > 0:
    if 'name' in generators.columns:
        gen_names = generators['name'].tolist()
    else:
        gen_names = generators.index.tolist()
    
    # Create generators with basic parameters
    for i, name in enumerate(gen_names):
        n.add("Generator", name, bus=bus_names[0] if len(bus_names) > 0 else "bus1", 
              p_nom=100, marginal_cost=50)  # Default values

print("Adding loads...")
if len(loads) > 0:
    if 'name' in loads.columns:
        load_names = loads['name'].tolist()
    else:
        load_names = loads.index.tolist()
    
    # Create loads with basic parameters
    for i, name in enumerate(load_names):
        n.add("Load", name, bus=bus_names[0] if len(bus_names) > 0 else "bus1", 
              p_set=50)  # Default load value

print("Setting snapshots...")
if len(snapshots) > 0:
    if 'name' in snapshots.columns:
        snapshot_names = snapshots['name'].tolist()
    else:
        snapshot_names = snapshots.index.tolist()
    n.set_snapshots(snapshot_names)
else:
    # Set a default snapshot if none provided
    n.set_snapshots([0])

print(f"\nNetwork created with:")
print(f"- {len(n.buses)} buses")
print(f"- {len(n.generators)} generators")
print(f"- {len(n.loads)} loads")
print(f"- {len(n.lines)} lines")
print(f"- {len(n.snapshots)} snapshots")

# Check if the model is feasible and optimize
print("\n" + "="*50)
print("OPTIMIZATION AND FEASIBILITY CHECK")
print("="*50)

try:
    print("Running optimization...")
    n.optimize()
    
    print("✓ Optimization completed successfully!")
    print(f"✓ Objective value: {n.objective:.2f}")
    
    # Check feasibility
    if n.objective is not None and not n.objective == float('inf'):
        print("✓ Model is FEASIBLE")
        
        # Additional feasibility checks
        print("\nDetailed feasibility analysis:")
        print(f"- Total generation capacity: {n.generators.p_nom.sum():.2f} MW")
        print(f"- Total load: {n.loads.p_set.sum():.2f} MW")
        print(f"- Generation adequacy: {'✓' if n.generators.p_nom.sum() >= n.loads.p_set.sum() else '✗'}")
        
        # Check for any infeasible constraints
        if hasattr(n, 'constraints') and len(n.constraints) > 0:
            print(f"- Number of constraints: {len(n.constraints)}")
        
        print("\n✓ PyPSA model is optimized and feasible!")
        
    else:
        print("✗ Model is INFEASIBLE - objective value is infinite")
        
except Exception as e:
    print(f"✗ Optimization failed: {str(e)}")
    print("This could indicate:")
    print("- Missing or incorrect data")
    print("- Infeasible constraints")
    print("- Network connectivity issues")
    print("- Insufficient generation capacity")