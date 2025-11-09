# PyPSA Configuration System Documentation

Comprehensive guide to the PyPSA configuration system, including all config sections, available options, and how they're used throughout the codebase.

## Table of Contents
1. [Configuration Overview](#configuration-overview)
2. [Config File Formats](#config-file-formats)
3. [Configuration Sections](#configuration-sections)
4. [Workflow and Execution Order](#workflow-and-execution-order)
5. [Data Flow](#data-flow)
6. [Examples](#examples)

---

## Configuration Overview

The configuration system manages:
- **Carrier name mapping** - Standardizes carrier names across data sources
- **Generator attributes** - Sets power plant operational parameters per carrier
- **Global constraints** - Sets system-wide generation limits
- **CC (Combined Cycle) generator merging** - Aggregates multi-unit generators
- **Regional aggregation** - Groups network components by geography
- **Data file paths** - Locates monthly and snapshot time-series data
- **Regional settings** - Defines region-specific parameters
- **Time periods** - Specifies modeling years

---

## Config File Formats

### Supported Formats

The system supports two file formats:
- **YAML** (.yaml) - Simple text format, easy to edit manually
- **Excel** (.xlsx) - Spreadsheet format with multiple tabs

### Loading Configuration

```python
from libs.config import load_config

# YAML format
config = load_config("config/config_single.yaml")

# Excel format
config = load_config("config/config_single.xlsx")
```

### File Structure for Excel Format

When using Excel, the following sheets are required:

| Sheet Name | Columns | Purpose |
|-----------|---------|---------|
| `carrier_mapping` | original_carrier, mapped_carrier | Maps carrier names |
| `generator_attributes` | carrier, p_min_pu, p_max_pu, max_cf, ... | Generator operational limits |
| `global_constraints` | carrier, min_cf, max_cf | System-wide generation constraints |
| `file_paths` | setting, value | Paths to data files |
| `regional_settings` | setting, value | Regional configuration |
| `cc_merge_rules` | attribute, rule | Rules for merging CC generators |
| `years` | year | Modeling years |

---

## Configuration Sections

### 1. carrier_mapping

**Purpose:** Maps original carrier names from data sources to standardized network carrier names.

**Why needed:** Data files often use different naming conventions than the network model. This section ensures consistent carrier names throughout the system.

**Format:**

```yaml
carrier_mapping:
  # Original carrier name: Standardized carrier name
  bituminous: coal
  anthracite: coal
  LNG: gas
  nuclear: nuclear
  wind: wind
  solar: solar
  hydro: hydro
  PSH: PSH
  bio: bio
  oil: oil
  diesel: oil
  fuelcell: others
  IGCC: others
  miscellaneous: others
```

**Example:** All three coal types (bituminous, anthracite, and others) are mapped to a single "coal" carrier in the network. This simplifies the model while preserving data distinctions.

**When used:**
1. Data is loaded with original carrier names
2. Mapping applied at the END via `standardize_carrier_names()` before optimization
3. This ensures data loading uses original names, final network uses standardized names

**Function:** `libs/cost_mapping.py::standardize_carrier_names()`
- Updates all components (generators, loads, storage units, etc.) with new carrier names
- Adds new carriers to `network.carriers` table
- Removes unused old carriers

---

### 2. generator_attributes

**Purpose:** Sets operational constraints for generators grouped by carrier type.

**What it does:** These attributes define technical limits that apply to ALL generators of a given carrier type.

**Format:**

```yaml
generator_attributes:
  gas:
    p_min_pu: 0.2          # Minimum output: 20% of capacity
    p_max_pu: 1.0          # Maximum output: 100% of capacity
    max_cf: 0.5            # Maximum capacity factor: 50%
  coal:
    p_min_pu: 0.4          # Minimum output: 40% of capacity
    p_max_pu: 1.0
    max_cf: 0.5
  nuclear:
    p_min_pu: 0.6          # Minimum output: 60% of capacity
    p_max_pu: 1.0
    # No max_cf - can run at full capacity
  hydro:
    p_min_pu: 0.2
    p_max_pu: 1.0
  oil:
    p_min_pu: 0.2
    p_max_pu: 1.0
```

**Available Attributes:**

| Attribute | Type | Range | Description |
|-----------|------|-------|-------------|
| `p_min_pu` | float | 0-1 | Minimum output as fraction of capacity (technical minimum) |
| `p_max_pu` | float | 0-1 | Maximum output as fraction of capacity |
| `max_cf` | float | 0-1 | Maximum capacity factor (average over time) |
| `efficiency` | float | 0-1 | Conversion efficiency |
| `marginal_cost` | float | any | Variable cost per MWh |
| `capital_cost` | float | any | Fixed cost per MW of capacity |

**When used:**
1. Applied AFTER carrier standardization via `apply_generator_attributes()`
2. Updates `network.generators.loc[carrier_gens, attr] = value`
3. Applied just before optimization

**Function:** `libs/cost_mapping.py::apply_generator_attributes()`
- Finds all generators with matching carrier
- Sets attribute values for all matching generators
- Applied individually per carrier

**Example:** Coal generators have minimum output of 40% because they take time to ramp down efficiently.

---

### 3. global_constraints

**Purpose:** Sets system-wide generation limits for each carrier.

**Format:**

```yaml
global_constraints:
  gas:
    max_cf: 1.0            # Total gas generation: up to 100% capacity factor
  coal:
    max_cf: 1.0
  nuclear:
    min_cf: 0.0            # No minimum total nuclear generation
```

**Available Constraints:**

| Constraint | Type | Description |
|-----------|------|-------------|
| `min_cf` | float | Minimum capacity factor for carrier (system-wide) |
| `max_cf` | float | Maximum capacity factor for carrier (system-wide) |

**When used:**
- Loaded from config but NOT currently applied in main workflow
- Prepared for future use in optimization constraints

**Note:** Currently defined but not actively used. Can be integrated into PyPSA optimization constraints in future versions.

---

### 4. cc_merge_rules

**Purpose:** Defines how to aggregate attributes when merging combined cycle (CC) generators.

**Background:** Combined cycle plants often consist of multiple generators (gas turbine + steam turbine) that operate as a unit. This section defines how to combine them into a single model generator.

**Format:**

```yaml
cc_merge_rules:
  # Attribute: aggregation rule
  build_year: oldest        # Use earliest year
  capital_cost: largest     # Use highest cost
  p_nom: sum               # Sum all capacities
  others: p_nom            # Default rule for unspecified attributes
  name: cc_group           # Use cc_group value as identifier
```

**Available Rules:**

| Rule | Operation | Use Case |
|------|-----------|----------|
| `oldest` / `smallest` | `min()` | For years, dates, minimum values |
| `newest` / `largest` | `max()` | For years, dates, maximum values |
| `sum` | `sum()` | For capacities, costs to accumulate |
| `mean` | `mean()` | For efficiencies, factors (averages) |
| `p_nom` | Use value from generator with largest capacity | For attributes of the dominant unit |
| `cc_group` | Use the cc_group value itself | For identifier preservation |
| `remove` | Don't include in merged generator | For attributes to skip |

**How it works:**

1. **Identify CC groups:** Generators with same `cc_group` value are candidates for merging
2. **Find dominant generator:** Generator with largest `p_nom` (capacity)
3. **Apply rules per attribute:**
   - For each generator attribute, apply the specified rule
   - Example: `build_year: oldest` means take the earliest build year among all units
4. **Merge:** Create single merged generator with aggregated attributes
5. **Replace:** Remove original generators, add merged generator with name `{cc_group}_CC`

**Example:**

Before merging:
```
GT_Unit1 (gas turbine): p_nom=100 MW, build_year=2010
ST_Unit1 (steam turbine): p_nom=50 MW, build_year=2015
(both have cc_group="Plant_A")
```

With rules: `p_nom: sum`, `build_year: oldest`

After merging:
```
Plant_A_CC: p_nom=150 MW, build_year=2010
```

**When used:**
1. Applied early in workflow via `merge_cc_generators()`
2. Before other data processing and carrier standardization
3. Simplifies the network and reduces computational burden

**Function:** `libs/cc_merger.py::merge_cc_generators()`
- Checks for `cc_group` column in generators
- Groups by cc_group value
- Applies rules and creates merged generator

**Network requirement:** Original network must have a `cc_group` column in generators table. If missing, CC merge is skipped.

---

### 5. generator_region_aggregator_rules

**Purpose:** Defines how to aggregate generators by (carrier, region) combination.

**When needed:** When creating one aggregated generator per carrier per region instead of keeping individual generators.

**Format:**

```yaml
generator_region_aggregator_rules:
  carrier: carrier          # Keep carrier name as-is
  province: region          # Use region value for province attribute
  bus: region              # Connect to regional bus using region name
  control: PQ              # Set to PQ (reactive power control)
  p_nom: sum               # Sum capacities of all units
  efficiency: mean         # Average efficiency
  marginal_cost: mean      # Average marginal cost
  capital_cost: mean       # Average capital cost
  x: mean                  # Average x coordinate (center of region)
  y: mean                  # Average y coordinate (center of region)
  others: ignore           # Default: don't include other attributes
```

**Available Rules:**

| Rule | Operation | Use Case |
|------|-----------|----------|
| `carrier` | Preserve carrier name | For carrier attribute |
| `region` | Use region value | For regional attributes |
| `p_nom` | Use value from largest generator | For capacity-related attributes |
| `oldest` / `smallest` | `min()` | For minimum values |
| `newest` / `largest` | `max()` | For maximum values |
| `sum` | `sum()` | For total capacities |
| `mean` | `mean()` | For averages (efficiency, costs) |
| `remove` / `ignore` | Skip this attribute | For attributes to exclude |
| Fixed value | Any literal value | `PQ` as control type |

**Result Generator Names:**
- Format: `{carrier}_{region}` 
- Example: `gas_경기`, `wind_서울`, `coal_경상도`

**When used:**
- Activated via `regional_aggregation.aggregate_generators_by_carrier: true`
- Called inside `aggregate_network_by_region()` near the end
- Only if region aggregation is enabled

**Function:** `libs/aggregators.py::aggregate_generators_by_carrier_and_region()`

---

### 6. regional_aggregation

**Purpose:** Controls how the network is aggregated by geographical regions.

**When used:** In regional analysis workflows (vs single-node analysis).

**Format:**

```yaml
regional_aggregation:
  # Core settings
  region_column: province              # Column name to aggregate by
  aggregate_generators_by_carrier: true # Create carrier_region generators
  demand_file: data/others/province_demand.xlsx
  province_mapping_file: data/others/province_mapping.csv
  load_carrier: ""                     # Empty = no carrier for loads
  bus_carrier: ""                      # Empty = use original carrier
  
  # Line aggregation rules
  lines:
    grouping: by_voltage              # by_voltage or ignore_voltage
    circuits: sum                     # How to aggregate parallel circuits
    s_nom: scale_by_circuits          # How to aggregate nominal power
    impedance: weighted_by_circuits   # How to aggregate r, x, b
    length: mean                      # How to aggregate length
    remove_self_loops: true           # Remove intra-region lines
  
  # Link aggregation rules  
  links:
    grouping: ignore_voltage
    p_nom: sum
    default_efficiency: 1.0            # 100% efficiency (transmission)
    unlimited_capacity: 1000000        # MW (if p_nom becomes 0)
    length: mean
    remove_self_loops: true
```

#### 6a. Core Regional Settings

| Setting | Type | Description |
|---------|------|-------------|
| `region_column` | string | DataFrame column name to use for aggregation (e.g., "province", "state", "region") |
| `aggregate_generators_by_carrier` | boolean | Create one generator per (carrier, region) combination |
| `demand_file` | string | Path to regional demand data (columns: region_column, demand) |
| `province_mapping_file` | string | Maps official region names to short names |
| `load_carrier` | string | Carrier for loads (empty string = no carrier) |
| `bus_carrier` | string | Carrier for buses (empty string = keep original) |

#### 6b. Line Aggregation Rules

**When grouping by region pairs (Region_A to Region_B), lines are aggregated using these rules:**

**grouping:**
- `by_voltage`: Group by (region0, region1, voltage) - keeps different voltage levels separate
- `ignore_voltage`: Group by (region0, region1) only - combines all voltages

**circuits:**
- `sum`: Sum all parallel circuits (most common)
- `max`: Use maximum circuits
- `mean`: Use average circuits

**s_nom (nominal power):**
- `keep_original`: Use s_nom from one line (tracked via circuits)
- `sum`: Sum all s_nom values
- `max`: Use maximum s_nom
- `scale_by_circuits`: Scale first line's s_nom by total circuits

**impedance (r, x, b):**
- `weighted_by_circuits`: Weighted average by number of circuits (most accurate)
- `mean`: Simple average
- `min`: Use minimum impedance
- `max`: Use maximum impedance

**length:**
- `mean`: Average length
- `max`: Maximum length
- `min`: Minimum length

**remove_self_loops:**
- `true`: Remove lines connecting a region to itself
- `false`: Keep all lines

#### 6c. Link Aggregation Rules

Similar to lines, with adaptations:

**p_nom:**
- `sum`: Sum capacities (most common)
- `max`: Use maximum capacity
- Default: Use first link's value

**default_efficiency:** Float value (1.0 = 100%) for aggregated links

**unlimited_capacity:** If aggregated p_nom becomes 0, use this value (MW) for unlimited capacity

#### Aggregation Algorithm

1. **Load original buses:** Create mapping of each bus → region
2. **Create regional buses:** One bus per unique region (with averaged coordinates)
3. **Map generators:** Update each generator's `bus` to regional bus
4. **Aggregate lines:** Group by (region_pair, voltage), apply aggregation rules
5. **Aggregate links:** Group by (region_pair), apply aggregation rules
6. **Create regional loads:** Distribute total demand by region using demand file
7. **Optionally aggregate generators:** If enabled, create carrier_region generators

**When used:**
Function `libs/region_aggregator.py::aggregate_network_by_region()`

---

### 7. monthly_data

**Purpose:** Specifies path to monthly time-series data file.

**Format:**

```yaml
monthly_data:
  file_path: "data/add/monthly_t.csv"
```

**Data file structure (CSV):**

```
snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
2024-01-01,LNG,generators,generators_t,fuel_cost,50000,TRUE,KR,national
2024-02-01,coal,generators,generators_t,fuel_cost,40000,TRUE,KR,national
...
```

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `snapshot` | datetime | Date/time for this data point (first day of month) |
| `carrier` | string | Original carrier name (before mapping) |
| `components` | string | PyPSA component table (e.g., "generators", "loads") |
| `components_t` | string | Time-series table (e.g., "generators_t", "loads_t") |
| `attribute` | string | Attribute name (e.g., "fuel_cost", "p_max_pu") |
| `value` | float | Value to apply |
| `status` | boolean | TRUE to apply, FALSE to skip |
| `region` | string | Region name (for regional aggregation) |
| `aggregation` | string | Aggregation level: "national" or "province" or "generator" |

**Aggregation levels:**

- `national`: Use value for all generators (matched by region="KR")
- `province`: Use value per province (matched by region=generator's province)
- `generator`: Use value for specific generator (matched by name)

**When used:**
1. Loaded early via `load_monthly_data()`
2. Applied to network via `apply_monthly_data_to_network()`
3. Uses original carrier names (before mapping)
4. Converts monthly values to network's snapshot resolution (forward-fill)

**Function:** `libs/cost_mapping.py::apply_monthly_data_to_network()`

---

### 8. snapshot_data

**Purpose:** Specifies path to snapshot-level (e.g., hourly) time-series data file.

**Format:**

```yaml
snapshot_data:
  file_path: "data/add/snapshot_t.csv"
```

**Data file structure (CSV):**

Same as monthly_data, but with hourly or more frequent snapshots:

```
snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
2024-01-01 00:00,wind,generators,generators_t,p_max_pu,0.8,TRUE,KR,national
2024-01-01 01:00,wind,generators,generators_t,p_max_pu,0.7,TRUE,KR,national
...
```

**Differences from monthly_data:**

- More frequent snapshots (typically hourly)
- No forward-fill of values (exact match to snapshot)
- Applied directly to time-series without aggregation

**When used:**
1. Loaded after monthly data via `load_snapshot_data()`
2. Applied via `apply_snapshot_data_to_network()`
3. Overrides or supplements monthly data

**Function:** `libs/cost_mapping.py::apply_snapshot_data_to_network()`

---

### 9. Base_year

**Purpose:** Specifies the base network data and year to analyze.

**Format:**

```yaml
Base_year:
  year: 2024
  file_path: "data/Singlenode2024"
```

**Settings:**

| Setting | Type | Description |
|---------|------|-------------|
| `year` | integer | Year to analyze (used for output naming) |
| `file_path` | string | Path to PyPSA network CSV folder |

**CSV folder structure:**

PyPSA networks are stored as CSV files. The folder should contain:

```
data/Singlenode2024/
├── buses.csv              # Bus definitions
├── generators.csv         # Generator definitions
├── loads.csv              # Load definitions
├── lines.csv              # Transmission line definitions
├── links.csv              # Link definitions (optional)
├── storage_units.csv      # Storage definitions (optional)
├── stores.csv             # Store definitions (optional)
├── generators_t/          # Time-series data for generators
│   ├── p_set.csv
│   ├── p_max_pu.csv
│   └── ...
├── loads_t/               # Time-series data for loads
│   ├── p_set.csv
│   └── ...
└── ...
```

**When used:**
Function `libs/data_loader.py::load_network()`
- Loads network from CSV folder
- Cleans up empty strings in special columns (e.g., cc_group)

---

### 10. Years

**Purpose:** Lists all modeling years to analyze (for multi-year analysis).

**Format:**

```yaml
Years:
  - 2024
  - 2025
  - 2026
```

**When used:**
- Can be used to loop through multiple years
- Currently defined but not actively used in main workflows
- Available for future multi-year optimization

---

### 11. regional_settings

**Purpose:** General regional configuration parameters.

**Format:**

```yaml
regional_settings:
  national_region: "KR"    # Name of national/whole-system region
```

**Settings:**

| Setting | Type | Description |
|---------|------|-------------|
| `national_region` | string | Name of the region representing the whole system (e.g., "KR" for Korea) |

**Used in:**
- Monthly/snapshot data matching for "national" aggregation level
- As default region name when no regional aggregation applies

---

## Workflow and Execution Order

### Single-Node Workflow (main_singlenode.py)

```
1. Load Configuration
   └─ config = load_config("config/config_single.yaml")

2. Load Base Network
   └─ network = load_network(config)
   └─ All components reference single "KR" bus

3. Merge CC Generators
   └─ network = merge_cc_generators(network, config)
   └─ Uses: cc_merge_rules
   └─ Creates: {cc_group}_CC generators

4. Load and Apply Monthly Data
   └─ monthly_df = load_monthly_data(config)
   └─ network = apply_monthly_data_to_network(network, config, monthly_df)
   └─ Uses: original carrier names from data

5. Load and Apply Snapshot Data
   └─ snapshot_df = load_snapshot_data(config)
   └─ network = apply_snapshot_data_to_network(network, config, snapshot_df)
   └─ Uses: original carrier names from data

6. Standardize Carrier Names (FINAL STEP)
   └─ network = standardize_carrier_names(network, carrier_mapping)
   └─ Applies: carrier_mapping
   └─ Updates: All components, network.carriers table

7. Apply Generator Attributes
   └─ network = apply_generator_attributes(network, generator_attributes)
   └─ Applies: generator_attributes per carrier

8. Run Optimization
   └─ network.optimize(snapshots=optimization_snapshots)
   └─ All data is now standardized and ready
```

### Regional Workflow (main_region.py)

```
1. Load Configuration
   └─ config = load_config("config/config_province.yaml")

2. Load Base Network
   └─ network = load_network(config)
   └─ Network has multiple buses per province

3. Merge CC Generators
   └─ network = merge_cc_generators(network, config)
   └─ Uses: cc_merge_rules

4. Load and Apply Monthly Data
   └─ monthly_df = load_monthly_data(config)
   └─ network = apply_monthly_data_to_network(network, config, monthly_df)
   └─ Uses: original carrier names from data

5. Load and Apply Snapshot Data
   └─ snapshot_df = load_snapshot_data(config)
   └─ network = apply_snapshot_data_to_network(network, config, snapshot_df)
   └─ Uses: original carrier names from data

6. Aggregate Network by Region
   └─ network = aggregate_network_by_region(network, config)
   └─ Uses: regional_aggregation settings
   ├─ 6a. Clean duplicate columns
   ├─ 6b. Create bus→region mapping
   ├─ 6c. Create regional buses (one per region)
   ├─ 6d. Map generators to regional buses
   ├─ 6e. Aggregate lines by region pairs
   ├─ 6f. Aggregate links by region pairs
   ├─ 6g. Optionally aggregate generators by carrier+region
   │   └─ Uses: generator_region_aggregator_rules
   └─ 6h. Create regional loads from demand file

7. Standardize Carrier Names (FINAL STEP)
   └─ network = standardize_carrier_names(network, carrier_mapping)
   └─ Applies: carrier_mapping
   └─ Updates: All components, network.carriers table

8. Run Optimization
   └─ network.optimize(snapshots=optimization_snapshots)
   └─ All data is now standardized and regional
```

---

## Data Flow

### Carrier Name Flow

```
Data Files (original names)
         ↓
    Load Data
         ↓
    Apply to Network (original carrier names)
         ↓
    CC Merge (uses original names)
         ↓
    Monthly/Snapshot Data (uses original names)
         ↓
    Regional Aggregation (uses original names)
         ↓
    STANDARDIZE CARRIER NAMES (final step)
         ↓
    Apply Generator Attributes (uses new names)
         ↓
    Optimization (standardized names)
```

**Why this order?**
- Data files use original carrier names
- Keeping original names during data loading ensures accurate matching
- Standardizing at the end creates a clean, consistent network for optimization
- Generator attributes applied after standardization use consistent names

### Generator Attribute Application Flow

```
Network with Carriers
         ↓
Standardize Names (apply carrier_mapping)
         ↓
Apply Generator Attributes per Carrier
    ├─ gas generators → p_min_pu=0.2, p_max_pu=1.0, max_cf=0.5
    ├─ coal generators → p_min_pu=0.4, p_max_pu=1.0, max_cf=0.5
    ├─ nuclear generators → p_min_pu=0.6, p_max_pu=1.0
    └─ hydro generators → p_min_pu=0.2, p_max_pu=1.0
         ↓
Network Ready for Optimization
```

---

## Examples

### Example 1: Single-Node Analysis with CC Merging

**Scenario:** Model Korea's energy system as single node with combined cycle generator merging.

**Config (config_single.yaml):**

```yaml
carrier_mapping:
  bituminous: coal
  anthracite: coal
  LNG: gas

generator_attributes:
  coal:
    p_min_pu: 0.4
    p_max_pu: 1.0
  gas:
    p_min_pu: 0.2
    p_max_pu: 1.0

cc_merge_rules:
  p_nom: sum
  build_year: oldest
  others: p_nom

monthly_data:
  file_path: "data/add/monthly_t.csv"

snapshot_data:
  file_path: "data/add/snapshot_t.csv"

Base_year:
  year: 2024
  file_path: "data/Singlenode2024"

regional_settings:
  national_region: "KR"
```

**Execution:**

```bash
python main_singlenode.py
```

**Results:**
- Single network with one "KR" bus
- All coal types mapped to "coal" carrier
- CC generators merged into unified units
- Monthly data applied with original names, then standardized
- Ready for 48-hour optimization

### Example 2: Regional Analysis with Generator Aggregation

**Scenario:** Model Korea by province with carriers aggregated per region.

**Config (config_province.yaml):**

```yaml
carrier_mapping:
  bituminous: coal
  anthracite: coal
  LNG: gas

generator_attributes:
  coal:
    p_min_pu: 0.4
    p_max_pu: 1.0
  gas:
    p_min_pu: 0.2
    p_max_pu: 1.0

generator_region_aggregator_rules:
  carrier: carrier
  province: region
  bus: region
  p_nom: sum
  marginal_cost: mean
  others: ignore

regional_aggregation:
  region_column: province
  aggregate_generators_by_carrier: true
  demand_file: data/others/province_demand.xlsx
  province_mapping_file: data/others/province_mapping.csv
  lines:
    grouping: by_voltage
    circuits: sum
    s_nom: scale_by_circuits
    impedance: weighted_by_circuits
    remove_self_loops: true

Base_year:
  year: 2024
  file_path: "data/Provincenode2024"
```

**Execution:**

```bash
python main_region.py
```

**Results:**
- 16 regional buses (one per province)
- Lines aggregated between provinces
- Generators aggregated: {carrier}_{province} format
  - Example: "coal_경기", "gas_서울", "wind_강원"
- Regional loads distributed by province demand
- Ready for regional optimization

### Example 3: Advanced Regional Analysis with Custom Rules

**Scenario:** Model with strict wind/solar restrictions, detailed line impedance handling.

**Config excerpt:**

```yaml
generator_attributes:
  wind:
    p_min_pu: 0.0           # No minimum
    p_max_pu: 1.0
    max_cf: 0.35            # Capacity factor limit
  solar:
    p_min_pu: 0.0
    p_max_pu: 1.0
    max_cf: 0.25            # Lower capacity factor
  coal:
    p_min_pu: 0.4           # High minimum
    p_max_pu: 1.0

regional_aggregation:
  lines:
    grouping: ignore_voltage    # Combine all voltages
    circuits: max              # Use maximum circuits
    s_nom: sum                 # Sum all power ratings
    impedance: weighted_by_circuits  # Most accurate aggregation
    length: max                # Use longest distance
    remove_self_loops: false   # Keep all lines

  links:
    grouping: ignore_voltage
    p_nom: sum
    default_efficiency: 0.97   # 97% transmission efficiency
```

**Rationale:**
- Wind/solar have stricter capacity factor limits due to intermittency
- Coal has high minimum output due to thermal inertia
- Lines: ignore voltage to simplify, use weighted impedance for accuracy
- Links: slightly less than perfect efficiency to account for transmission losses

---

## Configuration Best Practices

1. **Carrier Mapping:**
   - Map all similar fuel types to one carrier (e.g., all coal types → "coal")
   - Use descriptive names (gas, coal, wind, solar, hydro)
   - Test with small network to verify mapping is correct

2. **Generator Attributes:**
   - p_min_pu should reflect technical minimum (0-1)
   - max_cf should be <= 1.0
   - Use consistent values across similar technologies

3. **CC Merge Rules:**
   - Always include `p_nom: sum` to combine capacities
   - Use `oldest` for build_year (representative age)
   - Use `mean` for efficiency values
   - Use `p_nom` rule for attributes from dominant unit

4. **Regional Aggregation:**
   - Test region_column exists in all relevant tables
   - Verify demand_file has correct region names
   - Use `by_voltage` grouping for detailed analysis
   - Use `weighted_by_circuits` for impedance (most accurate)

5. **Data Files:**
   - Ensure monthly/snapshot data uses original carrier names
   - Verify status column is TRUE for data to apply
   - Check aggregation level matches region column
   - Test data file paths before running full analysis

---

## Debugging Guide

### Issue: Carrier not found after standardization

**Cause:** Carrier in data file not in carrier_mapping

**Solution:**
1. Check data file carrier names
2. Add missing mappings to carrier_mapping
3. Verify spelling and case sensitivity

### Issue: Generators not receiving attributes

**Cause:** Generator carrier doesn't match generator_attributes keys

**Solution:**
1. Print standardized carrier names: `print(network.generators.carrier.unique())`
2. Ensure generator_attributes has matching keys
3. Check carrier standardization applied correctly

### Issue: Regional aggregation fails

**Cause:** region_column not in network components

**Solution:**
1. Verify region_column exists in generators, buses, loads
2. Check CSV files have province/region data
3. Ensure no NaN values in region column

### Issue: CC merge not working

**Cause:** No cc_group column or column is empty

**Solution:**
1. Check CSV has cc_group column
2. Verify cc_group values are not empty strings
3. Load network checks for this: `network.generators['cc_group'].replace('', pd.NA)`

---

## Summary Table: Configuration Sections

| Section | Purpose | When Used | Key Options |
|---------|---------|-----------|------------|
| `carrier_mapping` | Map carrier names | Final step before optimization | Dictionary of old→new names |
| `generator_attributes` | Set generator limits per carrier | After carrier standardization | p_min_pu, p_max_pu, max_cf, etc. |
| `global_constraints` | System-wide limits | Prepared but not actively used | min_cf, max_cf per carrier |
| `cc_merge_rules` | Merge multi-unit generators | Early in workflow | oldest, newest, sum, mean, p_nom |
| `generator_region_aggregator_rules` | Aggregate generators by region | Regional workflows | carrier, region, sum, mean, ignore |
| `regional_aggregation` | Group by geography | Regional workflows | region_column, lines, links rules |
| `monthly_data` | Monthly time-series file path | Data loading | file_path |
| `snapshot_data` | Hourly time-series file path | Data loading | file_path |
| `Base_year` | Network data location | Network loading | year, file_path |
| `Years` | Multi-year analysis | Multi-year workflows | List of years |
| `regional_settings` | Regional parameters | Throughout workflow | national_region |

