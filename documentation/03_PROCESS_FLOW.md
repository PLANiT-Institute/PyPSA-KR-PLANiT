# Process Flow Documentation

This document explains the complete execution process, data flow, and decision logic of the PyPSA Alternative project.

## Table of Contents

1. [Overall Architecture](#overall-architecture)
2. [Data Flow Diagram](#data-flow-diagram)
3. [Detailed Process Steps](#detailed-process-steps)
4. [Decision Trees](#decision-trees)
5. [Component Interactions](#component-interactions)
6. [Error Handling](#error-handling)

---

## Overall Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     PyPSA Alternative                        │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │ Main Scripts │   │   Libraries  │   │    Config    │   │
│  ├──────────────┤   ├──────────────┤   ├──────────────┤   │
│  │ singlenode   │   │  config.py   │   │    .xlsx     │   │
│  │ province     │   │  data_loader │   │   files      │   │
│  │ group        │   │  temporal    │   │              │   │
│  └──────┬───────┘   │  carrier_std │   └───────┬──────┘   │
│         │           │  component   │           │           │
│         │           │  cc_merger   │           │           │
│         │           │  generator   │           │           │
│         │           │  energy      │           │           │
│         └───────────┤  aggregators │◄──────────┘           │
│                     │  region_agg  │                        │
│                     │  resample    │                        │
│                     │  visualize   │                        │
│                     └──────┬───────┘                        │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   PyPSA Core    │
                    │  (optimization) │
                    └─────────────────┘
```

### Data Sources

```
Input Data Structure:
├── config/
│   ├── config_single.xlsx      # Single-node configuration
│   ├── config_province.xlsx    # Province-level configuration
│   └── config_group.xlsx       # Group-level configuration
│
├── data/
│   ├── 2024/                   # Base year network data (CSV folder)
│   │   ├── buses.csv
│   │   ├── generators.csv
│   │   ├── lines.csv
│   │   ├── loads.csv
│   │   ├── generators_t/
│   │   │   └── p_max_pu.csv
│   │   └── loads_t/
│   │       └── p_set.csv
│   │
│   ├── monthly_costs.csv       # Monthly fuel costs, etc.
│   └── hourly_data.csv         # Hourly capacity factors, etc.
│
└── output/
    └── (generated results)
```

---

## Data Flow Diagram

### High-Level Data Flow

```
┌─────────────┐
│   Config    │
│  (.xlsx)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│   Network   │      │ Time-Series  │
│   (CSV)     │      │ Data (CSV)   │
└──────┬──────┘      └──────┬───────┘
       │                    │
       └──────────┬─────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Load & Parse  │
         │   (Step 1-2)   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Merge & Apply │
         │   Data         │
         │   (Step 3-6)   │
         └────────┬───────┘
                  │
                  ▼
      ┌───────────────────────┐
      │   Regional            │
      │   Aggregation         │
      │   (Optional,Step 7)   │
      └───────────┬───────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Standardize & │
         │  Configure     │
         │   (Step 8-10)  │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Temporal Ops  │
         │  (Optional,    │
         │   Step 11-12)  │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Optimization  │
         │   (PyPSA)      │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Visualization  │
         │  & Results     │
         └────────────────┘
```

---

## Detailed Process Steps

### Step 1: Configuration Loading

**Module:** `libs.config.load_config()`

**Input:**
- Excel file path (e.g., 'config/config_group.xlsx')

**Process:**
1. Detect file type (.xlsx or .yaml)
2. Read all sheets from Excel
3. Parse each sheet into Python data structures:
   - DataFrames → keep as DataFrame (resample_rules, province_mapping)
   - key-value pairs → dict
   - Lists → Python list
4. Convert data types (TRUE/FALSE → bool, numbers → int/float)

**Output:**
```python
config = {
    'carrier_mapping': {...},
    'generator_attributes': {...},
    'Base_year': {'year': 2024, 'file_path': 'data/2024'},
    'monthly_data': {'file_path': '...'},
    'snapshot_data': {'file_path': '...'},
    'regional_aggregation': {...},
    'modelling_setting': {...},
    ...
}
```

**Decision Points:**
- If `.xlsx`: Use `load_config_from_excel()`
- If `.yaml`: Use `yaml.safe_load()`
- Sheet exists? Load it. Otherwise: skip (optional sheets)

---

### Step 2: Network Loading

**Module:** `libs.data_loader.load_network()`

**Input:**
- config['Base_year']['file_path']

**Process:**
1. Create empty PyPSA Network
2. Import from CSV folder:
   ```
   network.import_from_csv_folder('data/2024/')
   ```
3. Clean cc_group column (empty strings → pd.NA)
4. Convert ALL datetime indices to day-first format:
   - network.snapshots → DatetimeIndex
   - generators_t.*.index → DatetimeIndex
   - loads_t.*.index → DatetimeIndex
   - All other *_t indices → DatetimeIndex

**Output:**
- PyPSA Network object with:
  - Static tables: buses, generators, loads, lines, etc.
  - Time-series tables: generators_t, loads_t, etc.
  - All datetime indices properly formatted

**Critical:**
- Date parsing uses **day-first=True**
- '01/03/2024' = 1st March, not 3rd January
- All time-series must have consistent datetime indices

---

### Step 3: Combined Cycle Merging

**Module:** `libs.cc_merger.merge_cc_generators()`

**Input:**
- Network with cc_group column
- config['cc_merge_rules']

**Process:**

```
For each unique cc_group:
  1. Find all generators with this cc_group
  2. For each attribute (p_nom, efficiency, etc.):
     - Look up aggregation rule
     - Apply rule (sum, mean, oldest, etc.)
  3. Create merged generator named {cc_group}_CC
  4. Remove original generators
```

**Aggregation Logic:**

| Attribute | Rule | Implementation |
|-----------|------|----------------|
| p_nom | sum | `group_data['p_nom'].sum()` |
| efficiency | mean | `group_data['efficiency'].mean()` |
| build_year | oldest | `group_data['build_year'].min()` |
| carrier | carrier | Use carrier value directly |
| cc_group | cc_group | Use group name |
| bus | p_nom | From generator with largest p_nom |

**Output:**
- Network with merged CC generators
- Original individual units removed

**Example:**
```
Before: 당진1-GT, 당진1-ST (cc_group='당진1CC')
After:  당진1CC_CC (p_nom = sum of both)
```

---

### Step 4: Monthly Data Application

**Module:** `libs.temporal_data.apply_monthly_data_to_network()`

**Input:**
- network
- config
- monthly_df (from `load_monthly_data()`)

**Process:**

```
1. Filter active records (status=TRUE)
2. Group by (components, components_t, attribute, aggregation)
3. For each component instance (generator/load/storage):
   a. Match by carrier (exact match, no mapping)
   b. Match by region based on aggregation level:
      - national: region='KR'
      - province: region=component.province
      - generator: name=component_name (fallback to province)
   c. Expand monthly values to all snapshots in that month
   d. Forward fill missing values
4. Create time-series DataFrame
5. Assign to network.{component}_t.{attribute}
```

**Matching Logic:**

```python
if aggregation == 'national':
    use data where region = config['regional_settings']['national_region']
elif aggregation == 'province':
    use data where region = generator.province
elif aggregation == 'generator':
    use data where name = generator.name
    if not found: fallback to province
```

**Output:**
- network.generators_t.fuel_cost (monthly values expanded to hourly)
- network.generators_t.marginal_cost (if in data)
- Any other monthly time-series attributes

---

### Step 5: Snapshot Data Application

**Module:** `libs.temporal_data.apply_snapshot_data_to_network()`

**Input:**
- network
- config
- snapshot_df (from `load_snapshot_data()`)

**Process:**

```
1. Filter active records (status=TRUE)
2. Group by (components, components_t, attribute, aggregation)
3. For each component instance:
   a. Match by carrier
   b. Match by region (same logic as monthly data)
   c. Merge data by exact snapshot timestamp
4. Create time-series DataFrame
5. Assign to network.{component}_t.{attribute}
```

**Difference from monthly:**
- Matches by **exact timestamp**, not month
- No forward fill (data must exist for each snapshot)

**Output:**
- network.generators_t.p_max_pu (hourly capacity factors)
- network.loads_t.p_set (hourly load profile)
- Any other hourly time-series attributes

---

### Step 6: Marginal Cost Assignment

**Code:**
```python
network.generators_t.marginal_cost = network.generators_t.fuel_cost
```

**Purpose:**
- Sets generator operating cost equal to fuel cost
- Used in optimization objective function
- Can be overridden if marginal_cost data exists separately

---

### Step 7: Regional Aggregation (Optional)

**Module:** `libs.region_aggregator.aggregate_network_by_region()`

**When:** Only in main_province.py and main_group.py

**Input:**
- network (with original buses)
- config['regional_aggregation']

**Process:**

#### 7a. Create Bus-to-Region Mapping

```
For each bus:
  region = bus.{region_column}  # e.g., bus.province
  standardized = standardize_region_name(region, mapping)
  bus_to_region[bus_name] = standardized
```

#### 7b. Remap Components to Regional Buses

**Generators:**
```
For each generator:
  old_bus = generator.bus
  new_bus = bus_to_region[old_bus]
  generator.bus = new_bus
```

**Loads:**
```
1. Group loads by region
2. Create load_shares from province_demand config
3. For each regional bus:
   regional_load[t] = total_load[t] × load_share[region]
```

**Lines:**
```
For each line:
  bus0_region = bus_to_region[line.bus0]
  bus1_region = bus_to_region[line.bus1]
  line.bus0 = bus0_region
  line.bus1 = bus1_region
```

#### 7c. Aggregate Lines by Region Pairs

```
Group lines by (bus0, bus1) or (bus0, bus1, v_nom):

For each group:
  Apply aggregation rules:
    - num_parallel: sum (or max, mean)
    - s_nom: sum (or max, scale_by_circuits)
    - r, x, b: weighted_by_circuits (or mean, min, max)
    - length: mean (or max, min)

  Create aggregated line: {bus0}-{bus1}-{v_nom}kV
  Remove original lines
```

**Weighted Impedance Calculation:**
```python
# For r (resistance):
r_aggregated = sum(r_i × circuits_i) / sum(circuits_i)

# Example:
# Line 1: r=0.05, circuits=2
# Line 2: r=0.06, circuits=1
# Result: (0.05×2 + 0.06×1) / (2+1) = 0.053
```

#### 7d. Remove Self-Loops (Optional)

```
If remove_self_loops = TRUE:
  Remove all lines where bus0 == bus1
  (intra-regional transmission eliminated)
```

#### 7e. Aggregate Generators by Carrier (Optional)

```
If aggregate_by_carrier = TRUE:
  Use aggregators.aggregate_generators_by_carrier_and_region()

  For each (carrier, region) pair:
    - Aggregate static attributes (p_nom: sum, efficiency: mean, etc.)
    - Aggregate time-series (p_max_pu: mean, marginal_cost: mean, etc.)
    - Create new generator: {carrier}_{region}
    - Remove original generators
```

#### 7f. Create Regional Buses

```
For each unique region:
  Create bus named: standardized_region_name
  Inherit attributes from representative original bus
```

#### 7g. Second-Level Group Aggregation (Optional)

```
If aggregate_regions_by_group = TRUE:
  region_groups = config['regional_aggregation']['region_groups']  # 'group1' or 'group2'

  Repeat steps 7a-7f, but:
    - Use province_mapping[region_groups] instead of 'short'
    - Aggregate from provincial buses → group buses
    - Example: All '육지' provinces → single '육지' bus
```

**Output:**
- Network with regional buses (e.g., 17 provincial or 2-3 group buses)
- Aggregated lines between regions
- Redistributed loads
- Generators mapped to regional buses

---

### Step 8: Carrier Standardization

**Module:** `libs.carrier_standardization.standardize_carrier_names()`

**Input:**
- network (with original Korean carrier names)
- config['carrier_mapping']

**Process:**

```
For each component with 'carrier' column:
  For each row:
    old_carrier = row['carrier']
    new_carrier = carrier_mapping.get(old_carrier, old_carrier)
    row['carrier'] = new_carrier

Update network.carriers:
  - Add new carriers (if don't exist)
  - Remove old carriers (if no longer used)
```

**Mapping Example:**
```python
carrier_mapping = {
    'LNG복합': 'gas',
    '석탄화력': 'coal',
    '원자력': 'nuclear',
    '태양광': 'solar',
    '풍력': 'wind',
    '수력': 'hydro',
    'ESS': 'battery',
}
```

**Output:**
- All components use English carrier names
- network.carriers contains only English names

---

### Step 9: Generator Dispatch Profile

**Module:** `libs.generator_p_set.set_generator_p_set()`

**Input:**
- network
- carrier_list = ['solar', 'wind']

**Process:**

```
For each generator in carrier_list:
  If generators_t.p_max_pu exists for this generator:
    p_set[t] = p_nom × p_max_pu[t]
    Remove p_max_pu column (p_set takes precedence)
```

**Formula:**
```python
# Example: Solar generator with p_nom=100 MW
# generators_t.p_max_pu:
#   00:00 → 0.0
#   06:00 → 0.3
#   12:00 → 0.9
#   18:00 → 0.2
#   23:00 → 0.0

# Resulting p_set:
#   00:00 → 0 MW    (100 × 0.0)
#   06:00 → 30 MW   (100 × 0.3)
#   12:00 → 90 MW   (100 × 0.9)
#   18:00 → 20 MW   (100 × 0.2)
#   23:00 → 0 MW    (100 × 0.0)
```

**Effect:**
- Solar and wind become **must-run**
- Their dispatch follows weather/capacity factor
- Optimizer cannot curtail them

**Output:**
- network.generators_t.p_set created for solar/wind
- network.generators_t.p_max_pu removed for these generators

---

### Step 10: Component Attributes

**Module:** `libs.component_attributes.apply_generator_attributes()`

**Input:**
- network
- config['generator_attributes']

**Process:**

```
1. Apply 'default' attributes to ALL generators:
   For each attribute in generator_attributes['default']:
     network.generators[attribute] = value

2. Apply carrier-specific attributes:
   For each carrier in generator_attributes:
     If carrier != 'default':
       Find generators with this carrier
       For each attribute:
         network.generators.loc[carrier_gens, attribute] = value
```

**Attribute Hierarchy:**
```
1. PyPSA defaults (most general)
2. Config 'default' values (override PyPSA)
3. Carrier-specific values (override 'default')
```

**Example:**
```python
generator_attributes = {
    'default': {
        'ramp_limit_up': 100,      # All generators
        'ramp_limit_down': 100,
    },
    'gas': {
        'p_min_pu': 0.2,           # Gas-specific
        'efficiency': 0.55,
    },
    'nuclear': {
        'p_min_pu': 0.8,           # Nuclear-specific
        'max_cf': 0.95,
        'min_cf': 0.80,
    },
}

# Result:
# All generators get ramp_limit_up=100
# Gas generators also get p_min_pu=0.2, efficiency=0.55
# Nuclear generators also get p_min_pu=0.8, max_cf=0.95, min_cf=0.80
```

**Special Handling:**
- Skips `p_max_pu` if `generators_t.p_max_pu` exists (time-series has priority)

**Storage Units:**
Similarly, `apply_storage_unit_attributes()` applies:
- efficiency_store, efficiency_dispatch
- max_hours
- standing_loss

**Output:**
- network.generators with all attributes set
- network.storage_units with all attributes set

---

### Step 11: Snapshot Limiting (Optional)

**Module:** `libs.resample.limit_snapshots()`

**When:** Only in main_group.py (if configured)

**Input:**
- network
- snapshot_start (from config['modelling_setting'])
- snapshot_end (from config['modelling_setting'])

**Process:**

```
1. Parse snapshot_start to datetime (day-first!)
2. Find start_idx = network.snapshots.searchsorted(start_date)
3. Calculate end_idx = start_idx + snapshot_end
4. Slice network.snapshots[start_idx:end_idx]
5. Slice all time-series data to match:
   generators_t.*[start_idx:end_idx]
   loads_t.*[start_idx:end_idx]
   etc.
```

**Example:**
```python
# Config:
snapshot_start = '01/01/2024 00:00'
snapshot_end = 168  # 7 days × 24 hours

# Result:
# network.snapshots = 168 hourly snapshots from Jan 1-7
```

**Output:**
- network with reduced snapshots (subset of original)
- All time-series data limited to same subset

---

### Step 12: Energy Constraints

**Module:** `libs.energy_constraints.apply_cf_energy_constraints()`

**Input:**
- network
- config['generator_attributes'] (max_cf, min_cf)
- optimization_snapshots

**Process:**

```
1. Calculate total_hours from snapshots
2. For each carrier with max_cf or min_cf:
   For each generator of that carrier:
     If max_cf exists:
       e_sum_max = p_nom × max_cf × total_hours
       network.generators.loc[gen, 'e_sum_max'] = e_sum_max

     If min_cf exists:
       e_sum_min = p_nom × min_cf × total_hours
       network.generators.loc[gen, 'e_sum_min'] = e_sum_min
```

**Formula:**
```python
# Nuclear generator: p_nom=1000 MW, max_cf=0.95, min_cf=0.80
# Optimization period: 168 hours

e_sum_max = 1000 × 0.95 × 168 = 159,600 MWh
e_sum_min = 1000 × 0.80 × 168 = 134,400 MWh

# Constraint in optimization:
# sum(p[t] × weight[t] for t in snapshots) <= 159,600
# sum(p[t] × weight[t] for t in snapshots) >= 134,400
```

**Output:**
- network.generators['e_sum_max'] populated
- network.generators['e_sum_min'] populated

---

### Step 13: Temporal Resampling (Optional)

**Module:** `libs.resample.resample_network()`

**When:** Only in main_group.py (if weights > 1)

**Input:**
- network
- weights (from config['modelling_setting'])
- config['resample_rules']

**Process:**

#### 13a. Resample Time-Series

```
1. Calculate new_snapshots by resampling at '{weights}h' frequency
2. For each component_t:
   For each time-series attribute:
     Resample using mean aggregation:
       resampled = df.resample(f'{weights}h').mean()
3. Update network.snapshots = new_snapshots
```

**Example:**
```python
# weights = 4 (4-hour snapshots)

# Before (hourly):
snapshot         load
00:00            5000
01:00            4800
02:00            4600
03:00            4500
04:00            4400

# After (4-hourly):
snapshot         load
00:00            4725  # mean(5000, 4800, 4600, 4500)
04:00            ...
```

#### 13b. Resample Static Attributes

```
For each rule in resample_rules:
  component = rule['component']
  attribute = rule['attribute']
  rule_type = rule['rule']

  If rule_type == 'scale':
    component_df[attribute] *= weights

  If rule_type == 'fixed':
    component_df[attribute] = rule['value']

  If rule_type == 'default':
    component_df[attribute] = PyPSA_default

  If rule_type == 'skip':
    pass  # don't modify
```

**Scaling Example:**
```python
# Rule: ramp_limit_up → scale
# Before: ramp_limit_up = 100 MW/hour
# After:  ramp_limit_up = 400 MW/4-hour (×4)
```

**Output:**
- network with reduced number of snapshots (by factor of weights)
- All time-series resampled to coarser resolution
- Static attributes scaled appropriately

---

### Step 14: Optimization

**PyPSA Core:** `network.optimize()`

**Input:**
- Fully configured network
- Optimization snapshots

**Process:**

PyPSA builds and solves linear program:

```
Minimize:
  sum(generator_marginal_cost × p_gen × weight)
  + sum(line_flow_cost × flow × weight)
  + ...

Subject to:
  Energy balance: generation = load + transmission losses
  Generator limits: p_min <= p_gen <= p_max
  Line limits: |flow| <= s_nom
  Ramp limits: |p_gen[t] - p_gen[t-1]| <= ramp_limit × weight
  Energy constraints: e_sum_min <= sum(p_gen) <= e_sum_max
  Storage constraints: SOC balance, charge/discharge limits
  ...
```

**Output:**
- status: ('ok', 'optimal') if successful
- network.generators_t.p: Optimal generator dispatch
- network.lines_t.p0: Optimal line flows
- network.storage_units_t.p: Optimal storage dispatch
- network.storage_units_t.state_of_charge: Storage levels

---

### Step 15: Visualization

**Module:** `libs.visualization.plot_generation_by_carrier()`

**Input:**
- network (with optimization results)
- config['carriers_order']

**Process:**

```
1. Extract generators_t.p (generation)
2. Extract storage_units_t.p (storage dispatch)
3. Separate storage into:
   - Discharge (positive values)
   - Charge (negative values)
4. Group by carrier and sum
5. Order carriers according to carriers_order
6. Create stacked area chart:
   - X-axis: snapshots
   - Y-axis: Power (MW)
   - Stacked areas by carrier
   - First carrier in config → bottom (baseload)
   - Last carrier in config → top (variable)
```

**Additional Visualizations** (main_group.py):
- `plot_link_and_line_flows()`: Transmission flow chart
- `print_link_and_line_flow_analysis()`: Text statistics

**Output:**
- Interactive Plotly charts displayed in browser
- Statistics printed to console

---

## Decision Trees

### 1. Regional Aggregation Decision

```
Is this main_singlenode.py?
├─ Yes → Skip regional aggregation
└─ No → Is this main_province.py or main_group.py?
    └─ Yes → Perform regional aggregation
        ├─ aggregate_by_region = TRUE?
        │  └─ Yes → Aggregate to provinces
        ├─ aggregate_by_carrier = TRUE?
        │  └─ Yes → Merge generators by (carrier, region)
        └─ aggregate_regions_by_group = TRUE?
           └─ Yes → Further aggregate to groups
              └─ Use province_mapping[region_groups] column
```

### 2. Temporal Resampling Decision

```
Is weights > 1?
├─ No → Use original snapshots (hourly)
└─ Yes → Resample to {weights}-hour snapshots
    ├─ Resample all time-series with mean()
    └─ Apply resample_rules to static attributes
        ├─ scale → multiply by weights
        ├─ fixed → set to specific value
        ├─ default → reset to PyPSA default
        └─ skip → don't modify
```

### 3. Generator Dispatch Decision

```
For each generator:
  Is carrier in ['solar', 'wind']?
  ├─ Yes → Does generators_t.p_max_pu exist?
  │  ├─ Yes → Set p_set = p_nom × p_max_pu (must-run)
  │  └─ No → Leave as optimizable
  └─ No → Leave as optimizable
```

### 4. Carrier Matching Decision

```
For each data row in monthly/snapshot data:
  aggregation level?
  ├─ 'national' → Match carrier + region='KR'
  ├─ 'province' → Match carrier + region=component.province
  └─ 'generator' → Match carrier + name=component.name
      └─ Not found? → Fallback to province match
```

### 5. Line Aggregation Decision

```
For each group of lines between same region pair:
  grouping = 'by_voltage'?
  ├─ Yes → Group separately by voltage level
  │  └─ Result: Multiple lines per region pair
  └─ No (ignore_voltage) → Combine all voltages
     └─ Result: Single line per region pair

  For each attribute (circuits, s_nom, r, x, etc.):
    Apply configured rule (sum, mean, weighted, etc.)
```

---

## Component Interactions

### Interaction Diagram

```
┌─────────────┐
│   Config    │────────────┐
└──────┬──────┘            │
       │                   ▼
       │            ┌─────────────┐
       │            │ Data Loader │
       │            └──────┬──────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  CC Merger  │────▶│   Network   │◀────┐
└─────────────┘     └──────┬──────┘     │
                           │            │
                           ▼            │
                    ┌─────────────┐     │
                    │  Temporal   │     │
                    │    Data     │     │
                    └──────┬──────┘     │
                           │            │
                           ▼            │
                    ┌─────────────┐     │
                    │   Region    │     │
                    │ Aggregator  │─────┘
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Carrier   │
                    │Standardizer │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Component  │
                    │ Attributes  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Generator  │
                    │    p_set    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Energy    │
                    │ Constraints │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Resample   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Optimization│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │Visualization│
                    └─────────────┘
```

### Key Dependencies

1. **Config depends on:** Nothing (entry point)
2. **Data Loader depends on:** Config
3. **CC Merger depends on:** Network, Config
4. **Temporal Data depends on:** Network, Config, Data
5. **Region Aggregator depends on:** Network, Config
6. **Carrier Standardizer depends on:** Network, Config
7. **Component Attributes depends on:** Network, Config, Carrier Standardizer
8. **Generator p_set depends on:** Network, Carrier Standardizer
9. **Energy Constraints depends on:** Network, Config
10. **Resample depends on:** Network, Config
11. **Optimization depends on:** Network (fully configured)
12. **Visualization depends on:** Network (with results)

**Critical Path:**
```
Config → Data Loader → CC Merger → Temporal Data → Carrier Standardizer → Component Attributes → Optimization
```

---

## Error Handling

### Common Errors and Solutions

#### 1. Date Parsing Errors

**Error:**
```
ValueError: time data '01/03/2024' does not match format
```

**Cause:**
- Date format mismatch (day-first vs. month-first)

**Solution:**
- Always use `dayfirst=True` in `pd.to_datetime()`
- Ensure CSV files use DD/MM/YYYY format

---

#### 2. Carrier Mismatch

**Error:**
```
[warn] No generators found for carrier 'LNG복합'
```

**Cause:**
- Carrier standardization happened before data application
- Data uses original names, network uses standardized names

**Solution:**
- Apply temporal data BEFORE standardization
- Or use standardized names in data files

---

#### 3. Missing Time-Series Data

**Error:**
```
KeyError: 'p_max_pu'
```

**Cause:**
- Expected time-series attribute doesn't exist
- Data not loaded or wrong snapshot range

**Solution:**
- Check that snapshot_data.csv contains required attributes
- Verify snapshot range matches data range

---

#### 4. Optimization Infeasibility

**Error:**
```
status = ('warning', 'infeasible')
```

**Cause:**
- Constraints conflict (e.g., load > total capacity)
- Energy constraints too tight
- Transmission capacity insufficient

**Solution:**
- Check generator p_nom values
- Review energy constraints (e_sum_max, e_sum_min)
- Verify transmission capacities after aggregation
- Temporarily relax constraints to identify bottleneck

---

#### 5. Regional Aggregation Errors

**Error:**
```
ValueError: Bus '강원' not found
```

**Cause:**
- Province mapping incomplete
- Region name mismatch

**Solution:**
- Verify province_mapping sheet in config
- Check that all buses have province column
- Ensure mapping covers all regions in network

---

## Summary

The PyPSA Alternative pipeline follows a strict sequence:

1. **Load** configuration and data
2. **Merge** combined cycle units
3. **Apply** time-varying data
4. **Aggregate** spatially (optional)
5. **Standardize** carrier names
6. **Configure** operational parameters
7. **Set** dispatch profiles (renewables)
8. **Apply** energy constraints
9. **Resample** temporally (optional)
10. **Optimize** the network
11. **Visualize** results

Each step modifies the network object, building up to a fully configured optimization problem. The key is maintaining consistency in:
- Datetime formats (always day-first)
- Carrier names (original until standardization step)
- Component references (update after aggregation)
- Time-series indices (match network.snapshots)

---

## Related Documentation

- [Main Scripts Documentation](01_MAIN_SCRIPTS.md)
- [Library Modules Documentation](02_LIBRARY_MODULES.md)
- [Configuration Guide](04_CONFIGURATION_GUIDE.md)
