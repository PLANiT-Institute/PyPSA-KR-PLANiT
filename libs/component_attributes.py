"""
Functions to apply attributes to network components (generators, storage_units, etc.).

This module handles setting operational parameters and characteristics
for different component types based on their carrier.
"""


def apply_generator_attributes(network, generator_attributes):
    """
    Apply carrier-specific attributes to generators from config.

    This should be called AFTER standardize_carrier_names() so that generators
    have the new standardized carrier names.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    generator_attributes : dict
        Dictionary mapping carrier names to their attributes
        Special carrier name 'default' applies to all generators that don't have
        carrier-specific values.
        Example:
        {
            'default': {'ramp_limit_up': 100, 'ramp_limit_down': 100},
            'gas': {'p_min_pu': 0.2, 'p_max_pu': 1.0},
            'coal': {'p_min_pu': 0.2, 'p_max_pu': 1.0}
        }

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    if not generator_attributes:
        print("[warn] No generator_attributes provided, skipping")
        return network

    print(f"[info] Applying carrier-specific generator attributes...")

    # Step 1: Apply default values to ALL generators (if 'default' exists)
    if 'default' in generator_attributes:
        default_attrs = generator_attributes['default']
        print(f"[info] Applying default attributes to ALL generators:")
        for attr, value in default_attrs.items():
            # Skip p_max_pu if time-series version exists (don't overwrite time-series data!)
            if attr == 'p_max_pu' and hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
                print(f"  - {attr}: skipped (time-series exists)")
                continue
            network.generators[attr] = value
            print(f"  - {attr} = {value}")

    # Step 2: Apply carrier-specific values (overrides defaults)
    updated_count = 0
    for carrier, attributes in generator_attributes.items():
        # Skip the 'default' entry
        if carrier == 'default':
            continue

        # Find generators with this carrier
        carrier_gens = network.generators[network.generators['carrier'] == carrier].index

        if len(carrier_gens) == 0:
            print(f"[info] No generators found for carrier '{carrier}', skipping")
            continue

        print(f"[info] Applying attributes to {len(carrier_gens)} {carrier} generators:")
        for attr, value in attributes.items():
            # Skip p_max_pu if time-series version exists (don't overwrite time-series data!)
            if attr == 'p_max_pu' and hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
                print(f"  - {attr}: skipped (time-series exists)")
                continue
            # Apply the attribute to all generators of this carrier
            network.generators.loc[carrier_gens, attr] = value
            print(f"  - {attr} = {value}")
            updated_count += 1

    print(f"[info] Applied {updated_count} carrier-specific attribute updates")
    return network


def apply_storage_unit_attributes(network, storage_unit_attributes):
    """
    Apply carrier-specific attributes to storage_units from config.

    This should be called AFTER standardize_carrier_names() so that storage_units
    have the new standardized carrier names.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object (modified in place)
    storage_unit_attributes : dict
        Dictionary mapping carrier names to their attributes
        Special carrier name 'default' applies to all storage_units that don't have
        carrier-specific values.
        Example:
        {
            'default': {'efficiency_store': 0.95, 'efficiency_dispatch': 0.95},
            'battery': {'max_hours': 4, 'efficiency_store': 0.9, 'efficiency_dispatch': 0.9},
            'PSH': {'max_hours': 8, 'efficiency_store': 0.85, 'efficiency_dispatch': 0.85}
        }

    Returns:
    --------
    pypsa.Network : The modified network (same object as input)
    """
    if not storage_unit_attributes:
        print("[warn] No storage_unit_attributes provided, skipping")
        return network

    if len(network.storage_units) == 0:
        print("[info] No storage_units in network, skipping")
        return network

    print(f"[info] Applying carrier-specific storage_unit attributes...")

    # Step 1: Apply default values to ALL storage_units (if 'default' exists)
    if 'default' in storage_unit_attributes:
        default_attrs = storage_unit_attributes['default']
        print(f"[info] Applying default attributes to ALL storage_units:")
        for attr, value in default_attrs.items():
            network.storage_units[attr] = value
            print(f"  - {attr} = {value}")

    # Step 2: Apply carrier-specific values (overrides defaults)
    updated_count = 0
    for carrier, attributes in storage_unit_attributes.items():
        # Skip the 'default' entry
        if carrier == 'default':
            continue

        # Find storage_units with this carrier
        carrier_sus = network.storage_units[network.storage_units['carrier'] == carrier].index

        if len(carrier_sus) == 0:
            print(f"[info] No storage_units found for carrier '{carrier}', skipping")
            continue

        print(f"[info] Applying attributes to {len(carrier_sus)} {carrier} storage_units:")
        for attr, value in attributes.items():
            # Apply the attribute to all storage_units of this carrier
            network.storage_units.loc[carrier_sus, attr] = value
            print(f"  - {attr} = {value}")
            updated_count += 1

    print(f"[info] Applied {updated_count} carrier-specific storage_unit attribute updates")
    return network
