# Utils Directory

This directory contains utility scripts for the PyPSA Alternative project.

## Interactive GUI

**utils_gui.py** - Graphical interface to run all 8 utilities with a click

```bash
# Launch GUI
python utils_gui.py

# Or use launchers
./run_utils_gui.sh        # macOS/Linux
run_utils_gui.bat         # Windows
```

The GUI provides:
- 8 tabs - one for each utility
- Point-and-click interface
- Real-time output console
- No command-line knowledge required
- All utilities in one window

**Available Tools:**
1. 📍 Geocoding - Add coordinates to CSV files
2. 🌍 Network Download - Download power network data
3. 📊 CSV→Excel - Convert CSV to Excel format
4. 🔤 Encoding - Convert EUC-KR/CP949 to UTF-8
5. ⚡ Add CC Groups - Add combined cycle group names
6. 🔗 Merge CC - Merge CC generators by group
7. 🗺️ Expand Mainland - Expand 육지 data to provinces
8. 🏷️ Unique Names - Make name column unique

See `../doc/GUI_README.md` for full GUI documentation.

## Available Utilities

### 1. download_pypsa_earth.py

Downloads and processes PyPSA-Earth network data for any country.

**Requirements:**
- PyPSA-Earth must be installed in `pypsa-earth/` directory (see main SETUP.md)
- All dependencies from requirements.txt

**Usage:**
```bash
# Download network for South Korea (220 kV and above)
python download_pypsa_earth.py KR --voltage-min 220

# Download network for Germany
python download_pypsa_earth.py DE --voltage-min 220 --output-dir ./networks/germany

# Enable verbose logging
python download_pypsa_earth.py KR --verbose
```

**Arguments:**
- `country_code`: 2-letter ISO country code (required)
- `--voltage-min`: Minimum voltage level in kV (default: 220)
- `--output-dir`: Output directory (default: ./networks)
- `--verbose, -v`: Enable verbose logging

**Output:**
Creates CSV files in the output directory:
- `buses.csv`: Network buses with coordinates
- `lines.csv`: Network lines with electrical parameters
- `network.csv`: Network metadata

### 2. geocode_addresses.py

Geocodes addresses in CSV files and adds x, y coordinates.

**Requirements:**
- Internet connection (uses Nominatim API)
- CSV files with address column

**Usage:**
```bash
# Basic geocoding
python geocode_addresses.py data/2024

# With custom address column
python geocode_addresses.py data/2024 --address-column province

# Auto-detect duplicate locations and prompt for jitter
python geocode_addresses.py data/2024 --jitter auto

# Apply 5 km jitter to coordinates
python geocode_addresses.py data/2024 --jitter jitter-5

# Apply 1 km jitter (numeric format)
python geocode_addresses.py data/2024 --jitter 1

# Overwrite existing coordinates
python geocode_addresses.py data/2024 --overwrite
```

**Arguments:**
- `folder`: Folder containing CSV files (required)
- `--address-column`: Column name for addresses (default: 'address')
- `--overwrite`: Overwrite existing coordinates
- `--jitter`: Add jitter to coordinates
  - `auto`: Prompt if all locations are identical
  - `jitter-X`: Apply X km jitter
  - `numeric`: Apply that many km jitter
- `--cache-file`: Cache file path (default: cache/geocode_cache.json)
- `--pattern`: File pattern to match (default: *.csv)

**Jitter Feature:**
When all geocoded locations are identical (e.g., all addresses resolve to the same city center), you can add random jitter to spread them out:
- Jitter is applied uniformly within a circle of specified radius
- Useful for visualization on maps
- Example: `--jitter 5` spreads points within ~5 km of the original location

**Caching:**
- Geocoding results are cached to avoid re-querying
- Cache location: `cache/geocode_cache.json`
- Only successful results are cached
- Speeds up repeated geocoding operations

## Backend Libraries

### libs/pypsa_earth_backend.py

Core implementation for PyPSA-Earth integration. Contains business logic for:
- Downloading OSM data via earth_osm
- Building PyPSA networks using PyPSA-Earth methodology
- Bus clustering using DBSCAN
- Line processing and electrical parameter calculation
- Exporting to CSV format for PyPSA import

**Key Functions:**
- `create_pypsa_network_with_earth()`: Main entry point
- `_run_pypsa_earth_download()`: OSM data download
- `_run_pypsa_earth_build_network()`: Network construction
- `_apply_pypsa_earth_bus_clustering()`: DBSCAN clustering
- `_export_to_csv_format()`: CSV export

## Setup

Before using these utilities, ensure you have:

1. Installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Cloned PyPSA-Earth (for download_pypsa_earth.py):
   ```bash
   git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
   cd pypsa-earth
   pip install -e .
   cd ..
   ```

Or simply run the automated setup script:
```bash
# Linux/macOS
./setup.sh

# Windows
setup.bat
```

For detailed setup instructions, see the main [SETUP.md](../SETUP.md) file.
