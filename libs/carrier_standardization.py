"""
Functions to standardize carrier names across network components.

This module handles mapping original carrier names from data files
to standardized carrier names for consistent analysis.
"""
import pandas as pd


def standardize_carrier_names(network, carrier_mapping):
    """
    Standardize carrier names across all network components using carrier mapping.

    This ensures all components use consistent carrier names from the config.
    Updates:
    - network.generators['carrier']
    - network.storage_units['carrier']
    - network.carriers (adds new carriers, removes unused old ones)
    - Any other components with 'carrier' column

    Should be called BEFORE applying monthly/snapshot data or regional aggregation.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    carrier_mapping : dict
        Mapping from old carrier names to new carrier names (from config)

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    if not carrier_mapping:
        print("[warn] No carrier_mapping provided, skipping carrier standardization")
        return network

    print(f"[info] Standardizing carrier names across all network components...")

    # Collect all unique carriers from the mapping
    old_carriers_in_mapping = set(carrier_mapping.keys())
    new_carriers_in_mapping = set(carrier_mapping.values())

    # Step 1: Update all components with 'carrier' column
    components_updated = {}

    for component_name in ['generators', 'loads', 'storage_units', 'stores', 'links', 'buses']:
        component = getattr(network, component_name, None)
        if component is None or not hasattr(component, 'columns'):
            continue

        if 'carrier' not in component.columns:
            continue

        if len(component) == 0:
            continue

        updated_count = 0
        for idx in component.index:
            old_carrier = component.loc[idx, 'carrier']
            if pd.notna(old_carrier) and old_carrier != '':
                new_carrier = carrier_mapping.get(old_carrier, old_carrier)
                if new_carrier != old_carrier:
                    component.loc[idx, 'carrier'] = new_carrier
                    updated_count += 1

        if updated_count > 0:
            components_updated[component_name] = updated_count

    # Step 2: Update network.carriers table
    # Get all carriers actually used in the network after mapping
    carriers_in_use = set()

    for component_name in ['generators', 'loads', 'storage_units', 'stores', 'links', 'buses']:
        component = getattr(network, component_name, None)
        if component is None or not hasattr(component, 'columns'):
            continue
        if 'carrier' not in component.columns or len(component) == 0:
            continue

        component_carriers = component['carrier'].dropna()
        component_carriers = component_carriers[component_carriers != '']
        carriers_in_use.update(component_carriers.unique())

    # Add new carriers that don't exist yet
    carriers_to_add = carriers_in_use - set(network.carriers.index)
    for carrier in carriers_to_add:
        print(f"[info] Adding new carrier '{carrier}' to network.carriers")
        network.add("Carrier", carrier)

    # Remove old carriers that are no longer used
    carriers_to_remove = set(network.carriers.index) - carriers_in_use
    # Don't remove carriers if they're still referenced (safety check)
    carriers_to_remove = carriers_to_remove & old_carriers_in_mapping

    for carrier in carriers_to_remove:
        if carrier in network.carriers.index:
            print(f"[info] Removing unused carrier '{carrier}' from network.carriers")
            network.remove("Carrier", carrier)

    # Print summary
    print(f"[info] Carrier standardization complete:")
    for component_name, count in components_updated.items():
        print(f"  - Updated {count} {component_name}")
    print(f"  - network.carriers now has: {sorted(network.carriers.index)}")

    return network
