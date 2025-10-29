# PyPSA Alternative

Power system analysis toolkit with utilities for geocoding and network data download.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Utilities

**Interactive GUI (Easiest):**
```bash
cd utils
python utils_gui.py

# Or use launcher
./run_utils_gui.sh        # macOS/Linux
run_utils_gui.bat         # Windows
```

**Command-Line:**
```bash
# Geocode addresses in CSV files
python utils/geocode_addresses.py data/2024 --jitter auto

# Download power network data
python utils/download_pypsa_earth.py KR --voltage-min 220
```

### 3. Run Main Analysis

```bash
python main_singlenode.py
```

## Project Structure

```
pypsa_alternative/
├── utils/                    # Utility tools
│   ├── utils_gui.py         # Interactive GUI
│   ├── geocode_addresses.py # Geocoding tool
│   ├── download_pypsa_earth.py # Network downloader
│   └── libs/                # Backend libraries
├── config/                   # Configuration files
│   └── config.yaml
├── doc/                      # Documentation
│   ├── README.md            # Full documentation
│   ├── SETUP.md             # Setup guide
│   ├── DEPENDENCIES.md      # Dependencies
│   └── GUI_README.md        # GUI user guide
├── data/                     # Your data files
├── cache/                    # Geocoding cache
└── main_singlenode.py       # Main analysis script
```

## Documentation

- **[doc/README.md](doc/README.md)** - Full documentation
- **[doc/QUICKSTART.md](doc/QUICKSTART.md)** - 5-minute quick start
- **[doc/SETUP.md](doc/SETUP.md)** - Detailed setup instructions
- **[doc/GUI_README.md](doc/GUI_README.md)** - GUI user guide
- **[doc/DEPENDENCIES.md](doc/DEPENDENCIES.md)** - Dependency information

## Features

### 🖥️ Interactive GUI
- User-friendly interface for all utilities
- No command-line knowledge required
- Real-time output console
- Located in `utils/utils_gui.py`

### 📍 Geocoding Utility
- Add x, y coordinates to CSV files
- Support for Korean and international addresses
- Smart jitter for identical locations
- Caching for fast re-runs

### 🌍 Network Download
- Download power network data from OpenStreetMap
- Support for any country (2-letter ISO code)
- Automatic network building and clustering
- Export to PyPSA-compatible CSV format

## Requirements

- Python 3.9+
- See `requirements.txt` for Python packages
- For network download: pypsa-earth repository (see doc/SETUP.md)

## Support

See documentation in `doc/` directory for detailed information.
