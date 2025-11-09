# Configuration System Overview

## Introduction

The PyPSA Alternative project uses an **Excel-based configuration system** that makes it easy to configure complex energy network models without editing code.

## Why Excel Configuration?

✅ **User-Friendly**: Edit in Excel, no YAML syntax to learn  
✅ **Organized**: Multiple tabs group related settings  
✅ **Documented**: Built-in NOTES_MANUAL tab with comprehensive guide  
✅ **Flexible**: Supports both single-node and regional network analysis  
✅ **Version Control**: Track changes in Git like any other file  

## Configuration File Location

```
config/
├── config_single.xlsx      # Single-node network configuration (recommended)
└── config_province.yaml    # Regional network configuration (YAML, legacy)
```

**Recommended:** Use `config_single.xlsx` for all new projects.

## Excel Workbook Structure

The configuration Excel file contains **8 tabs**:

| Tab # | Tab Name | Purpose |
|-------|----------|---------|
| 0 | **NOTES_MANUAL** | 📖 Complete user manual (read this first!) |
| 1 | **carrier_mapping** | Map fuel types to standardized names |
| 2 | **generator_attributes** | Set operational constraints per carrier |
| 3 | **global_constraints** | System-wide generation limits |
| 4 | **file_paths** | Data file locations |
| 5 | **regional_settings** | Regional analysis parameters |
| 6 | **cc_merge_rules** | Combined cycle generator merging rules |
| 7 | **years** | Years to analyze |

## Quick Start

### 1. Open Configuration File
```
Open: config/config_single.xlsx
```

### 2. Read the Manual
Navigate to the **NOTES_MANUAL** tab and read the comprehensive guide.

### 3. Customize Settings
Edit the tabs according to your needs:
- **carrier_mapping**: Define how fuel types are grouped
- **generator_attributes**: Set min/max power, ramp limits, etc.
- **file_paths**: Point to your data files

### 4. Save and Run
Save the Excel file and run your analysis:
```bash
python main_singlenode.py    # Single-node analysis
python main_region.py        # Regional network analysis
```

## Excel vs YAML

### Excel Configuration (Recommended)
```
config_path = 'config/config_single.xlsx'
```

**Advantages:**
- Visual editing with Excel
- Built-in documentation (NOTES_MANUAL tab)
- Less prone to syntax errors
- Easier for non-programmers

### YAML Configuration (Legacy)
```
config_path = 'config/config_province.yaml'
```

**Advantages:**
- Text-based (good for version control diffs)
- Preferred by some developers
- Supports complex nested structures

Both formats are supported. The system auto-detects based on file extension.

## Configuration Loading

The configuration is loaded in `libs/config.py`:

```python
from libs.config import load_config

# Auto-detects .xlsx or .yaml based on extension
config = load_config('config/config_single.xlsx')

# Access configuration sections
carrier_mapping = config['carrier_mapping']
gen_attrs = config['generator_attributes']
```

## What Each Section Controls

### 1. Carrier Mapping
**Purpose:** Standardize diverse fuel type names  
**Example:** `bituminous`, `anthracite` → `coal`  
**When Applied:** Final step before optimization

### 2. Generator Attributes
**Purpose:** Set operational constraints  
**Example:** Nuclear `p_min_pu=0.6`, Gas `ramp_limit_up=0.2`  
**When Applied:** After carrier standardization

### 3. Global Constraints
**Purpose:** System-wide generation limits  
**Example:** Nuclear ≥ 30% of total generation  
**Status:** Configured but not yet implemented in optimization

### 4. File Paths
**Purpose:** Locate network and time-series data  
**Example:** `data/Singlenode2024`, `data/add/monthly_t.csv`

### 5. Regional Settings
**Purpose:** Define geographical aggregation  
**Example:** `national_region = 'KR'`

### 6. CC Merge Rules
**Purpose:** Combine multi-unit power plants  
**Example:** Gas turbine + steam turbine → single unit

### 7. Years
**Purpose:** Multi-year analysis configuration  
**Current:** Single year (2024), multi-year planned for future

## Workflow Integration

The configuration is used throughout the analysis workflow:

```
1. Load Config
   ↓
2. Load Network (uses file_paths)
   ↓
3. Merge CC Generators (uses cc_merge_rules)
   ↓
4. Apply Monthly/Snapshot Data (uses file_paths)
   ↓
5. Standardize Carriers (uses carrier_mapping)
   ↓
6. Apply Generator Attributes (uses generator_attributes)
   ↓
7. Optimize Network
   ↓
8. Results & Visualization
```

## Next Steps

📖 **Read Next:**
- [02_CONFIG_REFERENCE.md](02_CONFIG_REFERENCE.md) - Detailed reference for each section
- [03_CONFIG_QUICK_GUIDE.md](03_CONFIG_QUICK_GUIDE.md) - Quick lookup and examples
- [04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md) - Workflows and data processing

💡 **Practical Steps:**
1. Open `config/config_single.xlsx`
2. Read the NOTES_MANUAL tab
3. Customize settings for your analysis
4. Run `python main_singlenode.py`

## Troubleshooting

### Config file not loading
- Check file extension (.xlsx for Excel, .yaml for YAML)
- Verify file path is correct
- Ensure openpyxl is installed: `pip install openpyxl`

### Data not being applied to generators
- Verify carrier names in data files match **original** carrier names
- Check that carrier_mapping occurs AFTER data loading
- Review [04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md) for correct order

### Excel file corrupted
- Keep a backup copy
- Re-export from YAML if needed (YAML is the source of truth)

## Support

- **Built-in Manual:** NOTES_MANUAL tab in Excel file
- **Code Reference:** See `libs/config.py` for loading logic
- **Examples:** Check `03_CONFIG_QUICK_GUIDE.md` for templates

---

**Version:** 2.0  
**Last Updated:** 2024-11-09
