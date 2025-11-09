"""
Functions for visualizing PyPSA network results.

This module provides interactive and static visualization of network
optimization results including generation, storage, and load data.
"""
import plotly.express as px
import pandas as pd


def plot_generation_by_carrier(network, snapshots=None, include_storage=True, title='Generation by Carrier', carriers_order=None):
    """
    Create interactive stacked area chart of generation and storage by carrier.

    Includes:
    - Generators: positive generation
    - Storage units: positive discharge (generation), negative charge (storing)

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to plot. If None, uses all snapshots from network.generators_t.p
    include_storage : bool
        If True, includes storage units in the plot (default: True)
    title : str
        Chart title (default: 'Generation by Carrier')
    carriers_order : list or None
        Order of carriers for stacking (first carrier at bottom/baseload, last at top).
        If None, uses default order. Carriers not in the list are appended at the end.

    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Plotly figure

    Example:
    --------
    >>> # After optimization
    >>> fig = plot_generation_by_carrier(network, snapshots=network.snapshots[:48])
    >>> fig.show()
    """
    if snapshots is None:
        # Use all available snapshots from generators_t.p
        if hasattr(network.generators_t, 'p') and network.generators_t.p is not None:
            snapshots = network.generators_t.p.index
        else:
            print("[error] No generator dispatch data (generators_t.p) found")
            return None

    # Get generator dispatch
    gen_data = pd.DataFrame()
    if hasattr(network.generators_t, 'p') and network.generators_t.p is not None:
        gen_dispatch = network.generators_t.p.loc[snapshots]
        # Group by carrier
        gen_by_carrier = gen_dispatch.groupby(network.generators.carrier, axis=1).sum()
        gen_data = gen_by_carrier

    # Get storage unit dispatch (both discharge positive and charge negative)
    storage_discharge_data = pd.DataFrame()
    storage_charge_data = pd.DataFrame()

    if include_storage and len(network.storage_units) > 0:
        if hasattr(network.storage_units_t, 'p') and network.storage_units_t.p is not None:
            storage_dispatch = network.storage_units_t.p.loc[snapshots]

            # Separate discharge (positive) and charge (negative)
            storage_discharge = storage_dispatch.clip(lower=0)  # Only positive values
            storage_charge = storage_dispatch.clip(upper=0)     # Only negative values

            # Group by carrier
            if not storage_discharge.empty:
                storage_discharge_by_carrier = storage_discharge.groupby(network.storage_units.carrier, axis=1).sum()
                storage_discharge_data = storage_discharge_by_carrier

            if not storage_charge.empty:
                storage_charge_by_carrier = storage_charge.groupby(network.storage_units.carrier, axis=1).sum()
                # Rename columns to indicate charging
                storage_charge_by_carrier.columns = [f"{col}_charge" for col in storage_charge_by_carrier.columns]
                storage_charge_data = storage_charge_by_carrier

    # Combine all data
    all_data = []
    if not gen_data.empty:
        all_data.append(gen_data)
    if not storage_discharge_data.empty:
        all_data.append(storage_discharge_data)
    if not storage_charge_data.empty:
        all_data.append(storage_charge_data)

    if not all_data:
        print("[error] No generation or storage dispatch data found")
        return None

    # Concatenate all data
    combined_data = pd.concat(all_data, axis=1)

    # Apply carrier ordering if specified
    # First carrier in config list appears at bottom (baseload), last at top
    # Need to reverse because Plotly stacks in reverse order (first column = top)
    if carriers_order is not None:
        # Get current columns
        current_cols = combined_data.columns.tolist()

        # Reorder columns based on carriers_order (reversed)
        ordered_cols = []
        remaining_cols = current_cols.copy()

        # Reverse the carriers_order so first in config appears at bottom in chart
        for carrier in reversed(carriers_order):
            # Check for exact match or with _charge suffix
            if carrier in remaining_cols:
                ordered_cols.append(carrier)
                remaining_cols.remove(carrier)
            # Check for charge variant
            charge_carrier = f"{carrier}_charge"
            if charge_carrier in remaining_cols:
                ordered_cols.append(charge_carrier)
                remaining_cols.remove(charge_carrier)

        # Add any remaining carriers not in the order list
        ordered_cols.extend(remaining_cols)

        # Reorder DataFrame columns
        combined_data = combined_data[ordered_cols]

    # Convert to long format for Plotly
    combined_data_reset = combined_data.reset_index()
    gen_data_long = combined_data_reset.melt(
        id_vars='snapshot',
        var_name='Carrier',
        value_name='Power (MW)'
    )

    # Create interactive area chart
    fig = px.area(
        gen_data_long,
        x='snapshot',
        y='Power (MW)',
        color='Carrier',
        title=title,
        labels={'snapshot': 'Time'},
        hover_data={'Power (MW)': ':.0f'}
    )

    fig.update_layout(
        hovermode='x unified',
        height=600,
        xaxis_title='Time',
        yaxis_title='Power (MW)'
    )

    print(f"[info] Created generation plot for {len(snapshots)} snapshots")
    print(f"[info] Carriers included: {sorted(combined_data.columns.tolist())}")
    if not storage_discharge_data.empty:
        print(f"[info] Storage discharge carriers: {sorted(storage_discharge_data.columns.tolist())}")
    if not storage_charge_data.empty:
        print(f"[info] Storage charge carriers: {sorted([col.replace('_charge', '') for col in storage_charge_data.columns])}")

    return fig


def plot_storage_state_of_charge(network, snapshots=None, title='Storage State of Charge'):
    """
    Create interactive line chart of storage unit state of charge.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to plot. If None, uses all snapshots from network.storage_units_t.state_of_charge
    title : str
        Chart title (default: 'Storage State of Charge')

    Returns:
    --------
    plotly.graph_objects.Figure or None
        Interactive Plotly figure, or None if no storage units

    Example:
    --------
    >>> fig = plot_storage_state_of_charge(network, snapshots=network.snapshots[:48])
    >>> fig.show()
    """
    if len(network.storage_units) == 0:
        print("[info] No storage units in network")
        return None

    if not hasattr(network.storage_units_t, 'state_of_charge') or network.storage_units_t.state_of_charge is None:
        print("[error] No state_of_charge data found")
        return None

    if snapshots is None:
        snapshots = network.storage_units_t.state_of_charge.index

    # Get state of charge data
    soc_data = network.storage_units_t.state_of_charge.loc[snapshots]

    # Group by carrier and sum
    soc_by_carrier = soc_data.groupby(network.storage_units.carrier, axis=1).sum()

    # Convert to long format
    soc_data_reset = soc_by_carrier.reset_index()
    soc_data_long = soc_data_reset.melt(
        id_vars='snapshot',
        var_name='Carrier',
        value_name='Energy (MWh)'
    )

    # Create line chart
    fig = px.line(
        soc_data_long,
        x='snapshot',
        y='Energy (MWh)',
        color='Carrier',
        title=title,
        labels={'snapshot': 'Time'},
        hover_data={'Energy (MWh)': ':.0f'}
    )

    fig.update_layout(
        hovermode='x unified',
        height=600,
        xaxis_title='Time',
        yaxis_title='Energy (MWh)'
    )

    print(f"[info] Created storage SoC plot for {len(snapshots)} snapshots")

    return fig


def plot_load_and_generation(network, snapshots=None, title='Load vs Generation'):
    """
    Create interactive chart comparing total load and total generation.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to plot. If None, uses all available snapshots
    title : str
        Chart title (default: 'Load vs Generation')

    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Plotly figure

    Example:
    --------
    >>> fig = plot_load_and_generation(network, snapshots=network.snapshots[:48])
    >>> fig.show()
    """
    if snapshots is None:
        snapshots = network.snapshots

    data = {}

    # Get total generation
    if hasattr(network.generators_t, 'p') and network.generators_t.p is not None:
        gen_total = network.generators_t.p.loc[snapshots].sum(axis=1)
        data['Generation'] = gen_total

    # Get total load
    if hasattr(network.loads_t, 'p_set') and network.loads_t.p_set is not None:
        load_total = network.loads_t.p_set.loc[snapshots].sum(axis=1)
        data['Load'] = load_total

    if not data:
        print("[error] No load or generation data found")
        return None

    # Create DataFrame
    df = pd.DataFrame(data, index=snapshots)
    df_reset = df.reset_index()
    df_long = df_reset.melt(
        id_vars='snapshot',
        var_name='Type',
        value_name='Power (MW)'
    )

    # Create line chart
    fig = px.line(
        df_long,
        x='snapshot',
        y='Power (MW)',
        color='Type',
        title=title,
        labels={'snapshot': 'Time'},
        hover_data={'Power (MW)': ':.0f'}
    )

    fig.update_layout(
        hovermode='x unified',
        height=600,
        xaxis_title='Time',
        yaxis_title='Power (MW)'
    )

    return fig
