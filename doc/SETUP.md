# PyPSA Alternative - Setup Guide

This guide explains how to set up the PyPSA Alternative project with PyPSA-Earth integration.

## Prerequisites

- Python 3.9 or higher
- Git
- pip

## Installation Steps

### 1. Clone the Repository (if not already done)

```bash
cd ~/github
git clone <your-repo-url> pypsa_alternative
cd pypsa_alternative
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Clone PyPSA-Earth

The `download_pypsa_earth.py` utility requires PyPSA-Earth to be installed in the `pypsa-earth` directory within this project.

```bash
# From the project root directory
git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
cd pypsa-earth

# Install PyPSA-Earth dependencies
pip install -e .

# Return to project root
cd ..
```

### 4. Verify Installation

Check that pypsa-earth is properly installed:

```bash
# Check directory structure
ls -la pypsa-earth/

# Expected output should show pypsa-earth scripts, configs, etc.
```

### 5. Test the Download Utility

```bash
# Download network data for South Korea (minimum 220 kV)
python utils/download_pypsa_earth.py KR --voltage-min 220

# Or for another country (e.g., Germany)
python utils/download_pypsa_earth.py DE --voltage-min 220
```

## Directory Structure

After setup, your directory should look like this:

```
pypsa_alternative/
├── cache/                    # Geocoding cache
├── data/                     # Your data files
├── libs/                     # Library files
├── utils/
│   ├── libs/
│   │   └── pypsa_earth_backend.py
│   ├── download_pypsa_earth.py
│   └── geocode_addresses.py
├── pypsa-earth/             # PyPSA-Earth installation (cloned)
│   ├── scripts/
│   ├── configs/
│   └── ...
├── config.yaml              # Your config
├── requirements.txt         # Python dependencies
├── SETUP.md                # This file
└── main_singlenode.py      # Main script
```

## Usage

### GUI Application (Recommended)

The easiest way to use the utilities is through the graphical interface:

```bash
# Launch the GUI
python pypsa_gui.py

# Or use the launcher scripts
./run_gui.sh        # macOS/Linux
run_gui.bat         # Windows
```

The GUI provides:
- User-friendly interface for all utilities
- Point-and-click configuration
- Real-time output console
- Prerequisite checking
- No command-line knowledge required

### Command-Line Usage

#### Download PyPSA-Earth Network Data

```bash
# Basic usage
python utils/download_pypsa_earth.py <COUNTRY_CODE>

# With options
python utils/download_pypsa_earth.py KR --voltage-min 220 --output-dir ./networks

# Enable verbose logging
python utils/download_pypsa_earth.py KR --verbose
```

**Available Options:**
- `country_code`: 2-letter ISO country code (KR, DE, US, etc.)
- `--voltage-min`: Minimum voltage level in kV (default: 220)
- `--output-dir`: Output directory for network files (default: ./networks)
- `--verbose, -v`: Enable verbose logging

### Geocode Addresses

```bash
# Geocode addresses in CSV files
python utils/geocode_addresses.py data/2024

# With jitter for identical locations
python utils/geocode_addresses.py data/2024 --jitter auto

# Apply specific jitter (e.g., 5 km)
python utils/geocode_addresses.py data/2024 --jitter jitter-5
```

## Troubleshooting

### PyPSA-Earth Not Found Error

If you see an error like `ModuleNotFoundError: No module named 'earth_osm'`, ensure:

1. PyPSA-Earth is cloned in the correct location: `pypsa-earth/` directory
2. PyPSA-Earth dependencies are installed: `cd pypsa-earth && pip install -e .`

### Import Errors

If you encounter import errors from PyPSA-Earth scripts:

```bash
# Reinstall PyPSA-Earth
cd pypsa-earth
pip install -e . --force-reinstall
cd ..
```

### earth_osm Download Issues

If OSM data download fails:

1. Check your internet connection
2. Ensure you have sufficient disk space
3. Try with a smaller country code (e.g., LU for Luxembourg)

### Geocoding Issues

If geocoding fails or is slow:

1. Geocoding uses Nominatim with rate limiting (1 request/second)
2. Results are cached in `cache/geocode_cache.json`
3. Use `--overwrite` to force re-geocoding

## Additional Resources

- [PyPSA Documentation](https://pypsa.readthedocs.io/)
- [PyPSA-Earth Documentation](https://pypsa-earth.readthedocs.io/)
- [earth-osm Documentation](https://github.com/pypsa-meets-earth/earth-osm)

## Support

For issues specific to:
- **This project**: Open an issue in this repository
- **PyPSA-Earth**: Check [pypsa-earth issues](https://github.com/pypsa-meets-earth/pypsa-earth/issues)
- **PyPSA**: Check [pypsa issues](https://github.com/PyPSA/PyPSA/issues)
