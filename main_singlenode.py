import pypsa

n = pypsa.Network()

n.import_from_csv_folder("data/2024")

# Get the single bus to use for the entire network
single_bus = n.buses.index[0]

# Convert all components to use the single bus
for component in n.iterate_components():
    if 'bus' in component.df.columns:
        component.df['bus'] = single_bus
    if 'bus0' in component.df.columns:
        component.df['bus0'] = single_bus
    if 'bus1' in component.df.columns:
        component.df['bus1'] = single_bus


# # Keep only the single bus, remove all others
# buses_to_remove = [bus for bus in n.buses.index if bus != single_bus]
# n.mremove("Bus", buses_to_remove)
