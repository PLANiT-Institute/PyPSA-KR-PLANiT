# PyPSA Alternative - Library Organization

This document describes the organization and purpose of each library module.

## Library Modules

### 1. **config.py**
**Purpose:** Configuration file loading and parsing

**Functions:**
- `load_config()` - Load YAML or Excel configuration files
- `load_config_from_excel()` - Excel-specific configuration loading

**Usage:**
```python
from libs.config import load_config
config = load_config('config/config_single.xlsx')
```

---

### 2. **data_loader.py**
**Purpose:** Load base network data and data files

**Functions:**
- `load_network()` - Load PyPSA network from CSV folder
- `load_monthly_data()` - Load monthly time-series data CSV
- `load_snapshot_data()` - Load snapshot/hourly time-series data CSV

**Usage:**
```python
from libs.data_loader import load_network, load_monthly_data, load_snapshot_data
network = load_network(config)
monthly_df = load_monthly_data(config)
snapshot_df = load_snapshot_data(config)
```

---

### 3. **temporal_data.py** ⭐ NEW
**Purpose:** Apply time-varying data to network components

**Functions:**
- `apply_monthly_data_to_network()` - Apply monthly time-series data (fuel costs, etc.)
- `apply_snapshot_data_to_network()` - Apply hourly time-series data (availability, prices)

**Usage:**
```python
from libs.temporal_data import apply_monthly_data_to_network, apply_snapshot_data_to_network
network = apply_monthly_data_to_network(network, config, monthly_df)
network = apply_snapshot_data_to_network(network, config, snapshot_df)
```

**Note:** These functions work with ORIGINAL carrier names (before standardization)

---

### 4. **carrier_standardization.py** ⭐ NEW
**Purpose:** Standardize carrier names across network components

**Functions:**
- `standardize_carrier_names()` - Map original carrier names to standardized names

**Usage:**
```python
from libs.carrier_standardization import standardize_carrier_names
carrier_mapping = config.get('carrier_mapping', {})
network = standardize_carrier_names(network, carrier_mapping)
```

**Note:** Called at the END of workflow, after all data is loaded

---

### 5. **component_attributes.py** ⭐ NEW
**Purpose:** Apply operational attributes to network components

**Functions:**
- `apply_generator_attributes()` - Set p_min_pu, p_max_pu, ramp limits, etc. for generators
- `apply_storage_unit_attributes()` - Set efficiency, max_hours, etc. for storage units

**Usage:**
```python
from libs.component_attributes import apply_generator_attributes, apply_storage_unit_attributes
generator_attributes = config.get('generator_attributes', {})
network = apply_generator_attributes(network, generator_attributes)

storage_unit_attributes = config.get('storage_unit_attributes', {})
network = apply_storage_unit_attributes(network, storage_unit_attributes)
```

**Note:** Called AFTER carrier standardization

---

### 6. **cc_merger.py**
**Purpose:** Merge combined cycle generators

**Functions:**
- `merge_cc_generators()` - Combine multiple units of combined cycle power plants

**Usage:**
```python
from libs.cc_merger import merge_cc_generators
network = merge_cc_generators(network, config)
```

**Note:** Called BEFORE data application

---

### 7. **generator_p_set.py**
**Purpose:** Set fixed dispatch for generators

**Functions:**
- `set_generator_p_set()` - Set p_set (fixed dispatch) for generators
- `clear_generator_p_set()` - Remove fixed dispatch, make generators optimizable

**Usage:**
```python
from libs.generator_p_set import set_generator_p_set
# Set p_set for solar and wind only
network = set_generator_p_set(network, carrier_list=['solar', 'wind'])

# Or set p_set for all generators with p_max_pu data
network = set_generator_p_set(network)
```

**Note:** Called AFTER carrier standardization

---

### 8. **region_aggregator.py**
**Purpose:** Aggregate network by geographical regions

**Functions:**
- `aggregate_network_by_region()` - Main regional aggregation function
- Internal helper functions for buses, lines, links, loads aggregation

**Usage:**
```python
from libs.region_aggregator import aggregate_network_by_region
network = aggregate_network_by_region(network, config)
```

**Note:** Used only in main_region.py, not in main_singlenode.py

---

### 9. **aggregators.py**
**Purpose:** Aggregate generators and other components

**Functions:**
- `aggregate_generators_by_carrier_and_region()` - Combine generators by carrier and region

**Usage:**
```python
from libs.aggregators import aggregate_generators_by_carrier_and_region
network = aggregate_generators_by_carrier_and_region(network, config)
```

---

### 10. **global_constraints.py**
**Purpose:** Add system-wide constraints

**Functions:**
- `add_global_constraints()` - Add capacity factor constraints (currently not implemented)

**Status:** ⚠️ Placeholder - not yet functional

---

## Deprecated Libraries

### ~~cost_mapping.py~~ ❌ DEPRECATED
**Status:** Functions moved to new libraries

**Migration:**
- `standardize_carrier_names()` → **carrier_standardization.py**
- `apply_generator_attributes()` → **component_attributes.py**
- `apply_storage_unit_attributes()` → **component_attributes.py**
- `apply_monthly_data_to_network()` → **temporal_data.py**
- `apply_snapshot_data_to_network()` → **temporal_data.py**

---

## Typical Workflow Order

### Single-Node Analysis (main_singlenode.py):
```python
1. load_network()                          # data_loader
2. merge_cc_generators()                   # cc_merger
3. apply_monthly_data_to_network()         # temporal_data
4. apply_snapshot_data_to_network()        # temporal_data
5. standardize_carrier_names()             # carrier_standardization
6. set_generator_p_set()                   # generator_p_set
7. apply_generator_attributes()            # component_attributes
8. apply_storage_unit_attributes()         # component_attributes
9. network.optimize()
```

### Regional Analysis (main_region.py):
```python
1. load_network()                          # data_loader
2. merge_cc_generators()                   # cc_merger
3. apply_monthly_data_to_network()         # temporal_data
4. apply_snapshot_data_to_network()        # temporal_data
5. aggregate_network_by_region()           # region_aggregator
6. standardize_carrier_names()             # carrier_standardization
7. network.optimize()
```

---

## Design Principles

1. **Separation of Concerns:** Each library has a single, clear purpose
2. **Logical Grouping:** Related functions are grouped together
3. **No Hardcoded Defaults:** All values come from config files
4. **Original Data First:** Data loading uses original carrier names
5. **Standardization Last:** Carrier mapping happens at the end

---

**Last Updated:** 2024-11-09
