# PyPSA Alternative - Documentation Index

This directory contains all documentation for the PyPSA Alternative project.

## Quick Navigation

### 📚 Getting Started
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [SETUP.md](SETUP.md) - Installation and setup instructions
- [README.md](README.md) - Main project README

### ⚙️ Configuration Documentation
- **[01_CONFIG_OVERVIEW.md](01_CONFIG_OVERVIEW.md)** - Start here! Overview of the configuration system
- **[02_CONFIG_REFERENCE.md](02_CONFIG_REFERENCE.md)** - Complete reference for all config options
- **[03_CONFIG_QUICK_GUIDE.md](03_CONFIG_QUICK_GUIDE.md)** - Quick lookup tables and examples
- **[04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md)** - Workflows and data processing pipelines

### 🖥️ User Interface
- [GUI_README.md](GUI_README.md) - GUI user guide
- [GUI_FIXES.md](GUI_FIXES.md) - GUI troubleshooting
- [LANGUAGE_SUPPORT.md](LANGUAGE_SUPPORT.md) - Multi-language support

### 🔧 Technical Guides
- [DEPENDENCIES.md](DEPENDENCIES.md) - Project dependencies
- [REVERSE_GEOCODE_GUIDE.md](REVERSE_GEOCODE_GUIDE.md) - Geocoding utilities
- [CHANGES.md](CHANGES.md) - Change log

## Documentation Organization

### Configuration System (New!)

The configuration system documentation is organized into 4 focused documents:

1. **Overview** - High-level introduction, Excel vs YAML, quick start
2. **Reference** - Detailed documentation for each config section
3. **Quick Guide** - Tables, examples, troubleshooting
4. **Workflows** - Step-by-step workflows and data flow

### Legacy Documentation

The following files contain older documentation that may overlap with new docs:
- `CONFIG_SYSTEM_DOCUMENTATION.md` (superseded by 01-04 series)
- `CONFIG_QUICK_REFERENCE.md` (superseded by 03)
- `CONFIG_SUMMARY.txt` (superseded by 01)
- `CONFIG_DOCUMENTATION_INDEX.md` (superseded by this file)

## For Different User Types

### 📊 **Data Analysts** - Start Here:
1. Read [01_CONFIG_OVERVIEW.md](01_CONFIG_OVERVIEW.md)
2. Open `config/config_single.xlsx` and read the NOTES_MANUAL tab
3. Review [03_CONFIG_QUICK_GUIDE.md](03_CONFIG_QUICK_GUIDE.md) for examples
4. Check [04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md) for data processing steps

### 🔬 **Researchers** - Advanced Topics:
1. Start with [02_CONFIG_REFERENCE.md](02_CONFIG_REFERENCE.md)
2. Review [04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md) for methodology
3. Check source code references in each document

### 💻 **Developers** - Code Integration:
1. Read [SETUP.md](SETUP.md) for development environment
2. Review [02_CONFIG_REFERENCE.md](02_CONFIG_REFERENCE.md) for API details
3. Check function references in [04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md)

### 🎯 **End Users** - GUI Usage:
1. Follow [QUICKSTART.md](QUICKSTART.md)
2. Read [GUI_README.md](GUI_README.md)
3. Reference [03_CONFIG_QUICK_GUIDE.md](03_CONFIG_QUICK_GUIDE.md) for configuration

## File Naming Convention

- `00_README.md` - This file (documentation index)
- `01-04_CONFIG_*.md` - Configuration documentation series (numbered for reading order)
- `[TOPIC]_[TYPE].md` - Other documentation (e.g., GUI_README.md, SETUP.md)

## Contributing to Documentation

When adding new documentation:
1. Place in `doc/` directory
2. Use clear, descriptive filenames
3. Add entry to this README
4. Cross-reference related documents
5. Include code examples where appropriate

## Questions or Issues?

- Check the appropriate guide above
- Review troubleshooting sections in each document
- See source code comments for implementation details

---

**Last Updated:** 2024-11-09
**Documentation Version:** 2.0 (Restructured)
