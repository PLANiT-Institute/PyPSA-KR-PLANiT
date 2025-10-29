# PyPSA GUI - User Guide

A graphical user interface for PyPSA Alternative utilities. No command-line knowledge required!

## Quick Start

### Launch the GUI

**Option 1: Direct Python**
```bash
python pypsa_gui.py
```

**Option 2: Launcher Scripts**
```bash
# macOS/Linux
./run_gui.sh

# Windows
run_gui.bat
```

**Option 3: Double-click** (after making executable)
- macOS/Linux: Double-click `run_gui.sh`
- Windows: Double-click `run_gui.bat`

## Interface Overview

The GUI has three main tabs:

### 1. Geocoding Tab

**Purpose:** Add geographic coordinates (x, y) to CSV files containing addresses.

**How to Use:**

1. **Input Folder**
   - Click "Browse..." to select folder containing CSV files
   - Or type the path directly (e.g., `data/2024`)

2. **Options**
   - **Address Column**: Name of the column containing addresses (default: `address`)
   - **File Pattern**: Which files to process (default: `*.csv` for all CSV files)
   - **Cache File**: Where to store geocoding results (default: `cache/geocode_cache.json`)
   - **Overwrite**: Check to re-geocode addresses that already have coordinates

3. **Jitter Settings**
   - **None**: No jitter applied
   - **Auto**: Prompts you if all locations are identical
   - **Custom**: Apply specified km jitter (e.g., 5 km spreads points within 5km radius)

4. **Run**
   - Click "Run Geocoding"
   - Watch progress in the Output Console
   - Results are automatically saved to the CSV files

**Example Use Case:**
You have CSV files with Korean addresses in a "province" column and want to add coordinates:
1. Browse to your data folder
2. Change "Address Column" to `province`
3. Set Jitter Mode to "auto" (in case all addresses resolve to same location)
4. Click "Run Geocoding"

### 2. PyPSA-Earth Download Tab

**Purpose:** Download power network data from OpenStreetMap for any country.

**How to Use:**

1. **Country Selection**
   - Enter 2-letter ISO country code (e.g., KR, DE, US)
   - Or use quick select buttons for common countries

2. **Options**
   - **Minimum Voltage**: Only include lines at or above this voltage (default: 220 kV)
     - 110 kV: Include all transmission lines
     - 220 kV: High voltage transmission only
     - 380 kV: Extra high voltage only
   - **Output Directory**: Where to save the network files (default: `./networks`)
   - **Verbose Logging**: Show detailed progress information

3. **Prerequisites Check**
   - Shows status of required components
   - Green = Ready to go
   - Red = Missing components (run `./setup.sh` first)

4. **Run**
   - Click "Download Network Data"
   - Watch progress in Output Console
   - Results saved to `[output_dir]/[COUNTRY]/`

**Example Use Case:**
Download South Korea's 220kV+ network:
1. Country Code: `KR` (already default)
2. Minimum Voltage: `220` (already default)
3. Check prerequisites are green
4. Click "Download Network Data"
5. Wait for completion (may take several minutes)
6. Find results in `./networks/KR/`

**Output Files:**
- `buses.csv`: Network buses with coordinates
- `lines.csv`: Transmission lines with electrical parameters
- `network.csv`: Network metadata

### 3. About Tab

Information about the application, including:
- Feature descriptions
- Requirements
- Quick links to documentation
- Command-line equivalents

## Output Console

The bottom panel shows real-time output:
- Progress messages
- Success/error notifications
- File processing status
- Detailed logs

**Console Controls:**
- **Clear Output**: Remove all messages from console
- **Auto-scroll**: Console automatically scrolls to show latest output

## Common Workflows

### Workflow 1: Geocode New Data

1. Launch GUI
2. Go to **Geocoding** tab
3. Browse to your data folder (e.g., `data/2024`)
4. Set jitter to "auto"
5. Click **Run Geocoding**
6. Wait for completion
7. Check your CSV files - now have x, y columns!

### Workflow 2: Download Multiple Countries

1. Launch GUI
2. Go to **PyPSA-Earth Download** tab
3. Enter country code (e.g., "DE")
4. Click **Download Network Data**
5. Wait for completion
6. Change country code (e.g., "FR")
7. Click **Download Network Data** again
8. Repeat for each country

### Workflow 3: Re-geocode with Different Settings

1. Launch GUI
2. Go to **Geocoding** tab
3. Browse to your data folder
4. Check **Overwrite existing coordinates**
5. Change jitter settings (e.g., set to custom 5 km)
6. Click **Run Geocoding**

## Troubleshooting

### GUI Won't Start

**Error:** `ModuleNotFoundError: No module named 'tkinter'`

**Solution:**
```bash
# macOS
brew install python-tk

# Ubuntu/Debian
sudo apt-get install python3-tk

# Windows
# Tkinter should be included with Python
# Reinstall Python with "tcl/tk and IDLE" checked
```

### Prerequisites Check Shows Red

**Solution:** Run the setup script:
```bash
./setup.sh        # macOS/Linux
setup.bat         # Windows
```

This will:
- Install all Python dependencies
- Clone pypsa-earth repository
- Verify installation

### Geocoding Runs But No Coordinates

**Possible causes:**
1. No internet connection (geocoding requires Nominatim API)
2. Addresses not found (try different address format)
3. Rate limiting (wait a minute and try again)

**Check console output** for specific error messages.

### Download Fails with Import Error

**Error:** `ModuleNotFoundError: No module named 'earth_osm'`

**Solution:**
```bash
cd pypsa-earth
pip install -e .
cd ..
```

### GUI Freezes During Operation

**This is normal!** Long operations run in background threads, but:
- The GUI may appear frozen
- Console continues updating
- Just wait for completion

The operations can take:
- Geocoding: 1-5 minutes (depends on cache)
- Download: 5-15 minutes (depends on country size)

## Advanced Tips

### Using Custom Address Columns

If your CSV has addresses in a column named "location" instead of "address":
1. Change **Address Column** to `location`
2. Run as normal

### Batch Processing Multiple Folders

Run the GUI multiple times, changing the input folder each time, or use command-line:
```bash
python utils/geocode_addresses.py data/2024
python utils/geocode_addresses.py data/2023
python utils/geocode_addresses.py data/2022
```

### Getting Better Geocoding Results

1. **Use jitter** when addresses are all the same city
2. **Check cache** - delete `cache/geocode_cache.json` to force fresh geocoding
3. **Clean addresses** - remove extra information in parentheses (done automatically)

### Viewing Downloaded Networks

After downloading, you can:
```python
import pypsa
network = pypsa.Network()
network.import_from_csv_folder("./networks/KR")
print(network.buses)
print(network.lines)
```

Or open the CSV files directly in Excel/Pandas.

## Keyboard Shortcuts

- **Ctrl+Tab**: Switch between tabs
- **Ctrl+A** (in console): Select all text
- **Ctrl+C** (in console): Copy selected text

## File Locations

After using the GUI, you'll find:

```
pypsa_alternative/
├── cache/
│   └── geocode_cache.json     # Geocoding cache
├── networks/
│   ├── KR/                     # South Korea network
│   │   ├── buses.csv
│   │   ├── lines.csv
│   │   └── network.csv
│   └── DE/                     # Germany network
│       └── ...
├── data/
│   └── 2024/                   # Your data (with x, y added)
│       └── *.csv
└── temp_pypsa_earth_*          # Temporary (auto-cleaned)
```

## Getting Help

1. **Check console output** for specific error messages
2. **Review documentation**:
   - SETUP.md - Installation
   - DEPENDENCIES.md - Requirements
   - utils/README.md - Utility details
3. **Open documentation from GUI**: About tab → Click buttons
4. **Try command-line version** for more detailed output

## Command-Line Equivalents

The GUI runs these commands behind the scenes:

**Geocoding:**
```bash
python utils/geocode_addresses.py [folder] \
  --address-column [column] \
  --pattern [pattern] \
  --jitter [mode] \
  --cache-file [cache]
```

**Download:**
```bash
python utils/download_pypsa_earth.py [COUNTRY] \
  --voltage-min [voltage] \
  --output-dir [output] \
  --verbose
```

You can use these directly if you prefer command-line or need scripting.

## FAQ

**Q: Can I close the GUI while it's running?**
A: No, this will stop the operation. Wait for completion.

**Q: Can I run multiple operations at once?**
A: No, run one at a time. Operations are resource-intensive.

**Q: Is my cache shared between GUI and command-line?**
A: Yes! Both use the same cache file by default.

**Q: Why does geocoding take so long?**
A: First run is slow (API calls), but cached results make subsequent runs fast.

**Q: Can I use the GUI on a server without a display?**
A: No, use command-line versions for headless servers.

**Q: Does the GUI work on all operating systems?**
A: Yes! Tested on macOS, Linux (Ubuntu), and Windows 10/11.

## Support

For issues:
1. Check console output
2. Review documentation files
3. Verify prerequisites are installed
4. Try the command-line version for more debug info
