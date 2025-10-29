# Project Reorganization Summary

This document describes the recent reorganization of the PyPSA Alternative project.

## Changes Made

### 1. Directory Restructuring

**Created new directories:**
- `doc/` - All documentation files
- `config/` - Configuration files

**Moved files:**
- All `.md` files → `doc/`
- `config.yaml` → `config/config.yaml`

### 2. GUI Reorganization

**Old structure:**
- `pypsa_gui.py` (root)
- `run_gui.sh` / `run_gui.bat` (root)

**New structure:**
- `utils/utils_gui.py` - Interactive GUI for utilities only
- `utils/run_utils_gui.sh` / `utils/run_utils_gui.bat` - Launchers

**Key change:** GUI now focuses only on running utilities (geocoding and network download), not main analysis.

### 3. Updated References

- `main_singlenode.py` - Updated to use `config/config.yaml`
- All documentation updated with new paths
- README files updated with new structure

## New Project Structure

```
pypsa_alternative/
├── config/                   # Configuration files
│   └── config.yaml
├── doc/                      # All documentation
│   ├── README.md            # Full documentation
│   ├── SETUP.md             # Setup guide
│   ├── QUICKSTART.md        # Quick start
│   ├── GUI_README.md        # GUI guide
│   ├── DEPENDENCIES.md      # Dependencies
│   └── CHANGES.md           # This file
├── utils/                    # Utility tools
│   ├── utils_gui.py         # Interactive GUI
│   ├── run_utils_gui.sh     # GUI launcher (Unix)
│   ├── run_utils_gui.bat    # GUI launcher (Windows)
│   ├── geocode_addresses.py # Geocoding tool
│   ├── download_pypsa_earth.py # Network downloader
│   ├── libs/                # Backend libraries
│   └── README.md            # Utils documentation
├── libs/                     # Main project libraries
├── data/                     # Data files
├── cache/                    # Geocoding cache
├── pypsa-earth/             # PyPSA-Earth (cloned)
├── README.md                # Project overview
├── requirements.txt         # Python dependencies
├── setup.sh / setup.bat     # Setup scripts
└── main_singlenode.py       # Main analysis script
```

## Migration Guide

### If you had code referencing old paths:

**Config file:**
```python
# Old
config = load_config('config.yaml')

# New
config = load_config('config/config.yaml')
```

**Documentation:**
```bash
# Old
cat SETUP.md

# New
cat doc/SETUP.md
```

**GUI launch:**
```bash
# Old
python pypsa_gui.py
./run_gui.sh

# New
cd utils
python utils_gui.py
./run_utils_gui.sh
```

## What's Different in the GUI

### Old GUI (pypsa_gui.py)
- Attempted to run main analysis
- Mixed utilities and main functionality
- Located in root directory

### New GUI (utils/utils_gui.py)
- **Focuses only on utilities:**
  - Geocoding addresses
  - Downloading network data
- Simpler, cleaner interface
- Located in utils/ directory
- Does NOT run main analysis (use `python main_singlenode.py` for that)

## Benefits of Reorganization

1. **Cleaner root directory** - Only essential files in root
2. **Organized documentation** - All docs in one place (doc/)
3. **Better separation** - Config, docs, and utils clearly separated
4. **GUI clarity** - GUI focused on utilities, not main analysis
5. **Easier navigation** - Logical file grouping

## No Breaking Changes to Core Functionality

- All utilities work the same
- Main analysis unchanged
- Only file locations changed
- All features preserved

## Quick Start After Reorganization

```bash
# Run utilities (interactive)
cd utils
python utils_gui.py

# Run utilities (command-line)
python utils/geocode_addresses.py data/2024
python utils/download_pypsa_earth.py KR

# Run main analysis
python main_singlenode.py

# View documentation
ls doc/
cat doc/QUICKSTART.md
```

## Questions?

See documentation in `doc/` directory:
- `doc/README.md` - Full documentation
- `doc/SETUP.md` - Setup instructions
- `doc/GUI_README.md` - GUI usage guide
