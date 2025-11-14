"""
Functions for visualizing PyPSA network results.

This module provides interactive and static visualization of network
optimization results including generation, storage, and load data.
"""
import plotly.express as px
import plotly.graph_objects as go
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


def plot_transmission_flows(network, snapshots=None, component='lines', top_n=10, title=None):
    """
    Create interactive chart showing energy flows in transmission lines or links.

    Displays power flows between buses over time. Shows the absolute flow values
    (magnitude of power transfer regardless of direction).

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to plot. If None, uses all available snapshots
    component : str
        Type of component to visualize: 'lines' or 'links' (default: 'lines')
    top_n : int or None
        Number of transmission components with highest total energy to display.
        If None, shows all components (default: 10)
    title : str or None
        Chart title. If None, generates default title based on component type

    Returns:
    --------
    plotly.graph_objects.Figure or None
        Interactive Plotly figure, or None if no data available

    Example:
    --------
    >>> # Show top 10 inter-provincial line flows
    >>> fig = plot_transmission_flows(network, snapshots=network.snapshots[:48], component='lines', top_n=10)
    >>> fig.show()

    >>> # Show all link flows
    >>> fig = plot_transmission_flows(network, component='links', top_n=None)
    >>> fig.show()
    """
    if component not in ['lines', 'links']:
        print(f"[error] component must be 'lines' or 'links', got '{component}'")
        return None

    # Get component DataFrame and time-series data
    if component == 'lines':
        if len(network.lines) == 0:
            print("[info] No lines in network")
            return None

        if not hasattr(network.lines_t, 'p0') or network.lines_t.p0 is None:
            print("[error] No line flow data (lines_t.p0) found")
            return None

        comp_df = network.lines
        flow_data = network.lines_t.p0
        default_title = 'Transmission Line Flows'

    else:  # links
        if len(network.links) == 0:
            print("[info] No links in network")
            return None

        if not hasattr(network.links_t, 'p0') or network.links_t.p0 is None:
            print("[error] No link flow data (links_t.p0) found")
            return None

        comp_df = network.links
        flow_data = network.links_t.p0
        default_title = 'Link Flows'

    # Set snapshots
    if snapshots is None:
        snapshots = flow_data.index

    # Get flow data for selected snapshots
    flow_subset = flow_data.loc[snapshots]

    # Calculate total energy (absolute value) for each component
    total_energy = flow_subset.abs().sum()

    if total_energy.sum() == 0:
        print(f"[info] No {component} flow detected in selected snapshots")
        return None

    # Select top_n components by total energy if specified
    if top_n is not None and top_n < len(total_energy):
        top_components = total_energy.nlargest(top_n).index
        flow_subset = flow_subset[top_components]
        print(f"[info] Showing top {top_n} {component} with highest energy flows")
    else:
        top_components = total_energy.index
        print(f"[info] Showing all {len(top_components)} {component}")

    # Create labels with bus0 -> bus1 format
    labels = {}
    for comp_name in top_components:
        bus0 = comp_df.loc[comp_name, 'bus0']
        bus1 = comp_df.loc[comp_name, 'bus1']
        labels[comp_name] = f"{bus0} → {bus1}"

    # Rename columns with descriptive labels
    flow_labeled = flow_subset.rename(columns=labels)

    # Take absolute values for visualization (show magnitude of flow)
    flow_abs = flow_labeled.abs()

    # Convert to long format for Plotly
    flow_reset = flow_abs.reset_index()
    flow_long = flow_reset.melt(
        id_vars='snapshot',
        var_name='Route',
        value_name='Power (MW)'
    )

    # Create line chart
    fig = px.line(
        flow_long,
        x='snapshot',
        y='Power (MW)',
        color='Route',
        title=title if title else default_title,
        labels={'snapshot': 'Time'},
        hover_data={'Power (MW)': ':.0f'}
    )

    fig.update_layout(
        hovermode='x unified',
        height=600,
        xaxis_title='Time',
        yaxis_title='Power (MW)',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )

    # Print summary statistics
    print(f"[info] Created {component} flow plot for {len(snapshots)} snapshots")
    print(f"[info] Total energy transferred:")
    for route, energy in total_energy.loc[top_components].sort_values(ascending=False).items():
        bus0 = comp_df.loc[route, 'bus0']
        bus1 = comp_df.loc[route, 'bus1']
        print(f"  {bus0} → {bus1}: {energy:,.0f} MWh")

    return fig


def plot_transmission_flows_map(network, snapshots=None, component='links', top_n=20, title=None):
    """
    Create interactive map showing energy flows between provinces/regions.

    Displays transmission flows as lines on a map with thickness proportional
    to total energy transferred. Bus positions are read from network.buses
    (x=longitude, y=latitude coordinates).

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to plot. If None, uses all available snapshots
    component : str
        Type of component to visualize: 'lines' or 'links' (default: 'links')
    top_n : int or None
        Number of transmission components with highest total energy to display.
        If None, shows all components (default: 20)
    title : str or None
        Chart title. If None, generates default title based on component type

    Returns:
    --------
    plotly.graph_objects.Figure or None
        Interactive Plotly map figure, or None if no data available

    Example:
    --------
    >>> # Show top 20 inter-provincial flows on map
    >>> fig = plot_transmission_flows_map(network, snapshots=network.snapshots[:48], component='links', top_n=20)
    >>> fig.show()
    """
    if component not in ['lines', 'links']:
        print(f"[error] component must be 'lines' or 'links', got '{component}'")
        return None

    # Get component DataFrame and time-series data
    if component == 'lines':
        if len(network.lines) == 0:
            print("[info] No lines in network")
            return None

        if not hasattr(network.lines_t, 'p0') or network.lines_t.p0 is None:
            print("[error] No line flow data (lines_t.p0) found")
            return None

        comp_df = network.lines
        flow_data = network.lines_t.p0
        default_title = 'Transmission Line Flows Map'

    else:  # links
        if len(network.links) == 0:
            print("[info] No links in network")
            return None

        if not hasattr(network.links_t, 'p0') or network.links_t.p0 is None:
            print("[error] No link flow data (links_t.p0) found")
            return None

        comp_df = network.links
        flow_data = network.links_t.p0
        default_title = 'Link Flows Map'

    # Check if buses have coordinates
    if 'x' not in network.buses.columns or 'y' not in network.buses.columns:
        print("[error] Bus coordinates (x=longitude, y=latitude) not found in network.buses")
        return None

    # Set snapshots
    if snapshots is None:
        snapshots = flow_data.index

    # Get flow data for selected snapshots
    flow_subset = flow_data.loc[snapshots]

    # Calculate total energy (absolute value) for each component
    total_energy = flow_subset.abs().sum()

    if total_energy.sum() == 0:
        print(f"[info] No {component} flow detected in selected snapshots")
        return None

    # Select top_n components by total energy if specified
    if top_n is not None and top_n < len(total_energy):
        top_components = total_energy.nlargest(top_n).index
        print(f"[info] Showing top {top_n} {component} with highest energy flows")
    else:
        top_components = total_energy.index
        print(f"[info] Showing all {len(top_components)} {component}")

    # Create figure
    fig = go.Figure()

    # Add transmission lines/links
    max_energy = total_energy.loc[top_components].max()

    for comp_name in top_components:
        bus0_name = comp_df.loc[comp_name, 'bus0']
        bus1_name = comp_df.loc[comp_name, 'bus1']
        energy = total_energy.loc[comp_name]

        # Get bus coordinates
        if bus0_name not in network.buses.index or bus1_name not in network.buses.index:
            continue

        lon0 = network.buses.loc[bus0_name, 'x']
        lat0 = network.buses.loc[bus0_name, 'y']
        lon1 = network.buses.loc[bus1_name, 'x']
        lat1 = network.buses.loc[bus1_name, 'y']

        # Calculate line width based on energy (normalized)
        line_width = 1 + (energy / max_energy) * 10  # Scale from 1 to 11

        # Add line for this connection
        fig.add_trace(go.Scattergeo(
            lon=[lon0, lon1],
            lat=[lat0, lat1],
            mode='lines',
            line=dict(width=line_width, color='rgba(255, 0, 0, 0.6)'),
            hovertemplate=(
                f"<b>{bus0_name} → {bus1_name}</b><br>"
                f"Total Energy: {energy:,.0f} MWh<br>"
                "<extra></extra>"
            ),
            showlegend=False
        ))

    # Add bus markers
    bus_names = []
    bus_lons = []
    bus_lats = []

    # Get all unique buses involved in flows
    involved_buses = set()
    for comp_name in top_components:
        involved_buses.add(comp_df.loc[comp_name, 'bus0'])
        involved_buses.add(comp_df.loc[comp_name, 'bus1'])

    for bus_name in involved_buses:
        if bus_name in network.buses.index:
            bus_names.append(bus_name)
            bus_lons.append(network.buses.loc[bus_name, 'x'])
            bus_lats.append(network.buses.loc[bus_name, 'y'])

    # Add bus markers
    fig.add_trace(go.Scattergeo(
        lon=bus_lons,
        lat=bus_lats,
        mode='markers+text',
        marker=dict(size=12, color='blue', symbol='circle'),
        text=bus_names,
        textposition='top center',
        textfont=dict(size=10, color='black'),
        hovertemplate='<b>%{text}</b><extra></extra>',
        showlegend=False
    ))

    # Update layout for Korea map
    fig.update_layout(
        title=title if title else default_title,
        geo=dict(
            scope='asia',
            center=dict(lat=36.5, lon=127.5),  # Center of South Korea
            projection_scale=20,  # Zoom level
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            showcountries=True,
            countrycolor='rgb(204, 204, 204)',
        ),
        height=800,
        width=900
    )

    print(f"[info] Created {component} flow map for {len(snapshots)} snapshots")
    print(f"[info] Top flows displayed:")
    for route, energy in total_energy.loc[top_components].sort_values(ascending=False).head(10).items():
        bus0 = comp_df.loc[route, 'bus0']
        bus1 = comp_df.loc[route, 'bus1']
        print(f"  {bus0} → {bus1}: {energy:,.0f} MWh")

    return fig


def plot_link_and_line_flows(network, snapshots=None, title='Link and Line Flow Over Time'):
    """
    Create interactive line chart showing link and line flows over time.

    Each link and line is displayed as a separate line trace with different colors.
    Positive values indicate flow in the bus0 → bus1 direction, negative values
    indicate reverse flow.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to plot. If None, uses all available snapshots
    title : str
        Chart title (default: 'Link and Line Flow Over Time')

    Returns:
    --------
    plotly.graph_objects.Figure or None
        Interactive Plotly figure, or None if no link or line flow data available

    Example:
    --------
    >>> # After optimization
    >>> fig = plot_link_and_line_flows(network, snapshots=network.snapshots[:48])
    >>> if fig:
    >>>     fig.show()
    """
    # Create figure
    flow_fig = go.Figure()
    has_data = False

    # Add link flows to chart
    if len(network.links) > 0 and hasattr(network, 'links_t') and hasattr(network.links_t, 'p0'):
        try:
            p0_df = network.links_t.p0
            if len(p0_df) > 0:
                # Use provided snapshots or all available
                if snapshots is None:
                    snapshots = p0_df.index

                for link_idx in network.links.index:
                    if link_idx in p0_df.columns:
                        flow_series = p0_df.loc[snapshots, link_idx]
                        bus0 = network.links.at[link_idx, 'bus0']
                        bus1 = network.links.at[link_idx, 'bus1']

                        flow_fig.add_trace(go.Scatter(
                            x=snapshots,
                            y=flow_series,
                            mode='lines',
                            name=f'Link: {bus0} → {bus1}',
                            line=dict(width=2),
                            hovertemplate='%{y:.2f} MW<extra></extra>'
                        ))
                        has_data = True

                print(f"[info] Added {len(network.links)} links to flow chart")
        except Exception as e:
            print(f"[warn] Could not plot link flows: {e}")

    # Add line flows to chart (if lines exist)
    if len(network.lines) > 0 and hasattr(network, 'lines_t') and hasattr(network.lines_t, 'p0'):
        try:
            lines_p0_df = network.lines_t.p0
            if len(lines_p0_df) > 0:
                # Use provided snapshots or all available
                if snapshots is None:
                    snapshots = lines_p0_df.index

                for line_idx in network.lines.index:
                    if line_idx in lines_p0_df.columns:
                        flow_series = lines_p0_df.loc[snapshots, line_idx]
                        bus0 = network.lines.at[line_idx, 'bus0']
                        bus1 = network.lines.at[line_idx, 'bus1']

                        flow_fig.add_trace(go.Scatter(
                            x=snapshots,
                            y=flow_series,
                            mode='lines',
                            name=f'Line: {bus0} → {bus1}',
                            line=dict(width=2, dash='dot'),
                            hovertemplate='%{y:.2f} MW<extra></extra>'
                        ))
                        has_data = True

                print(f"[info] Added {len(network.lines)} lines to flow chart")
        except Exception as e:
            print(f"[warn] Could not plot line flows: {e}")

    # Return None if no data was added
    if not has_data:
        print("[warn] No link or line flow data to plot")
        return None

    # Update layout
    flow_fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Power Flow (MW)',
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        height=500
    )

    return flow_fig


def print_link_and_line_flow_analysis(network, snapshots=None):
    """
    Print detailed analysis of link and line flows including capacity configuration
    and flow statistics.

    Parameters:
    -----------
    network : pypsa.Network
        PyPSA network object with optimization results
    snapshots : pd.Index or None
        Snapshots to analyze. If None, uses all available snapshots

    Example:
    --------
    >>> # After optimization
    >>> print_link_and_line_flow_analysis(network, snapshots=network.snapshots[:48])
    """
    # Analyze links
    if len(network.links) > 0:
        print(f"\nTotal links in network: {len(network.links)}")
        print("\n--- Link Capacity and Configuration ---")

        # Display link configuration
        for link_idx in network.links.index:
            bus0 = network.links.at[link_idx, 'bus0']
            bus1 = network.links.at[link_idx, 'bus1']
            p_nom = network.links.at[link_idx, 'p_nom']
            efficiency = network.links.at[link_idx, 'efficiency']
            print(f"{link_idx}: {bus0} → {bus1}, p_nom={p_nom:.0f} MW, eff={efficiency:.3f}", end="")

            if 'p_min_pu' in network.links.columns:
                p_min_pu = network.links.at[link_idx, 'p_min_pu']
                if p_min_pu < 0:
                    print(f", bidirectional (p_min_pu={p_min_pu:.1f})")
                else:
                    print()
            else:
                print()

        # Show link flow statistics
        if hasattr(network, 'links_t') and hasattr(network.links_t, 'p0'):
            try:
                p0_df = network.links_t.p0
                if len(p0_df) > 0:
                    print("\n--- Link Flow Statistics (over optimization period) ---")

                    # Use provided snapshots or all available
                    if snapshots is None:
                        snapshots = p0_df.index

                    for link_idx in network.links.index:
                        if link_idx in p0_df.columns:
                            # Get flow data for this link
                            flow_series = p0_df.loc[snapshots, link_idx]

                            bus0 = network.links.at[link_idx, 'bus0']
                            bus1 = network.links.at[link_idx, 'bus1']
                            p_nom = network.links.at[link_idx, 'p_nom']

                            mean_flow = flow_series.mean()
                            max_flow = flow_series.max()
                            min_flow = flow_series.min()
                            utilization = abs(flow_series).max() / p_nom * 100

                            print(f"\n{link_idx}:")
                            print(f"  Direction: {bus0} → {bus1}")
                            print(f"  Capacity: {p_nom:.0f} MW")
                            print(f"  Mean flow: {mean_flow:.2f} MW")
                            print(f"  Max flow: {max_flow:.2f} MW (forward)")
                            print(f"  Min flow: {min_flow:.2f} MW {'(reverse)' if min_flow < 0 else ''}")
                            print(f"  Utilization: {utilization:.1f}%")
                        else:
                            print(f"\n{link_idx}: No flow data available")
                else:
                    print("\n[warn] No link flow data available (empty DataFrame)")
            except Exception as e:
                print(f"\n[error] Could not retrieve link flow data: {e}")
        else:
            print("\n[warn] No link flow data available")
    else:
        print("\nNo links in the network")

    # Analyze lines
    if len(network.lines) > 0:
        print(f"\n\nTotal lines in network: {len(network.lines)}")
        print("\n--- Line Capacity and Configuration ---")

        # Display line configuration
        for line_idx in network.lines.index:
            bus0 = network.lines.at[line_idx, 'bus0']
            bus1 = network.lines.at[line_idx, 'bus1']
            s_nom = network.lines.at[line_idx, 's_nom']
            print(f"{line_idx}: {bus0} → {bus1}, s_nom={s_nom:.0f} MVA")

        # Show line flow statistics
        if hasattr(network, 'lines_t') and hasattr(network.lines_t, 'p0'):
            try:
                lines_p0_df = network.lines_t.p0
                if len(lines_p0_df) > 0:
                    print("\n--- Line Flow Statistics (over optimization period) ---")

                    # Use provided snapshots or all available
                    if snapshots is None:
                        snapshots = lines_p0_df.index

                    for line_idx in network.lines.index:
                        if line_idx in lines_p0_df.columns:
                            # Get flow data for this line
                            flow_series = lines_p0_df.loc[snapshots, line_idx]

                            bus0 = network.lines.at[line_idx, 'bus0']
                            bus1 = network.lines.at[line_idx, 'bus1']
                            s_nom = network.lines.at[line_idx, 's_nom']

                            mean_flow = flow_series.mean()
                            max_flow = flow_series.max()
                            min_flow = flow_series.min()
                            utilization = abs(flow_series).max() / s_nom * 100

                            print(f"\n{line_idx}:")
                            print(f"  Direction: {bus0} → {bus1}")
                            print(f"  Capacity: {s_nom:.0f} MVA")
                            print(f"  Mean flow: {mean_flow:.2f} MW")
                            print(f"  Max flow: {max_flow:.2f} MW (forward)")
                            print(f"  Min flow: {min_flow:.2f} MW {'(reverse)' if min_flow < 0 else ''}")
                            print(f"  Utilization: {utilization:.1f}%")
                        else:
                            print(f"\n{line_idx}: No flow data available")
                else:
                    print("\n[warn] No line flow data available (empty DataFrame)")
            except Exception as e:
                print(f"\n[error] Could not retrieve line flow data: {e}")
        else:
            print("\n[warn] No line flow data available")
