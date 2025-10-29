# PyPSA Alternative

A Python toolkit for power system analysis with integrated utilities for data processing and network generation.

## ✨ Features

### 🖥️ **NEW: Graphical User Interface**
User-friendly GUI for all utilities - no command-line knowledge required!

```bash
python pypsa_gui.py
```

### 🗺️ **Geocoding Utility**
- Automatically geocode addresses in CSV files
- Add x, y coordinates for spatial analysis
- Smart jitter for identical locations
- Caching for fast re-runs
- Supports Korean and international addresses

### 🌍 **PyPSA-Earth Integration**
- Download power network data from OpenStreetMap
- Support for any country (2-letter ISO code)
- Automatic network building and clustering
- Export to PyPSA-compatible CSV format

### ⚡ **Power System Modeling**
- PyPSA-based network analysis
- Single-node and multi-node support
- Configurable via YAML

## 🚀 Quick Start

### 1. Install

```bash
# Automated setup (recommended)
./setup.sh

# Or install manually
pip install -r requirements.txt
git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
cd pypsa-earth && pip install -e . && cd ..
```

### 2. Run GUI

```bash
python pypsa_gui.py

# Or use launcher
./run_gui.sh        # macOS/Linux
run_gui.bat         # Windows
```

### 3. Use Utilities

**Via GUI (Easy):**
1. Launch GUI
2. Select tab (Geocoding or Download)
3. Configure options
4. Click Run!

**Via Command-Line:**
```bash
# Geocode addresses
python utils/geocode_addresses.py data/2024 --jitter auto

# Download network data
python utils/download_pypsa_earth.py KR --voltage-min 220
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes |
| [GUI_README.md](GUI_README.md) | Complete GUI user guide |
| [SETUP.md](SETUP.md) | Detailed installation instructions |
| [DEPENDENCIES.md](DEPENDENCIES.md) | Dependency information and troubleshooting |
| [utils/README.md](utils/README.md) | Command-line utility documentation |

## 🎯 Use Cases

### Use Case 1: Add Geographic Coordinates to Data

You have CSV files with addresses but need coordinates for mapping:

1. Open GUI → **Geocoding** tab
2. Select your data folder
3. Enable "auto" jitter (spreads identical locations)
4. Click "Run Geocoding"
5. CSV files now have x, y columns!

### Use Case 2: Download Power Network

You need transmission network data for analysis:

1. Open GUI → **PyPSA-Earth Download** tab
2. Select country (e.g., "South Korea")
3. Set minimum voltage (e.g., 220 kV)
4. Click "Download Network Data"
5. Get buses.csv, lines.csv with full network!

### Use Case 3: Analyze Power System

Run optimization with your network:

```bash
python main_singlenode.py
```

## 📁 Project Structure

```
pypsa_alternative/
├── pypsa_gui.py              # 🖥️ GUI Application (NEW!)
├── run_gui.sh / .bat         # GUI launchers
├── main_singlenode.py        # Main analysis script
├── config.yaml               # Configuration
├── requirements.txt          # Python dependencies
│
├── utils/                    # Utilities
│   ├── geocode_addresses.py  # Geocoding tool
│   ├── download_pypsa_earth.py  # Network download
│   ├── libs/                 # Backend libraries
│   └── README.md            # Utility docs
│
├── pypsa-earth/             # PyPSA-Earth (cloned)
├── data/                    # Your data files
├── cache/                   # Geocoding cache
├── networks/                # Downloaded networks
│
└── Documentation
    ├── QUICKSTART.md        # Quick start guide
    ├── GUI_README.md        # GUI user guide
    ├── SETUP.md            # Setup instructions
    └── DEPENDENCIES.md     # Dependency info
```

## 🛠️ Requirements

### System Requirements
- Python 3.9 or higher
- Internet connection (for geocoding and downloads)
- 2GB+ RAM
- 1GB+ disk space

### Python Packages
All packages listed in `requirements.txt`:
- pypsa - Power system modeling
- pandas, numpy - Data processing
- geopandas, shapely - Geospatial operations
- earth-osm - OpenStreetMap data access
- geopy - Geocoding
- scipy, scikit-learn - Scientific computing
- tkinter - GUI (usually included with Python)

### External Dependencies
- pypsa-earth repository (automatically cloned by setup script)

## 🖥️ GUI Features

### Geocoding Tab
- 📁 Browse for data folders
- ⚙️ Configure address column, file patterns
- 🎲 Jitter settings (auto-detect, custom radius)
- ♻️ Overwrite existing coordinates
- 💾 Cache management

### PyPSA-Earth Download Tab
- 🌍 Country selection (2-letter ISO codes)
- ⚡ Voltage filtering
- 📂 Output directory selection
- ✅ Prerequisites checker
- 📊 Network summary after download

### Output Console
- 📋 Real-time progress
- ✓ Success notifications
- ❌ Error messages
- 📝 Detailed logs

## 💡 Tips & Tricks

### Geocoding Tips
1. **Use jitter** when all addresses are in same city
2. **Check cache** at `cache/geocode_cache.json`
3. **Use overwrite** to force re-geocoding with new settings

### Download Tips
1. **Check prerequisites** before running (red = issues)
2. **Start small** - try Luxembourg (LU) before large countries
3. **Adjust voltage** to control network size (higher = smaller)

### GUI Tips
1. **Watch console** for detailed progress
2. **Don't close** during operations
3. **Clear output** between runs for clarity

## 🐛 Troubleshooting

### GUI Won't Start
```bash
# Install tkinter
brew install python-tk          # macOS
sudo apt-get install python3-tk  # Ubuntu
```

### Prerequisites Check Fails
```bash
# Run setup script
./setup.sh
```

### Geocoding Slow
- First run is always slow (API calls)
- Subsequent runs use cache (fast!)
- Rate limited to 1 request/second

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

See [SETUP.md](SETUP.md) and [DEPENDENCIES.md](DEPENDENCIES.md) for more help.

## 📝 Examples

### Example 1: Geocode with Custom Jitter

```bash
# GUI: Set jitter mode to "custom", value to "5"
# CLI: Add --jitter jitter-5
python utils/geocode_addresses.py data/2024 --jitter jitter-5
```

### Example 2: Download Multiple Countries

```bash
# GUI: Change country code and run multiple times
# CLI: Run commands in sequence
python utils/download_pypsa_earth.py KR --voltage-min 220
python utils/download_pypsa_earth.py DE --voltage-min 220
python utils/download_pypsa_earth.py FR --voltage-min 220
```

### Example 3: Use Downloaded Network

```python
import pypsa

# Load network
network = pypsa.Network()
network.import_from_csv_folder("./networks/KR")

# Analyze
print(f"Buses: {len(network.buses)}")
print(f"Lines: {len(network.lines)}")
print(f"Voltages: {network.buses.v_nom.unique()}")
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

See LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [PyPSA](https://pypsa.readthedocs.io/) - Power system analysis
- [PyPSA-Earth](https://pypsa-earth.readthedocs.io/) - Global energy system modeling
- [earth-osm](https://github.com/pypsa-meets-earth/earth-osm) - OpenStreetMap data access
- [geopy](https://geopy.readthedocs.io/) - Geocoding

## 📞 Support

- **Documentation**: Check README files in project
- **GUI Help**: See [GUI_README.md](GUI_README.md)
- **Setup Issues**: See [SETUP.md](SETUP.md)
- **Dependencies**: See [DEPENDENCIES.md](DEPENDENCIES.md)

## 🗺️ Roadmap

Future enhancements:
- [ ] More visualization tools in GUI
- [ ] Network comparison features
- [ ] Batch processing for multiple countries
- [ ] Export to additional formats
- [ ] Advanced filtering options

---

**Version:** 1.0
**Status:** Stable and Active
**Last Updated:** 2024
