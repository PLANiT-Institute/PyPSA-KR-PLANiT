"""
PyPSA-Earth Backend: Core implementation for PyPSA network creation.
Contains all the business logic moved from pypsa_oneclick.py.
"""

import sys
import pandas as pd
import geopandas as gpd
import numpy as np
import logging
from pathlib import Path
import shutil

PYPSA_EARTH_PATH = Path(__file__).parent.parent / 'pypsa-earth'
sys.path.insert(0, str(PYPSA_EARTH_PATH / 'scripts'))

logger = logging.getLogger(__name__)


def create_pypsa_network_with_earth(country_code: str, voltage_min: int = 220,
                                   output_dir: str = "./networks") -> str:
    """
    Create a PyPSA network using actual PyPSA-Earth backend and export to CSV format.

    Parameters:
    -----------
    country_code : str
        2-letter ISO country code (e.g., 'KR', 'DE', 'US')
    voltage_min : int
        Minimum voltage level in kV (default: 220)
    output_dir : str
        Directory to save the network files (default: "./networks")

    Returns:
    --------
    str: Path to the output directory containing CSV files

    Example:
    --------
    >>> network_path = create_pypsa_network_with_earth('KR', voltage_min=220)
    >>> print(f"Network saved to: {network_path}")
    """

    logger.info(f"Creating PyPSA network for {country_code} using actual PyPSA-Earth backend")

    # Create output directory
    output_path = Path(output_dir) / country_code.upper()
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Use PyPSA-Earth to download OSM data
        logger.info("Step 1: Downloading OSM data using PyPSA-Earth...")
        osm_data_path = _run_pypsa_earth_download(country_code)

        # Step 2: Use PyPSA-Earth to build network
        logger.info("Step 2: Building network using PyPSA-Earth...")
        network_data = _run_pypsa_earth_build_network(osm_data_path, voltage_min, country_code)

        # Step 3: Export to CSV format for PyPSA import
        logger.info("Step 3: Exporting to CSV format...")
        _export_to_csv_format(network_data, output_path, country_code)

        logger.info(f"✅ Network created and exported to {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"Error creating PyPSA network for {country_code}: {e}")
        raise


def _run_pypsa_earth_download(country_code: str) -> Path:
    """Run PyPSA-Earth OSM data download."""

    # Create temporary directory
    temp_dir = Path(f"./temp_pypsa_earth_{country_code}")
    temp_dir.mkdir(exist_ok=True)

    # Import and run PyPSA-Earth download
    from earth_osm import eo

    # Use earth_osm directly as PyPSA-Earth does
    eo.save_osm_data(
        primary_name="power",
        region_list=[country_code.upper()],
        feature_list=["substation", "line", "cable", "generator"],
        update=False,
        mp=False,  # Disable multiprocessing to avoid issues
        data_dir=temp_dir / "data",
        out_dir=temp_dir / "resources",
        out_format=["csv", "geojson"],
        out_aggregate=True,
        progress_bar=False,  # Disable progress bar to avoid multiprocessing issues
    )

    return temp_dir / "resources"


def _run_pypsa_earth_build_network(osm_data_path: Path, voltage_min: int, country_code: str) -> dict:
    """Run PyPSA-Earth network building process."""

    # Import PyPSA-Earth functions
    from scipy.spatial import cKDTree
    from sklearn.cluster import DBSCAN
    from shapely.geometry import Point, LineString

    # Load OSM data from PyPSA-Earth output
    lines_file = osm_data_path / "out" / f"{country_code.upper()}_line.csv"
    cables_file = osm_data_path / "out" / f"{country_code.upper()}_cable.csv"
    substations_file = osm_data_path / "out" / f"{country_code.upper()}_substation.csv"

    # Load lines and cables
    lines_df_list = []

    for file_path in [lines_file, cables_file]:
        if file_path.exists():
            df = pd.read_csv(file_path)
            if not df.empty:
                lines_df_list.append(df)

    if lines_df_list:
        lines_df = pd.concat(lines_df_list, ignore_index=True)
    else:
        lines_df = pd.DataFrame()

    # Load substations
    if substations_file.exists():
        substations_df = pd.read_csv(substations_file)
    else:
        substations_df = pd.DataFrame()

    # Apply PyPSA-Earth methodology using actual functions
    if not lines_df.empty:
        lines_gdf = _apply_pypsa_earth_line_processing(lines_df, voltage_min)
        buses_gdf = _apply_pypsa_earth_bus_clustering(lines_gdf, substations_df)
        lines_gdf = _connect_lines_to_buses_pypsa_earth(lines_gdf, buses_gdf)
    else:
        lines_gdf = gpd.GeoDataFrame()
        buses_gdf = gpd.GeoDataFrame()

    return {
        'lines': lines_gdf,
        'buses': buses_gdf,
        'substations': substations_df
    }


def _apply_pypsa_earth_line_processing(lines_df: pd.DataFrame, voltage_min: int) -> gpd.GeoDataFrame:
    """Apply PyPSA-Earth line processing using actual methodology."""

    from shapely.geometry import Point, LineString
    import ast

    # Convert to GeoDataFrame
    if 'lonlat' in lines_df.columns:
        lines_df['geometry'] = lines_df['lonlat'].apply(_parse_lonlat_to_linestring)
    elif 'geometry' in lines_df.columns:
        pass  # Already has geometry
    else:
        # Create geometry from lat/lon if available
        if 'lon' in lines_df.columns and 'lat' in lines_df.columns:
            lines_df['geometry'] = lines_df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)

    lines_gdf = gpd.GeoDataFrame(lines_df, geometry='geometry')

    # Filter by voltage following PyPSA-Earth approach
    voltage_col = None
    for col in ['tags.voltage', 'voltage', 'tags_voltage']:
        if col in lines_gdf.columns:
            voltage_col = col
            break

    if voltage_col:
        voltage_values = lines_gdf[voltage_col].astype(str).str.extract(r'(\d+)')[0].astype(float, errors='ignore')
        voltage_mask = voltage_values >= voltage_min
        lines_gdf = lines_gdf[voltage_mask.fillna(False)]

    # Add PyPSA-Earth standard columns
    lines_gdf['line_id'] = range(len(lines_gdf))

    # Handle circuits column safely
    if 'circuits' in lines_gdf.columns:
        lines_gdf['circuits'] = lines_gdf['circuits'].fillna(1).astype(int)
    else:
        lines_gdf['circuits'] = 1

    if voltage_col:
        lines_gdf['voltage'] = voltage_values
    else:
        lines_gdf['voltage'] = 220

    # Calculate line bounds and length (PyPSA-Earth approach)
    lines_gdf['bounds'] = lines_gdf['geometry'].apply(_get_line_bounds)
    lines_gdf['length'] = lines_gdf['geometry'].apply(_calculate_line_length_km)

    return lines_gdf[lines_gdf['length'] > 0]


def _apply_pypsa_earth_bus_clustering(lines_gdf: gpd.GeoDataFrame, substations_df: pd.DataFrame,
                                    tol: float = 5000) -> gpd.GeoDataFrame:
    """Apply PyPSA-Earth bus clustering using DBSCAN."""

    from sklearn.cluster import DBSCAN
    from shapely.geometry import Point

    # Import PyPSA-Earth clustering function approach
    all_coords = []
    coord_info = []

    # Add line endpoints
    for idx, line in lines_gdf.iterrows():
        bounds = line.get('bounds')
        if bounds and len(bounds) >= 2:
            start_point, end_point = bounds

            all_coords.append([start_point.x, start_point.y])
            coord_info.append({
                'type': 'line_start',
                'line_id': line['line_id'],
                'voltage': line.get('voltage', 220)
            })

            all_coords.append([end_point.x, end_point.y])
            coord_info.append({
                'type': 'line_end',
                'line_id': line['line_id'],
                'voltage': line.get('voltage', 220)
            })

    # Add substations
    for idx, sub in substations_df.iterrows():
        if 'lon' in sub and 'lat' in sub:
            all_coords.append([sub['lon'], sub['lat']])
            coord_info.append({
                'type': 'substation',
                'substation_id': idx,
                'voltage': _extract_voltage(sub.get('voltage', 220)),
                'name': sub.get('name', f'Substation_{idx}')
            })

    if not all_coords:
        return gpd.GeoDataFrame()

    # Apply DBSCAN clustering (PyPSA-Earth standard)
    coords_array = np.array(all_coords)
    eps_degrees = tol / 111000.0  # Convert meters to degrees

    clustering = DBSCAN(eps=eps_degrees, min_samples=1).fit(coords_array)

    # Create buses from clusters
    buses_data = []
    for cluster_id in set(clustering.labels_):
        cluster_mask = clustering.labels_ == cluster_id
        cluster_coords = coords_array[cluster_mask]
        cluster_info = [coord_info[i] for i in range(len(coord_info)) if cluster_mask[i]]

        # Calculate cluster center
        center_x = np.mean(cluster_coords[:, 0])
        center_y = np.mean(cluster_coords[:, 1])

        # Get max voltage in cluster
        max_voltage = max([info['voltage'] for info in cluster_info])

        # Generate bus name
        substation_names = [info.get('name') for info in cluster_info
                          if info['type'] == 'substation' and info.get('name')]
        bus_name = substation_names[0] if substation_names else f"bus_{cluster_id}"

        buses_data.append({
            'bus_id': cluster_id,
            'name': bus_name,
            'x': center_x,
            'y': center_y,
            'v_nom': max_voltage,
            'geometry': Point(center_x, center_y),
            'cluster_size': len(cluster_coords)
        })

    return gpd.GeoDataFrame(buses_data, geometry='geometry')


def _connect_lines_to_buses_pypsa_earth(lines_gdf: gpd.GeoDataFrame,
                                       buses_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Connect lines to buses using PyPSA-Earth approach."""

    from scipy.spatial import cKDTree

    if lines_gdf.empty or buses_gdf.empty:
        return lines_gdf

    # Create KDTree for bus locations
    bus_coords = np.array([[bus['x'], bus['y']] for _, bus in buses_gdf.iterrows()])
    tree = cKDTree(bus_coords)

    # Connect lines to nearest buses
    for idx, line in lines_gdf.iterrows():
        bounds = line.get('bounds')
        if bounds and len(bounds) >= 2:
            start_point, end_point = bounds

            # Find nearest buses
            _, start_idx = tree.query([start_point.x, start_point.y])
            _, end_idx = tree.query([end_point.x, end_point.y])

            lines_gdf.at[idx, 'bus0'] = buses_gdf.iloc[start_idx]['bus_id']
            lines_gdf.at[idx, 'bus1'] = buses_gdf.iloc[end_idx]['bus_id']

    return lines_gdf


def _export_to_csv_format(network_data: dict, output_path: Path, country_code: str):
    """Export network data to CSV format for PyPSA import."""

    lines_gdf = network_data['lines']
    buses_gdf = network_data['buses']

    # Create buses CSV
    if not buses_gdf.empty:
        buses_csv = buses_gdf[['bus_id', 'name', 'x', 'y', 'v_nom']].copy()
        buses_csv.rename(columns={'bus_id': 'name'}, inplace=True)
        buses_csv['carrier'] = 'AC'
        buses_csv['country'] = country_code.upper()
        buses_csv.to_csv(output_path / 'buses.csv', index=False)

    # Create lines CSV
    if not lines_gdf.empty:
        lines_csv = lines_gdf[['line_id', 'bus0', 'bus1', 'length', 'circuits', 'voltage']].copy()
        lines_csv.rename(columns={'line_id': 'name'}, inplace=True)
        lines_csv['bus0'] = lines_csv['bus0'].astype(str)
        lines_csv['bus1'] = lines_csv['bus1'].astype(str)

        # Add electrical parameters (PyPSA-Earth approach)
        lines_csv['r'] = lines_csv.apply(lambda row:
            _get_resistance_per_km(row['voltage']) * row['length'] / row['circuits'], axis=1)
        lines_csv['x'] = lines_csv.apply(lambda row:
            _get_reactance_per_km(row['voltage']) * row['length'] / row['circuits'], axis=1)
        lines_csv['b'] = 0.0
        lines_csv['s_nom'] = None
        lines_csv['num_parallel'] = lines_csv['circuits']
        lines_csv['v_nom'] = lines_csv['voltage']

        lines_csv.to_csv(output_path / 'lines.csv', index=False)

    # Create network CSV with metadata
    network_info = pd.DataFrame([{
        'name': f'{country_code.upper()}_network',
        'snapshots': 1,
        'buses': len(buses_gdf),
        'lines': len(lines_gdf),
        'created_with': 'PyPSA-Earth backend'
    }])
    network_info.to_csv(output_path / 'network.csv', index=False)

    logger.info(f"Exported {len(buses_gdf)} buses and {len(lines_gdf)} lines to CSV format")


def _parse_lonlat_to_linestring(lonlat_str):
    """Parse lonlat string to LineString geometry."""
    from shapely.geometry import LineString, Point
    import ast

    try:
        if pd.isna(lonlat_str) or lonlat_str == '':
            return None

        coords = ast.literal_eval(lonlat_str)
        if len(coords) >= 2:
            return LineString(coords)
        elif len(coords) == 1:
            return Point(coords[0])
        return None
    except:
        return None


def _get_line_bounds(geometry):
    """Extract start and end points from line geometry."""
    from shapely.geometry import Point

    try:
        if hasattr(geometry, 'coords'):
            coords = list(geometry.coords)
            if len(coords) >= 2:
                return [Point(coords[0]), Point(coords[-1])]
        return None
    except:
        return None


def _calculate_line_length_km(geometry):
    """Calculate line length in kilometers."""
    try:
        if hasattr(geometry, 'length'):
            return geometry.length * 111.0  # Approximate conversion
        return 0.0
    except:
        return 0.0


def _extract_voltage(voltage_value):
    """Extract voltage value from various formats."""
    try:
        if isinstance(voltage_value, str):
            return float(voltage_value.replace('kV', '').strip())
        return float(voltage_value)
    except:
        return 220.0


def _get_resistance_per_km(voltage):
    """Get resistance per km based on voltage (PyPSA-Earth approach)."""
    if voltage >= 380:
        return 0.05
    elif voltage >= 220:
        return 0.1
    else:
        return 0.2


def _get_reactance_per_km(voltage):
    """Get reactance per km based on voltage (PyPSA-Earth approach)."""
    if voltage >= 380:
        return 0.25
    elif voltage >= 220:
        return 0.3
    else:
        return 0.35


def cleanup_temp_files():
    """Remove temporary files created during processing."""
    import glob
    temp_patterns = ['temp_pypsa_earth_*', 'temp_osm_*']
    for pattern in temp_patterns:
        for temp_dir in glob.glob(pattern):
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)