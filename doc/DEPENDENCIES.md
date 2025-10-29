# Dependencies Guide

This document explains all the dependencies required for PyPSA Alternative and what each one is used for.

## Core Requirements

### PyPSA-Earth Repository

**Installation:**
```bash
git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
cd pypsa-earth
pip install -e .
cd ..
```

**Location:** Must be in `pypsa-earth/` directory in the project root

**Purpose:** Provides the backend for downloading OSM data and building power networks

**Used by:** `utils/download_pypsa_earth.py`, `utils/libs/pypsa_earth_backend.py`

## Python Package Dependencies

All packages listed in `requirements.txt`:

### Energy Modeling

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `pypsa` | ≥0.21.0 | Core power system analysis library | Network creation, analysis |

### Data Processing

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `pandas` | ≥1.5.0 | Data manipulation and CSV handling | All utilities |
| `numpy` | ≥1.23.0 | Numerical computing | Network calculations, jitter |

### Geospatial Processing

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `geopandas` | ≥0.12.0 | Geospatial data operations | PyPSA-Earth backend |
| `shapely` | ≥2.0.0 | Geometric operations | Line/bus geometry |
| `geopy` | ≥2.3.0 | Geocoding addresses | geocode_addresses.py |

### Scientific Computing

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `scipy` | ≥1.9.0 | KDTree for spatial indexing | Bus clustering |
| `scikit-learn` | ≥1.1.0 | DBSCAN clustering algorithm | Bus clustering |

### OSM Data Access

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `earth-osm` | ≥0.3.0 | Download OSM power infrastructure data | PyPSA-Earth backend |

### Visualization (Optional)

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `matplotlib` | ≥3.5.0 | Plotting and visualization | Network visualization |
| `cartopy` | ≥0.21.0 | Geospatial plotting | Map-based visualization |

### Data File Support

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `openpyxl` | ≥3.0.0 | Excel file reading/writing (.xlsx) | Data import/export |
| `xlrd` | ≥2.0.0 | Excel file reading (.xls) | Legacy Excel support |

### Utilities

| Package | Version | Purpose | Used by |
|---------|---------|---------|---------|
| `pyyaml` | ≥6.0 | YAML config file parsing | Config management |
| `requests` | ≥2.28.0 | HTTP requests | API calls |

## Installation

### Quick Install (Recommended)

Use the automated setup script:

```bash
# Linux/macOS
./setup.sh

# Windows
setup.bat
```

### Manual Install

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Clone and install PyPSA-Earth
git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
cd pypsa-earth
pip install -e .
cd ..
```

## Dependency Tree

```
pypsa_alternative/
│
├── Core Algorithm Dependencies
│   ├── pypsa ──────────────── Network modeling
│   ├── pandas ─────────────── Data processing
│   └── numpy ──────────────── Numerical ops
│
├── PyPSA-Earth Integration
│   ├── pypsa-earth/ ───────── Repository (cloned)
│   ├── earth-osm ──────────── OSM data download
│   ├── geopandas ──────────── Geospatial operations
│   ├── shapely ────────────── Geometry handling
│   ├── scipy ──────────────── Spatial indexing (KDTree)
│   └── scikit-learn ───────── Clustering (DBSCAN)
│
├── Geocoding Utilities
│   └── geopy ──────────────── Address → Coordinates
│
└── Data I/O
    ├── openpyxl ───────────── Excel support
    ├── pyyaml ─────────────── Config files
    └── requests ───────────── API calls
```

## Common Issues

### 1. earth_osm Not Found

**Error:** `ModuleNotFoundError: No module named 'earth_osm'`

**Solution:**
```bash
cd pypsa-earth
pip install -e .
cd ..
```

### 2. GEOS/GDAL Issues (geopandas/shapely)

**Error:** `OSError: Could not find lib c or load any of its variants`

**Solution (macOS):**
```bash
brew install geos gdal
pip install --no-binary :all: shapely
```

**Solution (Ubuntu/Debian):**
```bash
sudo apt-get install libgeos-dev libgdal-dev
pip install --no-binary :all: shapely
```

**Solution (Windows):**
```bash
# Use conda instead of pip
conda install -c conda-forge geopandas shapely
```

### 3. PyPSA-Earth Import Issues

**Error:** Import errors from PyPSA-Earth scripts

**Solution:**
```bash
cd pypsa-earth
pip install -e . --force-reinstall
cd ..
```

### 4. Cartopy Installation Issues

**Note:** Cartopy can be difficult to install. If you don't need map visualization:

```bash
# Install without cartopy
pip install -r requirements.txt --ignore-installed cartopy
```

## Minimal Requirements

If you only need specific functionality, you can install minimal dependencies:

### For Geocoding Only:
```bash
pip install pandas numpy geopy openpyxl
```

### For PyPSA Network Download Only:
```bash
pip install pypsa pandas numpy geopandas shapely scipy scikit-learn earth-osm
# Plus pypsa-earth repository
```

## Version Compatibility

**Python:** Requires Python 3.9 or higher

**Tested with:**
- Python 3.9, 3.10, 3.11
- PyPSA 0.21+
- earth-osm 0.3+

**Operating Systems:**
- macOS (tested)
- Linux (Ubuntu 20.04+, tested)
- Windows 10/11 (should work, limited testing)

## Support

For dependency-related issues:

1. **PyPSA-Earth dependencies:** Check [pypsa-earth documentation](https://pypsa-earth.readthedocs.io/)
2. **Geospatial packages (geopandas/shapely):** Check [geopandas installation guide](https://geopandas.org/en/stable/getting_started/install.html)
3. **PyPSA:** Check [pypsa installation guide](https://pypsa.readthedocs.io/en/latest/installation.html)
