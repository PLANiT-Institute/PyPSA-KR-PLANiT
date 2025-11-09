# Configuration Reference

Complete reference for all configuration sections in `config/config_single.xlsx`.

## Tab 1: carrier_mapping

**Purpose:** Map original carrier names to standardized names

**Structure:**
| Column | Description | Example |
|--------|-------------|---------|
| original_carrier | Name in network data | `bituminous` |
| mapped_carrier | Standardized name | `coal` |

**Standard Mappings:**
- Coal: `bituminous`, `anthracite` → `coal`
- Gas: `LNG` → `gas`
- Oil: `heavy oil`, `diesel` → `oil`
- Others: `fuelcell`, `waste`, `miscellaneous` → `others`

**Applied:** Last step before optimization (in `standardize_carrier_names()`)

---

## Tab 2: generator_attributes

**Purpose:** Set operational constraints per carrier type

**Columns:**
- `carriers` (required): Carrier name (after mapping)
- `p_min_pu`: Minimum output (0.0-1.0)
- `p_max_pu`: Maximum output (0.0-1.0)
- `ramp_limit_up`: Max ramp up rate (fraction/hour)
- `ramp_limit_down`: Max ramp down rate (fraction/hour)
- `min_up_time`: Minimum online time (hours)
- `min_down_time`: Minimum offline time (hours)
- `efficiency`: Conversion efficiency (0.0-1.0)
- `max_cf`: Maximum capacity factor

**Typical Values:**
```
Gas:      p_min=0.2-0.4, ramp=0.2-0.5, min_time=4-8h
Coal:     p_min=0.4-0.6, ramp=0.1-0.2, min_time=12-24h
Nuclear:  p_min=0.6-0.8, ramp=0.05, min_time=24-72h
Hydro:    p_min=0.0-0.2, ramp=0.5-1.0, min_time=1h
```

**Applied:** After carrier standardization (in `apply_generator_attributes()`)

---

## Tab 3: global_constraints

**Purpose:** System-wide generation share limits

**Columns:**
- `carrier`: Carrier name (after mapping)
- `min_cf`: Minimum capacity factor (0.0-1.0)
- `max_cf`: Maximum capacity factor (0.0-1.0)

**Status:** ⚠️ Not yet implemented in optimization

---

## Tab 4: file_paths

**Purpose:** Specify data file locations

**Settings:**
```
monthly_data_file:  data/add/monthly_t.csv
snapshot_data_file: data/add/snapshot_t.csv
base_year:          2024
base_file_path:     data/Singlenode2024
```

**Data File Requirements:**
- `base_file_path`: Must contain PyPSA network CSVs (buses.csv, generators.csv, loads.csv)
- `monthly_data_file`: Monthly time-series (fuel costs, etc.)
- `snapshot_data_file`: Hourly time-series (availability, prices)

---

## Tab 5: regional_settings

**Purpose:** Regional analysis parameters

**Settings:**
- `national_region`: Code for national-level data (e.g., `KR`)

Used for filtering data by aggregation level (national vs provincial).

---

## Tab 6: cc_merge_rules

**Purpose:** Define how to merge combined cycle (CC) generators

**Available Rules:**
- `oldest`: Use minimum value (for build_year)
- `newest`: Use maximum value
- `largest`: Use maximum value (for capital_cost)
- `smallest`: Use minimum value
- `p_nom`: Use value from largest unit
- `sum`: Add all values (for capacities)
- `mean`: Average all values
- `cc_group`: Use CC group name
- `remove`: Delete attribute

**Standard Configuration:**
```
p_nom:        sum      (total capacity)
build_year:   oldest   (conservative)
capital_cost: largest  (conservative)
name:         cc_group (use group ID)
others:       p_nom    (fallback rule)
```

**Applied:** Early in workflow (in `merge_cc_generators()`)

---

## Tab 7: years

**Purpose:** List of years to analyze

**Current Use:** Single-year (2024)  
**Future:** Multi-year analysis support

---

## Configuration Loading API

```python
from libs.config import load_config

# Load config (auto-detects Excel or YAML)
config = load_config('config/config_single.xlsx')

# Access sections
carrier_mapping = config['carrier_mapping']           # dict
gen_attrs = config['generator_attributes']            # dict
global_constr = config['global_constraints']          # dict
monthly_file = config['monthly_data']['file_path']    # str
snapshot_file = config['snapshot_data']['file_path']  # str
base_year = config['Base_year']['year']               # int
base_path = config['Base_year']['file_path']          # str
national = config['regional_settings']['national_region']  # str
cc_rules = config['cc_merge_rules']                   # dict
years = config['Years']                               # list
```

---

**See Also:**
- [01_CONFIG_OVERVIEW.md](01_CONFIG_OVERVIEW.md) - Overview
- [03_CONFIG_QUICK_GUIDE.md](03_CONFIG_QUICK_GUIDE.md) - Examples
- [04_CONFIG_WORKFLOWS.md](04_CONFIG_WORKFLOWS.md) - Workflows
