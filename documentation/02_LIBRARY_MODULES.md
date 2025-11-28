# Library Modules Documentation

This document provides comprehensive documentation for all library modules in the `libs/` folder.

## Table of Contents

1. [Overview](#overview)
2. [config.py](#configpy)
3. [data_loader.py](#data_loaderpy)
4. [temporal_data.py](#temporal_datapy)
5. [carrier_standardization.py](#carrier_standardizationpy)
6. [component_attributes.py](#component_attributespy)
7. [cc_merger.py](#cc_mergerpy)
8. [generator_p_set.py](#generator_p_setpy)
9. [energy_constraints.py](#energy_constraintspy)
10. [aggregators.py](#aggregatorspy)
11. [region_aggregator.py](#region_aggregatorpy)
12. [resample.py](#resamplepy)
13. [visualization.py](#visualizationpy)
14. [bus_mapper.py](#bus_mapperpy)

---

## Overview

The `libs/` folder contains modular Python functions that power the PyPSA Alternative analysis pipeline. Each module has a specific responsibility:

| Module | Primary Function | Used By |
|--------|-----------------|---------|
| config.py | Load and parse configuration files | All main scripts |
| data_loader.py | Load network and time-series data | All main scripts |
| temporal_data.py | Apply time-varying data to network | All main scripts |
| carrier_standardization.py | Standardize carrier names | All main scripts |
| component_attributes.py | Set operational parameters | All main scripts |
| cc_merger.py | Merge combined cycle generators | All main scripts |
| generator_p_set.py | Set fixed generator dispatch | All main scripts |
| energy_constraints.py | Apply energy limits | All main scripts |
| aggregators.py | Aggregate generators by carrier/region | main_province.py, main_group.py |
| region_aggregator.py | Aggregate network by regions | main_province.py, main_group.py |
| resample.py | Temporal resampling and snapshot limiting | main_group.py |
| visualization.py | Create charts and plots | All main scripts |
| bus_mapper.py | Utility for bus name mapping | Internal use |

---

## config.py

**Module:** `libs/config.py`

**Purpose:** Load and parse configuration from YAML or Excel files.

### Functions

#### `load_config(config_path="config.yaml")`

Main entry point for loading configuration.

**Parameters:**
- `config_path` (str): Path to configuration file (.yaml or .xlsx)

**Returns:**
- dict: Configuration dictionary with all settings

**Description:**
Detects file type and delegates to appropriate loader:
- `.xlsx` → `load_config_from_excel()`
- `.yaml` → `yaml.safe_load()`

**Example:**
```python
config = load_config('config/config_group.xlsx')
carrier_mapping = config['carrier_mapping']
generator_attributes = config['generator_attributes']
```

---

#### `load_config_from_excel(excel_path)`

Loads configuration from Excel file with multiple sheets.

**Parameters:**
- `excel_path` (str or Path): Path to Excel configuration file

**Returns:**
- dict: Configuration dictionary

**Expected Excel Sheets:**

1. **carrier_mapping**: Maps original carrier names to standardized names
   - Columns: `original_carrier`, `mapped_carrier`
   - Example: 'LNG복합' → 'gas'

2. **generator_attributes**: Carrier-specific operational parameters
   - Columns: `carrier` (or `carriers`), `p_min_pu`, `p_max_pu`, `max_cf`, `min_cf`, etc.
   - Special carrier 'default' applies to all generators

3. **storage_unit_attributes**: Storage-specific parameters
   - Columns: `carrier`, `efficiency_store`, `efficiency_dispatch`, `max_hours`

4. **global_constraints**: System-wide energy constraints
   - Columns: `carrier`, `min_cf`, `max_cf`

5. **file_paths**: Data file locations
   - Columns: `setting`, `value`
   - Settings: `monthly_data_file`, `snapshot_data_file`, `base_file_path`, `base_year`

6. **regional_settings**: Regional configuration
   - Columns: `setting`, `value`
   - Example: `national_region = 'KR'`

7. **cc_merge_rules**: Combined cycle aggregation rules
   - Columns: `attribute`, `rule`
   - Rules: 'sum', 'mean', 'oldest', 'newest', 'p_nom', 'cc_group', 'others'

8. **years**: List of modeling years
   - Columns: `year`

9. **carrier_order**: Display order for visualization
   - Columns: `carriers`
   - First carrier appears at bottom of stacked chart (baseload)

10. **regional_aggregation** (optional): Regional aggregation settings
    - Columns: `setting`, `value`
    - Key settings:
      - `aggregate_by_region`: TRUE/FALSE
      - `aggregate_by_carrier`: TRUE/FALSE
      - `aggregate_regions_by_group`: TRUE/FALSE
      - `region_column`: 'province'
      - `region_groups`: 'group1' or 'group2'
      - `demand_file`: Path to regional demand data
      - `province_mapping_file`: Path to province mapping

11. **generator_region_agg_rules** (optional): Generator aggregation rules
    - Columns: `attribute`, `rule`
    - Used when aggregating generators by (carrier, region)

12. **generator_t_aggregator_rules** (optional): Time-series aggregation rules
    - Columns: `attribute`, `rule`
    - Rules: 'sum', 'mean', 'max', 'min'

13. **lines_config** (optional): Line aggregation settings
    - Columns: `setting`, `value`
    - Settings:
      - `grouping`: 'by_voltage' or 'ignore_voltage'
      - `circuits_rule`: 'sum', 'max', 'mean'
      - `s_nom_rule`: 'keep_original', 'sum', 'max', 'scale_by_circuits'
      - `impedance_rule`: 'weighted_by_circuits', 'mean', 'min', 'max'
      - `length_rule`: 'mean', 'max', 'min'
      - `remove_self_loops`: TRUE/FALSE

14. **links_config** (optional): Link aggregation settings
    - Same structure as lines_config

15. **province_mapping** (optional): Province name standardization
    - Columns: `short`, `official`, `group1`, `group2`
    - Example: '강원', '강원특별자치도', '육지', '육지'

16. **province_demand** (optional): Regional demand shares
    - Used for distributing loads to provinces

17. **modelling_setting** (optional): Modeling parameters
    - Columns: `attributes`, `value`
    - Attributes:
      - `year`: Modeling year
      - `weights`: Temporal aggregation factor (hours)
      - `snapshot_start`: Start date ('DD/MM/YYYY HH:MM')
      - `snapshot_end`: Number of snapshots

18. **resample_rules** (optional): Resampling configuration
    - Columns: `component`, `attribute`, `rule`, `value`
    - Rules: 'scale', 'fixed', 'default', 'skip'

**Description:**

Reads Excel file and constructs a nested dictionary structure:

```python
config = {
    'carrier_mapping': {'LNG복합': 'gas', ...},
    'generator_attributes': {
        'default': {'ramp_limit_up': 100, ...},
        'gas': {'p_min_pu': 0.2, 'p_max_pu': 1.0, ...},
        ...
    },
    'Base_year': {'year': 2024, 'file_path': 'data/2024'},
    'monthly_data': {'file_path': 'data/monthly_costs.csv'},
    'snapshot_data': {'file_path': 'data/hourly_data.csv'},
    ...
}
```

**Type Conversions:**
- Boolean strings ('TRUE'/'FALSE') → Python bool
- Numeric strings → int or float
- Empty cells → `pd.NA` or `None`

---

## data_loader.py

**Module:** `libs/data_loader.py`

**Purpose:** Load PyPSA network and time-series data from files.

### Functions

#### `load_network(config)`

Load PyPSA network from CSV folder.

**Parameters:**
- `config` (dict): Configuration dictionary with `Base_year['file_path']`

**Returns:**
- pypsa.Network: Loaded network with time-series data

**Description:**

1. Imports network from CSV folder using `network.import_from_csv_folder()`
2. Cleans up empty strings in `cc_group` column (converts to `pd.NA`)
3. Fixes snapshot and time-series indices to DatetimeIndex with **day-first format**
4. Ensures all time-series indices match network.snapshots

**Important:**
- Date format is **day-first** (DD/MM/YYYY), not month-first
- Example: '01/03/2024' = March 1st, 2024 (not January 3rd)

**Example:**
```python
config = load_config('config/config.xlsx')
network = load_network(config)
# network.snapshots is now DatetimeIndex
# All generators_t, loads_t indices are DatetimeIndex
```

---

#### `load_monthly_data(config)`

Load monthly time-series data from CSV.

**Parameters:**
- `config` (dict): Configuration with `monthly_data['file_path']`

**Returns:**
- pd.DataFrame: Monthly data with parsed datetime

**Columns:**
- `snapshot` (datetime): Month (parsed with day-first format)
- `carrier` (str): Generator carrier type
- `components` (str): Component type (e.g., 'generators')
- `components_t` (str): Time-series component (e.g., 'generators_t')
- `attribute` (str): Attribute name (e.g., 'marginal_cost', 'fuel_cost')
- `value` (float): Attribute value
- `status` (bool): Active/inactive flag
- `region` (str): Region name (for regional data)
- `aggregation` (str): 'national', 'province', or 'generator'
- `name` (str, optional): Generator name (for generator-level data)

**Example:**
```python
monthly_df = load_monthly_data(config)
# snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
# 01/01/2024,gas,generators,generators_t,fuel_cost,45.2,TRUE,KR,national
```

---

#### `load_snapshot_data(config)`

Load hourly/sub-hourly time-series data from CSV.

**Parameters:**
- `config` (dict): Configuration with `snapshot_data['file_path']`

**Returns:**
- pd.DataFrame: Snapshot data with parsed datetime

**Columns:**
- `snapshot` (datetime): Timestamp (parsed with day-first format)
- `carrier` (str): Generator carrier type
- `region` (str): Region name
- `aggregation` (str): 'national', 'province', or 'generator'
- `components` (str): Component type
- `components_t` (str): Time-series component
- `attribute` (str): Attribute name (e.g., 'p_max_pu')
- `value` (float): Attribute value
- `status` (bool): Active/inactive flag
- `name` (str, optional): Generator name

**Example:**
```python
snapshot_df = load_snapshot_data(config)
# snapshot,carrier,region,aggregation,components,components_t,attribute,value,status
# 01/01/2024 00:00,solar,KR,national,generators,generators_t,p_max_pu,0.0,TRUE
# 01/01/2024 01:00,solar,KR,national,generators,generators_t,p_max_pu,0.0,TRUE
```

---

## temporal_data.py

**Module:** `libs/temporal_data.py`

**Purpose:** Apply time-varying data to network components.

### Functions

#### `apply_monthly_data_to_network(network, config, monthly_df)`

Apply monthly data to network time-series components.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `config` (dict): Configuration with `regional_settings['national_region']`
- `monthly_df` (pd.DataFrame): Monthly data from `load_monthly_data()`

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

Matches monthly data to generators/loads/storage based on:
1. **Carrier** (exact match, no mapping)
2. **Aggregation level** and **region**:
   - `national`: Matches `region='KR'` (or configured national region)
   - `province`: Matches `region=generator.province`
   - `generator`: Matches `name=generator_name`, with fallback to province

**Process:**
1. Filters active records (`status=TRUE`)
2. Groups by `(components, components_t, attribute, aggregation)`
3. For each component (generator/load/storage):
   - Matches carrier
   - Matches region based on aggregation level
   - Expands monthly values to all snapshots in that month (using `ffill()`)
4. Creates time-series DataFrame and assigns to `network.{component}_t.{attribute}`

**Example:**

Monthly fuel cost data:
```csv
snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
01/01/2024,gas,generators,generators_t,fuel_cost,45.2,TRUE,KR,national
01/02/2024,gas,generators,generators_t,fuel_cost,47.8,TRUE,KR,national
```

Result: `network.generators_t.fuel_cost` has 45.2 for all Jan snapshots, 47.8 for all Feb snapshots.

---

#### `apply_snapshot_data_to_network(network, config, snapshot_df)`

Apply hourly/sub-hourly data to network time-series components.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `config` (dict): Configuration with `regional_settings['national_region']`
- `snapshot_df` (pd.DataFrame): Snapshot data from `load_snapshot_data()`

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

Similar to `apply_monthly_data_to_network`, but matches by exact snapshot timestamp instead of month.

**Process:**
1. Filters active records (`status=TRUE`)
2. Groups by `(components, components_t, attribute, aggregation)`
3. For each component:
   - Matches carrier
   - Matches region based on aggregation level
   - Merges snapshot data by timestamp
4. Creates time-series DataFrame

**Example:**

Hourly capacity factor data:
```csv
snapshot,carrier,region,aggregation,components,components_t,attribute,value,status
01/01/2024 00:00,solar,KR,national,generators,generators_t,p_max_pu,0.0,TRUE
01/01/2024 01:00,solar,KR,national,generators,generators_t,p_max_pu,0.0,TRUE
01/01/2024 12:00,solar,KR,national,generators,generators_t,p_max_pu,0.8,TRUE
```

Result: `network.generators_t.p_max_pu` has hourly values for solar generators.

---

## carrier_standardization.py

**Module:** `libs/carrier_standardization.py`

**Purpose:** Standardize carrier names across network components.

### Functions

#### `standardize_carrier_names(network, carrier_mapping)`

Map original carrier names to standardized names.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `carrier_mapping` (dict): Mapping from old → new carrier names

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

**Why standardize?**
- Data files use Korean names ('LNG복합', '석탄화력')
- Analysis uses English names ('gas', 'coal')
- Standardization happens AFTER data import, BEFORE optimization

**Process:**
1. Updates `carrier` column for all components:
   - generators
   - loads
   - storage_units
   - stores
   - links
   - buses

2. Updates `network.carriers` table:
   - Adds new standardized carriers
   - Removes old carriers that are no longer used

**Example:**
```python
carrier_mapping = {
    'LNG복합': 'gas',
    '석탄화력': 'coal',
    '원자력': 'nuclear',
    '태양광': 'solar',
    '풍력': 'wind',
}

network = standardize_carrier_names(network, carrier_mapping)
# All generators.carrier now use English names
```

**Output:**
```
[info] Standardizing carrier names across all network components...
[info] Carrier standardization complete:
  - Updated 45 generators
  - Updated 10 storage_units
  - network.carriers now has: ['battery', 'coal', 'gas', 'hydro', 'nuclear', 'solar', 'wind']
```

---

## component_attributes.py

**Module:** `libs/component_attributes.py`

**Purpose:** Apply operational parameters to generators and storage units.

### Functions

#### `apply_generator_attributes(network, generator_attributes)`

Set carrier-specific parameters for generators.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `generator_attributes` (dict): Attributes by carrier from config

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

Applies two-tier system:
1. **Default attributes** (carrier='default'): Applied to ALL generators
2. **Carrier-specific attributes**: Override defaults for specific carriers

**Attributes:**
- `p_min_pu`: Minimum output as fraction of p_nom (e.g., 0.2 = 20% minimum)
- `p_max_pu`: Maximum output as fraction of p_nom (static, not time-series)
- `ramp_limit_up`: MW/hour ramp-up rate
- `ramp_limit_down`: MW/hour ramp-down rate
- `max_cf`: Maximum capacity factor (converted to e_sum_max later)
- `min_cf`: Minimum capacity factor (converted to e_sum_min later)
- `efficiency`: Conversion efficiency
- `marginal_cost`: Operating cost (€/MWh)

**Example:**
```python
generator_attributes = {
    'default': {
        'ramp_limit_up': 100,
        'ramp_limit_down': 100,
    },
    'gas': {
        'p_min_pu': 0.2,
        'p_max_pu': 1.0,
        'efficiency': 0.55,
    },
    'coal': {
        'p_min_pu': 0.4,
        'p_max_pu': 1.0,
        'efficiency': 0.40,
    },
    'nuclear': {
        'p_min_pu': 0.8,
        'p_max_pu': 1.0,
        'max_cf': 0.95,
        'min_cf': 0.80,
    },
}

network = apply_generator_attributes(network, generator_attributes)
```

**Output:**
```
[info] Applying carrier-specific generator attributes...
[info] Applying default attributes to ALL generators:
  - ramp_limit_up = 100
  - ramp_limit_down = 100
[info] Applying attributes to 15 gas generators:
  - p_min_pu = 0.2
  - p_max_pu = 1.0
  - efficiency = 0.55
[info] Applied 9 carrier-specific attribute updates
```

**Important:**
- Skips `p_max_pu` if time-series version (`generators_t.p_max_pu`) exists
- Must be called AFTER `standardize_carrier_names()`

---

#### `apply_storage_unit_attributes(network, storage_unit_attributes)`

Set carrier-specific parameters for storage units.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `storage_unit_attributes` (dict): Attributes by carrier

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

Similar to `apply_generator_attributes` but for storage units.

**Attributes:**
- `efficiency_store`: Charging efficiency (0.0-1.0)
- `efficiency_dispatch`: Discharging efficiency (0.0-1.0)
- `max_hours`: Maximum storage duration (energy capacity / power capacity)
- `standing_loss`: Self-discharge rate (fraction per hour)
- `p_min_pu`: Minimum charge/discharge rate
- `p_max_pu`: Maximum charge/discharge rate

**Example:**
```python
storage_unit_attributes = {
    'default': {
        'efficiency_store': 0.95,
        'efficiency_dispatch': 0.95,
    },
    'battery': {
        'max_hours': 4,
        'efficiency_store': 0.90,
        'efficiency_dispatch': 0.90,
        'standing_loss': 0.001,  # 0.1% per hour
    },
    'PSH': {  # Pumped hydro
        'max_hours': 8,
        'efficiency_store': 0.85,
        'efficiency_dispatch': 0.90,
    },
}

network = apply_storage_unit_attributes(network, storage_unit_attributes)
```

---

## cc_merger.py

**Module:** `libs/cc_merger.py`

**Purpose:** Merge combined cycle (CC) power plant units.

### Functions

#### `merge_cc_generators(network, config)`

Aggregate generators with `cc_group` column.

**Parameters:**
- `network` (pypsa.Network): Network to modify
- `config` (dict): Configuration with `cc_merge_rules`

**Returns:**
- pypsa.Network: Modified network (new generators added, old removed)

**Description:**

Combined cycle power plants have multiple units (gas turbine + steam turbine). This function merges them into single generators.

**Identification:**
- Generators with non-null `cc_group` column
- All generators with same `cc_group` value are merged

**Aggregation Rules** (from config):

| Rule | Description | Example |
|------|-------------|---------|
| `sum` | Add values | Total capacity |
| `mean` | Average values | Average efficiency |
| `oldest` / `smallest` | Minimum value | Build year |
| `newest` / `largest` | Maximum value | Latest retrofit |
| `p_nom` | Use value from largest unit | Inherit attributes from largest |
| `cc_group` | Use the group name itself | Preserve group identity |
| `others` | Default rule for unspecified | Fallback behavior |

**Example:**

Before merge:
```
Generator       p_nom  efficiency  build_year  cc_group
당진화력1-GT     400    0.40        2005        당진1CC
당진화력1-ST     200    0.55        2005        당진1CC
당진화력2-GT     400    0.42        2008        당진2CC
당진화력2-ST     200    0.57        2008        당진2CC
```

Config rules:
```python
cc_merge_rules = {
    'p_nom': 'sum',           # Total capacity
    'efficiency': 'mean',      # Average efficiency
    'build_year': 'oldest',    # First build year
    'cc_group': 'cc_group',    # Keep group name
    'others': 'p_nom',         # Inherit from largest
}
```

After merge:
```
Generator        p_nom  efficiency  build_year
당진1CC_CC        600    0.475       2005
당진2CC_CC        600    0.495       2008
```

**Process:**
1. Find all generators with `cc_group` not null
2. Group by `cc_group` value
3. For each group:
   - Apply aggregation rules to static attributes
   - Remove old generators
   - Add new merged generator named `{cc_group}_CC`

---

## generator_p_set.py

**Module:** `libs/generator_p_set.py`

**Purpose:** Set fixed dispatch profiles for generators.

### Functions

#### `set_generator_p_set(network, carrier_list=None, snapshots=None)`

Create fixed dispatch by multiplying `p_nom × p_max_pu`.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `carrier_list` (list or None): Carriers to set p_set for (e.g., `['solar', 'wind']`)
- `snapshots` (pd.Index or None): Snapshots to apply (default: all)

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

**Why use p_set?**
- Makes generators **must-run** (not optimizable)
- Useful for renewable generation (solar/wind follow weather, not economics)
- Prevents curtailment or unrealistic dispatch

**Formula:**
```
p_set[t] = p_nom × generators_t.p_max_pu[t]
```

**Important:**
- Only works with **time-varying** `generators_t.p_max_pu` (not static `generators.p_max_pu`)
- Removes `p_max_pu` columns after setting `p_set` (p_set takes precedence)

**Example:**
```python
# After loading capacity factor data into generators_t.p_max_pu
network = set_generator_p_set(network, carrier_list=['solar', 'wind'])
# Now solar and wind follow their capacity factor profile
```

**Output:**
```
[info] Setting p_set for carriers: ['solar', 'wind']
[info] Found 25 generators with time-varying p_max_pu
[info] Removed p_max_pu for 25 generators (p_set takes precedence)
[info] Breakdown by carrier:
  - solar: 15 generators, 3500.00 MW total
  - wind: 10 generators, 2500.00 MW total
[info] Created p_set for 25 generators × 8760 snapshots
[info] Dispatch statistics:
  - Mean: 1250.45 MW
  - Max:  5800.00 MW
  - Min:  0.00 MW
```

---

#### `clear_generator_p_set(network)`

Remove p_set, making generators dispatchable again.

**Parameters:**
- `network` (pypsa.Network): Network to modify

**Returns:**
- pypsa.Network: Modified network

**Example:**
```python
network = clear_generator_p_set(network)
# All generators now optimizable
```

---

## energy_constraints.py

**Module:** `libs/energy_constraints.py`

**Purpose:** Convert capacity factors into energy sum constraints.

### Functions

#### `apply_cf_energy_constraints(network, generator_attributes, snapshots=None, snapshot_weightings=None)`

Calculate `e_sum_max` and `e_sum_min` from capacity factors.

**Parameters:**
- `network` (pypsa.Network): Network to modify (in place)
- `generator_attributes` (dict): Attributes with `max_cf` and `min_cf`
- `snapshots` (pd.Index or None): Snapshots for constraint (default: all)
- `snapshot_weightings` (pd.Series or None): Duration of each snapshot

**Returns:**
- pypsa.Network: Modified network (same object)

**Description:**

**Capacity Factor Constraints:**

Instead of:
```
generator must run at capacity factor between 80-95%
```

PyPSA uses energy bounds:
```
total energy generation over period must be between X and Y MWh
```

**Formula:**
```python
e_sum_max = p_nom × max_cf × total_hours
e_sum_min = p_nom × min_cf × total_hours
```

Where:
- `p_nom`: Generator nominal capacity (MW)
- `max_cf`: Maximum capacity factor (0.0-1.0)
- `min_cf`: Minimum capacity factor (0.0-1.0)
- `total_hours`: Total hours in optimization period

**Example:**

Generator attributes:
```python
generator_attributes = {
    'nuclear': {
        'max_cf': 0.95,  # Cannot exceed 95% CF
        'min_cf': 0.80,  # Must run at least 80% CF
    },
}
```

For 168-hour optimization (1 week):
```python
# Nuclear generator with p_nom=1000 MW
e_sum_max = 1000 × 0.95 × 168 = 159,600 MWh
e_sum_min = 1000 × 0.80 × 168 = 134,400 MWh
```

**Usage:**
```python
network = apply_cf_energy_constraints(
    network,
    generator_attributes,
    snapshots=optimization_snapshots
)
```

**Output:**
```
[info] Applying capacity factor energy constraints for 168 snapshots (168.0 total hours)...
[info] Applied energy constraints to 3 carrier groups:
  nuclear: max_cf=0.95 (carrier-specific) → e_sum_max=159600 MWh total
  nuclear: min_cf=0.80 (carrier-specific) → e_sum_min=134400 MWh total
  coal: max_cf=0.90 (default) → e_sum_max=302400 MWh total
```

---

## aggregators.py

**Module:** `libs/aggregators.py`

**Purpose:** Aggregate generators by carrier and/or region.

### Functions

#### `aggregate_generators_by_carrier_and_region(network, config, region_column=None, province_mapping=None)`

Merge generators by (carrier, region) combinations.

**Parameters:**
- `network` (pypsa.Network): Network to modify
- `config` (dict): Configuration with aggregation rules
- `region_column` (str or None): Column to group by (e.g., 'province')
- `province_mapping` (dict or None): Name standardization mapping

**Returns:**
- pypsa.Network: Modified network (old generators removed, new added)

**Description:**

**Two modes:**

1. **Carrier-only aggregation** (`region_column=None`):
   - One generator per carrier
   - Named: `{carrier}_aggregated`
   - Example: `gas_aggregated`, `coal_aggregated`

2. **Carrier + Region aggregation** (`region_column='province'`):
   - One generator per (carrier, region) pair
   - Named: `{carrier}_{region}`
   - Example: `gas_강원`, `solar_경기`

**Aggregation Rules** (from `config['generator_region_aggregator_rules']`):

| Attribute | Rule | Result |
|-----------|------|--------|
| p_nom | sum | Total capacity |
| efficiency | mean | Average efficiency |
| build_year | oldest | Earliest build year |
| marginal_cost | mean | Average cost |
| bus | region | Connect to regional bus |
| carrier | carrier | Preserve carrier |
| province | region | Preserve region |
| ... | others (default) | From largest generator |

**Time-Series Aggregation** (from `config['generator_t_aggregator_rules']`):

| Attribute | Rule | Result |
|-----------|------|--------|
| p_max_pu | mean | Average capacity factor |
| marginal_cost | mean | Average marginal cost |
| fuel_cost | mean | Average fuel cost |
| ... | others (default) | Mean of all values |

**Example:**

Before aggregation (50 gas generators in 강원):
```
Generator         p_nom  efficiency  bus      carrier  province
당진_LNG_1        400    0.55        당진_bus  gas      강원
영흥_LNG_2        500    0.58        영흥_bus  gas      강원
...               ...    ...         ...      gas      강원
```

After aggregation:
```
Generator    p_nom   efficiency  bus   carrier  province
gas_강원     12500   0.56        강원   gas      강원
```

**Usage:**
```python
network = aggregate_generators_by_carrier_and_region(
    network,
    config,
    region_column='province',
    province_mapping=province_mapping
)
```

---

## region_aggregator.py

**Module:** `libs/region_aggregator.py`

**Purpose:** Aggregate entire network by geographical regions.

### Key Functions

#### `aggregate_network_by_region(network, config)`

Main function to aggregate network to regional level.

**Parameters:**
- `network` (pypsa.Network): Network to aggregate
- `config` (dict): Configuration with regional aggregation settings

**Returns:**
- pypsa.Network: Aggregated network

**Description:**

Comprehensive network aggregation that:
1. Creates bus-to-region mapping
2. Remaps components to regional buses
3. Aggregates lines/links between regions
4. Distributes loads to regional buses
5. Optionally aggregates generators by carrier
6. Optionally performs second-level group aggregation

**Configuration Settings:**

```python
regional_aggregation = {
    'aggregate_by_region': True,  # Enable regional aggregation
    'region_column': 'province',  # Column to aggregate by
    'aggregate_by_carrier': True,  # Merge generators by carrier
    'aggregate_regions_by_group': False,  # Second-level grouping
    'region_groups': 'group1',  # Group column (if second-level)
    'demand_file': 'data/regional_demand.csv',
    'province_mapping_file': 'data/province_mapping.csv',

    # Line aggregation
    'lines': {
        'grouping': 'by_voltage',  # or 'ignore_voltage'
        'circuits_rule': 'sum',
        's_nom_rule': 'sum',
        'impedance_rule': 'weighted_by_circuits',
        'length_rule': 'mean',
        'remove_self_loops': True,
    },

    # Link aggregation (if network has links)
    'links': {
        'grouping': 'ignore_voltage',
        'p_nom_rule': 'sum',
        ...
    },
}
```

**Line Aggregation:**

When multiple transmission lines connect the same region pair, they are aggregated based on rules:

**Example:** 3 lines from 강원 to 경기

Before aggregation:
```
Line           bus0   bus1   v_nom  num_parallel  s_nom  r       x       length
강원-경기-345kV  강원   경기   345    2             1000   0.05    0.15    120
강원-경기-765kV  강원   경기   765    1             2000   0.03    0.10    118
강원-경기-345kV  강원   경기   345    1             800    0.06    0.18    125
```

After aggregation (grouping='by_voltage'):
```
Line           bus0  bus1  v_nom  num_parallel  s_nom  r      x      length
강원-경기-345kV  강원  경기  345    3             1800   0.053  0.163  122.5
강원-경기-765kV  강원  경기  765    1             2000   0.030  0.100  118.0
```

Rules applied:
- `num_parallel`: sum → 2 + 1 = 3
- `s_nom`: sum → 1000 + 800 = 1800
- `r`, `x`: weighted_by_circuits → weighted average
- `length`: mean → (120 + 125) / 2 = 122.5

**Load Distribution:**

Loads are distributed to regional buses based on demand shares:

```python
# From province_demand config
demand_shares = {
    '강원': 0.05,  # 5% of national demand
    '경기': 0.25,  # 25% of national demand
    '서울': 0.20,  # 20% of national demand
    ...
}

# Applied to each snapshot
regional_load[snapshot, '강원'] = total_load[snapshot] × 0.05
```

---

#### `_aggregate_lines_by_region(network, lines_config, bus_to_region)`

Aggregate transmission lines between regional bus pairs.

**Line Grouping Options:**

1. **by_voltage**: Separate lines by voltage level
   - 345kV lines aggregated separately from 765kV lines
   - Result: Multiple lines per region pair (one per voltage)

2. **ignore_voltage**: Combine all voltages
   - All lines between regions merged into one
   - Result: Single line per region pair

**Aggregation Rules:**

circuits_rule:
- `sum`: Total number of circuits
- `max`: Maximum circuits of any line
- `mean`: Average circuits

s_nom_rule:
- `sum`: Total capacity (parallel lines add)
- `max`: Largest line capacity
- `scale_by_circuits`: Capacity × (total circuits / original circuits)
- `keep_original`: Use value from representative line

impedance_rule:
- `weighted_by_circuits`: Impedance weighted by circuit count
- `mean`: Simple average
- `min`: Minimum impedance
- `max`: Maximum impedance

length_rule:
- `mean`: Average length
- `max`: Maximum length
- `min`: Minimum length

---

#### Group-Level Aggregation

If `aggregate_regions_by_group=TRUE`:

**Example: Two-level aggregation**

Level 1 (Provincial):
```
Bus    group1
강원   육지
경기   육지
서울   육지
제주   제주
```

Level 2 (Group):
```
Bus   Generators              Lines
육지  All mainland gens       육지-제주 (HVDC link)
제주  Jeju island gens
```

This creates high-level scenarios like:
- Mainland vs. Island analysis
- Metropolitan vs. Non-metropolitan

---

## resample.py

**Module:** `libs/resample.py`

**Purpose:** Temporal resampling and snapshot limiting.

### Functions

#### `limit_snapshots(network, snapshot_start=None, snapshot_end=None)`

Limit network to specific date range.

**Parameters:**
- `network` (pypsa.Network): Network to limit (in place)
- `snapshot_start` (str or None): Start date 'DD/MM/YYYY HH:MM' (day-first!)
- `snapshot_end` (int or None): Number of snapshots to include

**Returns:**
- pypsa.Network: Modified network

**Description:**

Slices network snapshots and all time-series data to subset.

**Example:**
```python
# Limit to first week of January 2024
network = limit_snapshots(
    network,
    snapshot_start='01/01/2024 00:00',
    snapshot_end=168  # 7 days × 24 hours
)
# network now has only 168 snapshots
```

**Output:**
```
[info] Limiting snapshots
[info]   Original snapshots: 8760
[info]   Start date: 01/01/2024 00:00 -> 2024-01-01 00:00:00 (index: 0)
[info]   Number of snapshots: 168 (end index: 168)
[info]   generators_t.p_max_pu: limited (8760 -> 168 snapshots)
[info]   loads_t.p_set: limited (8760 -> 168 snapshots)
[info]   Limited snapshots: 168
[info]   Limited snapshot range: 2024-01-01 00:00:00 to 2024-01-07 23:00:00
```

---

#### `resample_network(network, weights=1, resample_rules=None, optimization_snapshots=None)`

Aggregate snapshots temporally (e.g., 1-hour → 4-hour).

**Parameters:**
- `network` (pypsa.Network): Network to resample (in place)
- `weights` (int): Aggregation factor in hours (e.g., 4 for 4-hour snapshots)
- `resample_rules` (pd.DataFrame or None): Static attribute resampling rules
- `optimization_snapshots` (pd.Index or None): Deprecated, not used

**Returns:**
- pypsa.Network: Resampled network

**Description:**

Reduces temporal resolution to speed up optimization.

**Time-Series Resampling:**
- All `_t` components resampled using **mean** aggregation
- Snapshots reduced by factor of `weights`

**Static Attribute Resampling** (optional, from `resample_rules`):

| Component | Attribute | Rule | Action |
|-----------|-----------|------|--------|
| generators | ramp_limit_up | scale | Multiply by weights (4h ramp = 4× 1h ramp) |
| generators | ramp_limit_down | scale | Multiply by weights |
| generators | min_up_time | scale | Multiply by weights (4h snapshots need 4× min uptime) |
| ... | ... | fixed | Set to specific value |
| ... | ... | default | Reset to PyPSA default |
| ... | ... | skip | Don't modify |

**Example:**
```python
# Original: 8760 hourly snapshots
network = resample_network(network, weights=4, resample_rules=resample_rules)
# Result: 2190 four-hourly snapshots (8760 / 4)
```

**Resampling hourly to 4-hourly:**
```
Before (1-hour):
snapshot         load    solar_cf
01/01 00:00      5000    0.0
01/01 01:00      4800    0.0
01/01 02:00      4600    0.0
01/01 03:00      4500    0.0
01/01 04:00      4400    0.1

After (4-hour):
snapshot         load    solar_cf
01/01 00:00      4725    0.025      # mean of 4 hours
01/01 04:00      ...     ...
```

**Ramp Limit Scaling:**
```
Before: ramp_limit_up = 100 MW/hour
After:  ramp_limit_up = 400 MW/4-hour (scaled by weights=4)
```

**Output:**
```
[info] Resampling network to 4-hour snapshots
[info]   Original snapshots: 8760
[info]   Snapshot range: 2024-01-01 00:00:00 to 2024-12-31 23:00:00
[info]   Resample rule: 4h
[info]   New snapshots count: 2190
[info]   Resampled snapshots: 2190
[info]   generators.ramp_limit_up: scaled by 4
[info]   generators.ramp_limit_down: scaled by 4
[info] Resampling complete
```

---

## visualization.py

**Module:** `libs/visualization.py`

**Purpose:** Create interactive charts of optimization results.

### Functions

#### `plot_generation_by_carrier(network, snapshots=None, include_storage=True, title='...', carriers_order=None)`

Create stacked area chart of generation by carrier.

**Parameters:**
- `network` (pypsa.Network): Network with optimization results
- `snapshots` (pd.Index or None): Snapshots to plot
- `include_storage` (bool): Include storage discharge/charge
- `title` (str): Chart title
- `carriers_order` (list or None): Stacking order (first = bottom/baseload)

**Returns:**
- plotly.graph_objects.Figure: Interactive chart

**Description:**

Creates Plotly stacked area chart showing:
- **Generators**: Positive generation (generators_t.p)
- **Storage discharge**: Positive values from storage_units_t.p
- **Storage charge**: Negative values from storage_units_t.p (shown as negative)

**Carrier Ordering:**

The `carriers_order` from config controls stacking:
```python
carriers_order = ['nuclear', 'coal', 'gas', 'hydro', 'battery', 'solar', 'wind']
# First carrier (nuclear) appears at bottom (baseload)
# Last carrier (wind) appears at top (variable)
```

**Example:**
```python
carriers_order = config.get('carriers_order', None)
fig = plot_generation_by_carrier(
    network,
    snapshots=network.snapshots,
    include_storage=True,
    title='Generation by Carrier - Group Level',
    carriers_order=carriers_order
)
fig.show()
```

**Chart Features:**
- Interactive hover showing values
- Unified hover mode (vertical line)
- Datetime x-axis
- Stacked areas with colors by carrier
- Negative values for storage charging

---

#### `plot_link_and_line_flows(network, snapshots=None)`

Create stacked area chart of transmission flows.

**Parameters:**
- `network` (pypsa.Network): Network with optimization results
- `snapshots` (pd.Index or None): Snapshots to plot

**Returns:**
- plotly.graph_objects.Figure or None: Interactive chart

**Description:**

Shows power flows on lines and links:
- Positive values: Power flowing from bus0 → bus1
- Negative values: Power flowing from bus1 → bus0
- Separate trace for each line/link

**Example:**
```python
fig = plot_link_and_line_flows(network)
if fig:
    fig.show()
```

---

#### `print_link_and_line_flow_analysis(network, snapshots=None)`

Print detailed transmission flow statistics.

**Parameters:**
- `network` (pypsa.Network): Network with optimization results
- `snapshots` (pd.Index or None): Snapshots to analyze

**Description:**

Prints text report with:
- Each line/link name
- Maximum flow (MW and % of capacity)
- Average flow (MW)
- Dominant flow direction
- Utilization statistics

**Example Output:**
```
================================================================================
LINK AND LINE FLOW ANALYSIS
================================================================================

Line Flows:
-----------
강원-경기-345kV:
  Max flow: 1500.0 MW (83.3% of capacity)
  Avg flow: 850.5 MW
  Direction: 강원 → 경기 (85% of time)

육지-제주-HVDC:
  Max flow: 2000.0 MW (100.0% of capacity)
  Avg flow: 1250.8 MW
  Direction: 육지 → 제주 (92% of time)
```

---

## bus_mapper.py

**Module:** `libs/bus_mapper.py`

**Purpose:** Utility functions for mapping bus names.

**Description:** Internal helper functions used by region_aggregator.py. Not typically called directly by users.

---

## Summary

The library modules work together in a pipeline:

1. **Configuration** (config.py) → Load all settings
2. **Data Loading** (data_loader.py) → Import network and time-series
3. **Data Application** (temporal_data.py) → Apply time-varying data
4. **Standardization** (carrier_standardization.py) → Unify names
5. **Merging** (cc_merger.py) → Combine CC units
6. **Aggregation** (region_aggregator.py, aggregators.py) → Spatial aggregation
7. **Attributes** (component_attributes.py) → Set operational params
8. **Dispatch** (generator_p_set.py) → Fix renewable generation
9. **Constraints** (energy_constraints.py) → Energy bounds
10. **Resampling** (resample.py) → Temporal aggregation
11. **Optimization** → PyPSA solve
12. **Visualization** (visualization.py) → Display results

Each module is independent and can be used separately, but they're designed to work together in the main scripts.

---

## Related Documentation

- [Main Scripts Documentation](01_MAIN_SCRIPTS.md)
- [Process Flow Documentation](03_PROCESS_FLOW.md)
- [Configuration Guide](04_CONFIGURATION_GUIDE.md)
