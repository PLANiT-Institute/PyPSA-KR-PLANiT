# Quick Start Guide

Get up and running with PyPSA Alternative in 5 minutes!

## Step 1: Install (One-time setup)

```bash
# Automated install (recommended)
./setup.sh

# Or manual install
pip install -r requirements.txt
git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
cd pypsa-earth && pip install -e . && cd ..
```

## Step 2: Launch GUI

```bash
python pypsa_gui.py

# Or double-click run_gui.sh (macOS/Linux) or run_gui.bat (Windows)
```

## Step 3: Choose Your Task

### Task A: Add Coordinates to CSV Files

1. Click **Geocoding** tab
2. Click **Browse...** and select your data folder
3. Set **Jitter Mode** to "auto"
4. Click **Run Geocoding**
5. Done! Your CSV files now have x, y coordinates

### Task B: Download Power Network Data

1. Click **PyPSA-Earth Download** tab
2. Select a country (e.g., click "South Korea" button)
3. Click **Download Network Data**
4. Done! Network saved to `./networks/KR/`

## That's It!

Check the Output Console at the bottom for progress and results.

## Need Help?

- **GUI Guide**: See [GUI_README.md](GUI_README.md)
- **Setup Issues**: See [SETUP.md](SETUP.md)
- **Dependencies**: See [DEPENDENCIES.md](DEPENDENCIES.md)

## Command-Line Users

Prefer terminal? Use these commands:

```bash
# Geocoding
python utils/geocode_addresses.py data/2024 --jitter auto

# Download network
python utils/download_pypsa_earth.py KR --voltage-min 220
```

See [SETUP.md](SETUP.md) for more details.
