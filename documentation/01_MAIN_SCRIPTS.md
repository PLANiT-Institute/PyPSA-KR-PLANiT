# Main Scripts Documentation

This document provides comprehensive documentation for the three main entry point scripts in the PyPSA Alternative project.

## Table of Contents

1. [Overview](#overview)
2. [main_singlenode.py](#main_singlenodepy)
3. [main_province.py](#main_provincepy)
4. [main_group.py](#main_grouppy)
5. [Common Execution Flow](#common-execution-flow)

---

## Overview

The PyPSA Alternative project provides three different aggregation levels for network analysis:

| Script | Aggregation Level | Description | Use Case |
|--------|------------------|-------------|----------|
| `main_singlenode.py` | Single node | All components connected to one 'KR' bus | National-level analysis, fastest computation |
| `main_province.py` | Provincial | 17 provincial buses with inter-provincial transmission | Regional-level analysis, moderate detail |
| `main_group.py` | Regional groups | 2-3 group buses (e.g., mainland, islands) | Group-level analysis, highest aggregation |

All three scripts follow a similar execution flow but differ in their aggregation settings.

---

## main_singlenode.py

### Purpose

Runs a single-node network analysis where all generators, loads, and storage units are connected to a single bus representing the entire country (Korea).

### Configuration File

```python
config_path = 'config/config_single.xlsx'
```

### Network Structure

- **Buses**: Single bus named 'KR' (created if doesn't exist)
- **Generators**: All generators connected to 'KR' bus
- **Loads**: All loads aggregated at 'KR' bus
- **Lines/Links**: No transmission constraints (single node)

### Execution Flow

1. **Load Configuration** (`libs.config.load_config`)
   - Reads Excel configuration file
   - Loads all settings: carrier mappings, generator attributes, file paths, etc.

2. **Load Network** (`libs.data_loader.load_network`)
   - Imports PyPSA network from CSV folder
   - Converts snapshots to DatetimeIndex with day-first format
   - Creates 'KR' bus if it doesn't exist

3. **Merge Combined Cycle Generators** (`libs.cc_merger.merge_cc_generators`)
   - Aggregates generators marked with `cc_group` column
   - Applies aggregation rules from config (sum capacity, mean efficiency, etc.)

4. **Load and Apply Monthly Data** (`libs.data_loader.load_monthly_data` + `libs.temporal_data.apply_monthly_data_to_network`)
   - Loads time-series data that varies by month (e.g., fuel costs)
   - Matches data by carrier, region, and aggregation level
   - Applies to network components (generators_t.marginal_cost, etc.)

5. **Load and Apply Snapshot Data** (`libs.data_loader.load_snapshot_data` + `libs.temporal_data.apply_snapshot_data_to_network`)
   - Loads hourly/sub-hourly time-series data
   - Matches data by carrier and applies to network components

6. **Copy Fuel Cost to Marginal Cost**
   ```python
   network.generators_t.marginal_cost = network.generators_t.fuel_cost
   ```
   - Sets marginal cost equal to fuel cost for all generators

7. **Standardize Carrier Names** (`libs.carrier_standardization.standardize_carrier_names`)
   - Maps original carrier names to standardized names from config
   - Updates all components and the carriers table
   - Example: 'LNG복합' → 'gas', '석탄화력' → 'coal'

8. **Set Generator Dispatch Profile** (`libs.generator_p_set.set_generator_p_set`)
   - For solar and wind: creates fixed dispatch profile `p_set = p_nom × p_max_pu`
   - Makes these generators must-run (not optimizable)

9. **Apply Generator Attributes** (`libs.component_attributes.apply_generator_attributes`)
   - Sets carrier-specific operational parameters
   - Example: `p_min_pu`, `p_max_pu`, `ramp_limit_up`, etc.
   - Uses 'default' values for all carriers, then overrides with carrier-specific values

10. **Apply Storage Unit Attributes** (`libs.component_attributes.apply_storage_unit_attributes`)
    - Sets storage-specific parameters
    - Example: `efficiency_store`, `efficiency_dispatch`, `max_hours`

11. **Define Optimization Snapshots**
    ```python
    optimization_snapshots = network.snapshots[:48]  # First 48 hours
    ```

12. **Apply Capacity Factor Energy Constraints** (`libs.energy_constraints.apply_cf_energy_constraints`)
    - Converts `max_cf` and `min_cf` into energy bounds
    - Formula: `e_sum_max = p_nom × max_cf × total_hours`

13. **Run Optimization**
    ```python
    status = network.optimize(snapshots=optimization_snapshots)
    ```
    - Solves linear optimization problem
    - Minimizes total system cost subject to constraints

14. **Visualize Results** (if optimization succeeded)
    - Creates interactive generation by carrier stacked area chart
    - Uses `libs.visualization.plot_generation_by_carrier`
    - Includes storage units (discharge = positive, charge = negative)

### Key Features

- **Simplest aggregation**: No spatial constraints
- **Fastest computation**: No transmission network
- **National-level insights**: Total generation mix and costs

### Example Output

After successful optimization:
- Generation by carrier chart showing hourly dispatch
- Total system cost
- Carrier-specific generation totals

---

## main_province.py

### Purpose

Aggregates the network to provincial level (17 provinces in Korea), with transmission lines connecting provinces.

### Configuration File

```python
config_path = 'config/config_province.xlsx'
```

### Network Structure After Aggregation

- **Buses**: One bus per province (17 total)
  - Named using short province names (e.g., '강원', '경기')
- **Generators**: Mapped to provincial buses based on their `province` column
- **Loads**: Distributed to provinces based on regional demand shares
- **Lines**: Aggregated between province pairs using configured rules

### Execution Flow

Follows the same flow as `main_singlenode.py` with one critical addition:

**Regional Aggregation** (inserted after step 6, before standardization):

```python
network = aggregate_network_by_region(network, config)
```

This step (`libs.region_aggregator.aggregate_network_by_region`):

1. **Creates Bus-to-Region Mapping**
   - Maps original buses to provincial buses using `province` column
   - Standardizes province names using mapping (official → short)

2. **Updates Component References**
   - Generators: Maps `bus` to provincial bus
   - Loads: Distributes to provincial buses based on demand shares
   - Lines: Updates `bus0` and `bus1` to provincial buses
   - Links: Updates `bus0` and `bus1` to provincial buses

3. **Aggregates Lines**
   - Groups lines by voltage level (or ignores voltage if configured)
   - Aggregates circuits, s_nom, impedances based on rules:
     - `circuits_rule`: 'sum', 'max', or 'mean'
     - `s_nom_rule`: 'sum', 'max', 'scale_by_circuits', etc.
     - `impedance_rule`: 'weighted_by_circuits', 'mean', etc.
   - Removes self-loops if `remove_self_loops=TRUE`

4. **Aggregates Links** (if present)
   - Similar to lines, using `links_config` rules

5. **Optionally Aggregates Generators by Carrier**
   - If `aggregate_generators_by_carrier=TRUE`
   - Creates one generator per (carrier, province) combination
   - Example: 'gas_강원', 'solar_경기', etc.

6. **Creates Provincial Buses**
   - One bus per province with standardized short name

### Configuration Settings

From `config/config_province.xlsx`:

**province_aggregation sheet:**
```
region_column: province
aggregate_generators_by_carrier: TRUE/FALSE
demand_file: path/to/regional_demand.csv
province_mapping_file: path/to/province_mapping.csv
```

**lines_config sheet:**
```
grouping: by_voltage / ignore_voltage
circuits_rule: sum / max / mean
s_nom_rule: sum / max / scale_by_circuits
impedance_rule: weighted_by_circuits / mean / min / max
length_rule: mean / max / min
remove_self_loops: TRUE / FALSE
```

### Key Features

- **Provincial resolution**: Captures inter-regional transmission constraints
- **Moderate detail**: Balance between computation time and spatial accuracy
- **Transmission analysis**: Can analyze inter-provincial power flows

---

## main_group.py

### Purpose

Provides two-level aggregation: first to provinces (17 regions), then optionally to higher-level groups (e.g., 2-3 groups like mainland vs. islands).

### Configuration File

```python
config_path = 'config/config_group.xlsx'
```

### Two-Level Aggregation

#### Level 1: Provincial Aggregation (17 provinces)
Same as `main_province.py`

#### Level 2: Group Aggregation (optional, 2-3 groups)
If `aggregate_regions_by_group=TRUE`:

1. **Groups Provincial Buses**
   - Uses `group1` or `group2` column from `province_mapping` sheet
   - Example groups:
     - group1: '육지' (mainland), '제주' (Jeju island)
     - group2: '수도권' (metropolitan), '육지' (mainland), '제주' (island)

2. **Aggregates to Group Level**
   - Provincial buses → Group buses
   - Generators remapped to group buses
   - Lines/links aggregated by group pairs
   - Loads summed within each group

### Execution Flow

Same as `main_province.py`, but the regional aggregation step supports group-level aggregation:

```python
network = aggregate_network_by_region(network, config)
```

The `aggregate_network_by_region` function checks:
```python
if config['regional_aggregation']['aggregate_regions_by_group'] == True:
    # Perform second-level aggregation to groups
    region_groups = config['regional_aggregation']['region_groups']  # e.g., 'group1'
```

### Additional Features

#### Modelling Settings

From `modelling_setting` sheet in config:

```python
year: 2024                    # Modeling year
weights: 4                    # Temporal aggregation (4-hour snapshots)
snapshot_start: '01/01/2024'  # Start date (day-first format)
snapshot_end: 168             # Number of snapshots (e.g., 1 week)
```

These settings enable:

1. **Snapshot Limiting** (`libs.resample.limit_snapshots`)
   - Selects specific date range
   - Reduces computation time for testing

2. **Temporal Resampling** (`libs.resample.resample_network`)
   - Aggregates snapshots (e.g., 1-hour → 4-hour)
   - Applies resampling rules from `resample_rules` sheet
   - Scales attributes like `ramp_limit_up` by weights

### Visualization Enhancements

After optimization, `main_group.py` provides additional visualizations:

1. **Generation by Carrier Chart**
   ```python
   fig = plot_generation_by_carrier(network, ...)
   ```

2. **Link and Line Flow Chart**
   ```python
   flow_fig = plot_link_and_line_flows(network, ...)
   ```

3. **Detailed Flow Analysis**
   ```python
   print_link_and_line_flow_analysis(network, ...)
   ```
   - Prints flow statistics for each line/link
   - Shows capacity, utilization, direction of flows

### Key Features

- **Multi-level aggregation**: Flexible grouping (provincial or group level)
- **Temporal control**: Adjust time resolution and range
- **Enhanced visualization**: Transmission flow analysis
- **Most configurable**: Supports complex aggregation scenarios

---

## Common Execution Flow

All three scripts follow this general pattern:

```
┌─────────────────────────────────────┐
│  1. Load Configuration              │
│     (from Excel file)               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  2. Load Network                    │
│     (from CSV folder)               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  3. Merge Combined Cycle Generators │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  4. Apply Monthly Data              │
│     (monthly fuel costs, etc.)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  5. Apply Snapshot Data             │
│     (hourly capacity factors, etc.) │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  6. Set Marginal Cost = Fuel Cost   │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │ OPTIONAL  │
         │ Regional  │  ← Only in main_province.py
         │ Aggreg.   │    and main_group.py
         └─────┬─────┘
               │
┌──────────────▼──────────────────────┐
│  7. Standardize Carrier Names       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  8. Set Generator p_set             │
│     (for solar/wind)                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  9. Apply Generator Attributes      │
│     (p_min_pu, ramp limits, etc.)   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 10. Apply Storage Attributes        │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │ OPTIONAL  │
         │ Snapshot  │  ← Only in main_group.py
         │ Limiting  │
         └─────┬─────┘
               │
┌──────────────▼──────────────────────┐
│ 11. Apply Energy Constraints        │
│     (from capacity factors)         │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │ OPTIONAL  │
         │ Temporal  │  ← Only in main_group.py
         │ Resample  │
         └─────┬─────┘
               │
┌──────────────▼──────────────────────┐
│ 12. Run Optimization                │
│     network.optimize()              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 13. Visualize Results               │
│     (if optimization succeeded)     │
└─────────────────────────────────────┘
```

### Key Differences Between Scripts

| Feature | main_singlenode.py | main_province.py | main_group.py |
|---------|-------------------|------------------|---------------|
| Regional aggregation | ❌ No | ✅ Yes (provincial) | ✅ Yes (provincial + groups) |
| Snapshot limiting | ❌ No | ❌ No | ✅ Yes (configurable) |
| Temporal resampling | ❌ No | ❌ No | ✅ Yes (configurable) |
| Transmission analysis | ❌ No | ✅ Yes | ✅ Yes (enhanced) |
| Modeling year from config | ❌ Hardcoded (2024) | ❌ Hardcoded (2024) | ✅ From config |
| Optimization snapshots | First 48 hours | First 48 hours | Configurable range |

---

## Best Practices

### When to Use Each Script

1. **Use main_singlenode.py when:**
   - Performing quick national-level analysis
   - Testing configurations
   - No transmission constraints needed
   - Focus on generation mix and costs

2. **Use main_province.py when:**
   - Need provincial-level detail
   - Analyzing inter-regional transmission
   - Moderate computation time acceptable
   - Testing regional policies

3. **Use main_group.py when:**
   - Need flexible aggregation levels
   - Analyzing island vs. mainland scenarios
   - Testing different time resolutions
   - Production runs with full control

### Configuration Tips

- Always run `main_singlenode.py` first to validate data
- Use temporal resampling (weights > 1) to speed up testing
- Enable snapshot limiting for development/debugging
- Use `aggregate_generators_by_carrier=TRUE` to reduce network size
- Check line aggregation rules carefully (affects transmission capacity)

### Debugging

If optimization fails:
1. Check generator marginal costs (must be positive)
2. Verify load data exists for all snapshots
3. Check transmission capacities (not too restrictive)
4. Review energy constraints (e_sum_max/min reasonable)
5. Ensure generator p_nom > 0 for all generators

---

## Related Documentation

- [Library Modules Documentation](02_LIBRARY_MODULES.md)
- [Process Flow Documentation](03_PROCESS_FLOW.md)
- [Configuration Guide](04_CONFIGURATION_GUIDE.md)
