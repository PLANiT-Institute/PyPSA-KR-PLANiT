# PyPSA Alternative

A comprehensive power system analysis toolkit for modeling and optimizing electricity networks. This project provides utilities for geocoding, network data processing, and multi-node power system analysis using PyPSA (Python for Power System Analysis).

## Overview

PyPSA Alternative is designed for energy system modeling and analysis, with a focus on:
- Multi-node network modeling (single node, province level, and grouped regions)
- Integration with PyPSA-Earth for OpenStreetMap-based network data
- Time-series energy system optimization
- Renewable energy integration analysis
- Storage and generation capacity planning

## Quick Start

### Automated Setup (Recommended)

**Windows:**
```batch
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup scripts will:
1. Install all Python dependencies
2. Clone and configure PyPSA-Earth repository
3. Verify installation

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Clone PyPSA-Earth (required for network utilities)
git clone https://github.com/pypsa-meets-earth/pypsa-earth.git
```

## Usage

### Main Analysis Scripts

**Single Node Analysis:**
```bash
python main_singlenode.py
```
Run power system optimization for a single-node network (entire region as one bus).

**Province-Level Analysis:**
```bash
python main_province.py
```
Run multi-node analysis with province-level granularity.

**Group-Level Analysis:**
```bash
python main_group.py
```
Run analysis with custom regional groupings.

### Utility Tools

**Interactive GUI (Easiest):**
```bash
cd utils
python utils_gui.py
```

**Geocoding addresses:**
```bash
python utils/geocode_addresses.py data/2024 --jitter auto
```
Add geographic coordinates (x, y) to CSV files containing addresses.

**Download network data:**
```bash
python utils/download_pypsa_earth.py KR --voltage-min 220
```
Download and process power network data from OpenStreetMap for any country.

## Project Structure

```
pypsa_alternative/
├── main_singlenode.py       # Single-node network analysis
├── main_province.py         # Province-level analysis
├── main_group.py            # Grouped regional analysis
├── libs/                    # Core analysis libraries
│   ├── config.py           # Configuration loader
│   ├── data_loader.py      # Network and time-series data loading
│   ├── temporal_data.py    # Time-series data application
│   ├── carrier_standardization.py # Carrier name standardization
│   ├── component_attributes.py    # Generator/storage attributes
│   ├── cc_merger.py        # Combined cycle generator handling
│   ├── generator_p_set.py  # Generator capacity settings
│   ├── energy_constraints.py # Capacity factor constraints
│   ├── aggregators.py      # Regional aggregation
│   ├── resample.py         # Time-series resampling
│   └── visualization.py    # Plotting and charts
├── utils/                   # Utility tools
│   ├── utils_gui.py        # Interactive GUI interface
│   ├── geocode_addresses.py # Address geocoding tool
│   ├── download_pypsa_earth.py # Network data downloader
│   ├── fill_missing_values.py # Data completion utility
│   └── libs/               # Utility backend libraries
├── config/                  # Configuration files
│   ├── config_single.xlsx  # Single-node configuration
│   ├── config_province.xlsx # Province-level configuration
│   └── config_group.xlsx   # Group-level configuration
├── data/                    # Input data files
│   ├── networks/           # Network CSV files
│   ├── Singlenode2024/     # Single-node time-series data
│   ├── Provincenode2024/   # Province-level time-series data
│   └── raw/                # Raw data files
├── output/                  # Analysis results and plots
├── cache/                   # Geocoding and processing cache
├── documentation/           # Additional documentation
└── pypsa-earth/            # PyPSA-Earth repository (cloned during setup)
```

## Configuration

Each analysis mode uses an Excel configuration file in the `config/` directory:

- `config_single.xlsx` - Single-node network configuration
- `config_province.xlsx` - Province-level network configuration
- `config_group.xlsx` - Group-level network configuration

Configuration files specify:
- Network component paths (generators, storage, loads, etc.)
- Time-series data paths
- Solver settings
- Output preferences
- Carrier mappings and attributes

## Features

### Power System Analysis
- Multi-temporal network optimization
- Generator capacity planning and dispatch
- Storage unit optimization
- Renewable energy integration
- Combined cycle power plant modeling
- Capacity factor constraints
- Regional aggregation and clustering

### Data Processing
- Time-series data resampling
- Carrier name standardization
- Component attribute application
- Regional aggregation
- Missing value interpolation

### Geocoding Utility
- Batch geocoding of addresses in CSV files
- Support for Korean and international addresses
- Smart jitter for co-located facilities
- Caching for performance
- Automatic coordinate system handling

### Network Data Download
- OpenStreetMap-based network extraction
- Country-specific network data (any ISO 2-letter code)
- Voltage level filtering
- Automatic network building and clustering
- Export to PyPSA-compatible CSV format

### Interactive GUI
- User-friendly interface for all utilities
- No command-line knowledge required
- Real-time output console and logging
- Batch processing support

## Requirements

- **Python:** 3.9 or higher
- **Operating System:** Windows, macOS, or Linux
- **Dependencies:** See `requirements.txt`
- **Optional:** PyPSA-Earth repository for network download utilities

### Key Dependencies
- `pypsa` - Power system analysis framework
- `pandas` - Data manipulation
- `geopandas` - Geospatial data processing
- `earth_osm` - OpenStreetMap data access
- `geopy` - Geocoding services
- `matplotlib` & `cartopy` - Visualization
- `openpyxl` - Excel file support

## Documentation

Additional documentation can be found in the `documentation/` directory.

## Contributing

This project is under active development. Contributions, bug reports, and feature requests are welcome.

## License

See LICENSE file for details.

## Support

For questions or issues:
1. Check the `documentation/` directory
2. Review example configurations in `config/`
3. Examine example scripts in `examples/`
