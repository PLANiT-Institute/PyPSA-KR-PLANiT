# Configuration Guide

This document provides a comprehensive guide to configuring the PyPSA Alternative project through Excel configuration files.

## Table of Contents

1. [Configuration File Overview](#configuration-file-overview)
2. [Common Configuration Sheets](#common-configuration-sheets)
3. [Regional Aggregation Configuration](#regional-aggregation-configuration)
4. [Temporal Configuration](#temporal-configuration)
5. [Configuration Examples](#configuration-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Configuration File Overview

The PyPSA Alternative project uses Excel files (`.xlsx`) for configuration. Each aggregation level has its own configuration file:

| File | Used By | Purpose |
|------|---------|---------|
| `config/config_single.xlsx` | main_singlenode.py | Single-node analysis |
| `config/config_province.xlsx` | main_province.py | Provincial analysis |
| `config/config_group.xlsx` | main_group.py | Group-level analysis |

### Excel Sheet Structure

Each configuration file contains multiple sheets (tabs), each serving a specific purpose. Required sheets are marked with *, optional sheets with †.

---

## Common Configuration Sheets

These sheets appear in all three configuration files.

### 1. carrier_mapping* (Required)

**Purpose:** Map original carrier names to standardized names

**Columns:**
- `original_carrier` (str): Original name from data files (usually Korean)
- `mapped_carrier` (str): Standardized name for analysis (usually English)

**Example:**
```
original_carrier    mapped_carrier
LNG복합            gas
석탄화력            coal
원자력              nuclear
태양광              solar
풍력                wind
수력                hydro
ESS                battery
양수                PSH
```

**Notes:**
- Standardization happens AFTER data loading
- Use English names for better tool compatibility
- Keep names short and lowercase for consistency

---

### 2. generator_attributes* (Required)

**Purpose:** Define operational parameters for generators by carrier type

**Columns:**
- `carrier` (or `carriers`) (str): Carrier name (after mapping)
- `p_min_pu` (float): Minimum output fraction (0.0-1.0)
- `p_max_pu` (float): Maximum output fraction (static, 0.0-1.0)
- `ramp_limit_up` (float): Ramp-up rate (MW/hour)
- `ramp_limit_down` (float): Ramp-down rate (MW/hour)
- `max_cf` (float): Maximum capacity factor for energy constraints
- `min_cf` (float): Minimum capacity factor for energy constraints
- `efficiency` (float): Conversion efficiency (0.0-1.0)
- `marginal_cost` (float): Operating cost (€/MWh or ₩/MWh)

**Special Carrier:**
- `default`: Applied to ALL generators, then overridden by carrier-specific values

**Example:**
```
carrier     p_min_pu  p_max_pu  ramp_limit_up  ramp_limit_down  max_cf  min_cf  efficiency
default     0.0       1.0       100            100
gas         0.2       1.0       150            150                              0.55
coal        0.4       1.0       80             80                               0.40
nuclear     0.8       1.0       50             50               0.95    0.80    0.33
hydro       0.0       1.0       200            200
solar       0.0       1.0                                                       1.0
wind        0.0       1.0                                                       1.0
battery     0.0       1.0
```

**Notes:**
- Leave cells blank for attributes that don't apply
- `p_max_pu` here is static; time-varying values come from snapshot_data
- `max_cf`/`min_cf` converted to energy constraints (e_sum_max/min)
- Ramp limits in MW/hour (scaled automatically if resampling)

---

### 3. storage_unit_attributes† (Optional)

**Purpose:** Define parameters for storage units (batteries, pumped hydro)

**Columns:**
- `carrier` (str): Carrier name
- `efficiency_store` (float): Charging efficiency (0.0-1.0)
- `efficiency_dispatch` (float): Discharging efficiency (0.0-1.0)
- `max_hours` (float): Maximum storage duration (hours)
- `standing_loss` (float): Self-discharge rate per hour
- `p_min_pu` (float): Minimum charge/discharge rate
- `p_max_pu` (float): Maximum charge/discharge rate

**Example:**
```
carrier    efficiency_store  efficiency_dispatch  max_hours  standing_loss
default    0.95              0.95
battery    0.90              0.90                 4          0.001
PSH        0.85              0.90                 8          0.0001
```

**Notes:**
- Round-trip efficiency = efficiency_store × efficiency_dispatch
- `max_hours` determines energy capacity: `e_nom = p_nom × max_hours`
- `standing_loss` as fraction per hour (0.001 = 0.1% per hour)

---

### 4. global_constraints† (Optional)

**Purpose:** System-wide constraints (not currently used in main scripts)

**Columns:**
- `carrier` (str): Carrier name
- `min_cf` (float): Minimum system-wide capacity factor
- `max_cf` (float): Maximum system-wide capacity factor

---

### 5. file_paths* (Required)

**Purpose:** Specify locations of data files

**Columns:**
- `setting` (str): Setting name
- `value` (str): File path or value

**Settings:**
```
setting                 value
monthly_data_file       data/monthly_costs.csv
snapshot_data_file      data/hourly_data.csv
base_year               2024
base_file_path          data/2024
```

**Notes:**
- `base_file_path`: Folder containing network CSV files (buses, generators, etc.)
- `base_year`: Year of base network data
- Paths relative to project root

---

### 6. regional_settings* (Required)

**Purpose:** Basic regional configuration

**Columns:**
- `setting` (str): Setting name
- `value` (str): Setting value

**Settings:**
```
setting           value
national_region   KR
```

**Notes:**
- `national_region`: Region name for national-level data matching

---

### 7. cc_merge_rules* (Required)

**Purpose:** Define how to aggregate combined cycle generator attributes

**Columns:**
- `attribute` (str): Generator attribute name
- `rule` (str): Aggregation rule

**Rules:**
- `sum`: Add values (e.g., total capacity)
- `mean`: Average values (e.g., average efficiency)
- `oldest` / `smallest`: Minimum value
- `newest` / `largest`: Maximum value
- `p_nom`: Use value from generator with largest p_nom
- `cc_group`: Use the cc_group value
- `others`: Default rule for unspecified attributes

**Example:**
```
attribute        rule
p_nom            sum
efficiency       mean
build_year       oldest
marginal_cost    mean
carrier          carrier
cc_group         cc_group
bus              p_nom
others           p_nom
```

**Notes:**
- Only applies to generators with `cc_group` column
- `others` is the fallback for any attribute not listed

---

### 8. years* (Required)

**Purpose:** List of modeling years

**Columns:**
- `year` (int): Year

**Example:**
```
year
2024
2030
2040
2050
```

**Notes:**
- Currently only the first year is used
- Future: Support multi-year analysis

---

### 9. carrier_order* (Required)

**Purpose:** Define display order for visualization

**Columns:**
- `carriers` (str): Carrier name

**Example:**
```
carriers
nuclear
coal
gas
hydro
PSH
battery
solar
wind
```

**Notes:**
- **First carrier appears at BOTTOM** of stacked chart (baseload)
- **Last carrier appears at TOP** (variable/peaking)
- Order represents typical dispatch hierarchy
- Carriers not in list appear at the end

---

## Regional Aggregation Configuration

These sheets control spatial aggregation (only in config_province.xlsx and config_group.xlsx).

### 10. regional_aggregation* (Required for province/group)

**Purpose:** Main regional aggregation settings

**Columns:**
- `setting` (str): Setting name
- `value` (str or bool): Setting value

**Settings:**
```
setting                        value
aggregate_by_region            TRUE
aggregate_by_carrier           TRUE
aggregate_regions_by_group     FALSE
region_column                  province
region_groups                  group1
demand_file                    data/regional_demand.csv
province_mapping_file          data/province_mapping.csv
```

**Setting Descriptions:**

| Setting | Type | Description |
|---------|------|-------------|
| `aggregate_by_region` | bool | Enable regional aggregation |
| `aggregate_by_carrier` | bool | Merge generators by (carrier, region) |
| `aggregate_regions_by_group` | bool | Second-level group aggregation |
| `region_column` | str | Column name to aggregate by (default: 'province') |
| `region_groups` | str | Group column for second-level ('group1' or 'group2') |
| `demand_file` | str | Path to regional demand shares |
| `province_mapping_file` | str | Path to province name mapping |

**Notes:**
- Set booleans as `TRUE` or `FALSE` (case-insensitive)
- `aggregate_regions_by_group` only works if `aggregate_by_region` is TRUE

---

### 11. generator_region_agg_rules† (Optional)

**Purpose:** Define how to aggregate generator static attributes by region

**Columns:**
- `attribute` (str): Generator attribute name
- `rule` (str): Aggregation rule

**Rules:**
- `sum`: Add values
- `mean`: Average values
- `oldest` / `smallest`: Minimum
- `newest` / `largest`: Maximum
- `p_nom`: From generator with largest p_nom
- `carrier`: Use carrier value
- `region`: Use region value
- `remove` / `ignore`: Remove this attribute
- `others`: Default rule

**Example:**
```
attribute        rule
p_nom            sum
efficiency       mean
build_year       oldest
marginal_cost    mean
carrier          carrier
province         region
bus              region
cc_group         remove
others           p_nom
```

**Notes:**
- Only used if `aggregate_by_carrier=TRUE`
- `bus` should use `region` rule to connect to regional bus

---

### 12. generator_t_aggregator_rules† (Optional)

**Purpose:** Define how to aggregate generator time-series by region

**Columns:**
- `attribute` (str): Time-series attribute name
- `rule` (str): Aggregation rule

**Rules:**
- `sum`: Add time-series
- `mean`: Average time-series
- `max`: Maximum across generators
- `min`: Minimum across generators

**Example:**
```
attribute        rule
p_max_pu         mean
marginal_cost    mean
fuel_cost        mean
others           mean
```

**Notes:**
- Applied to generators_t.* attributes
- `others` is the default for unlisted attributes

---

### 13. lines_config* (Required for province/group)

**Purpose:** Configure transmission line aggregation

**Columns:**
- `setting` (str): Setting name
- `value` (str or bool): Setting value

**Settings:**
```
setting           value
grouping          by_voltage
circuits_rule     sum
s_nom_rule        sum
impedance_rule    weighted_by_circuits
length_rule       mean
remove_self_loops TRUE
```

**Setting Descriptions:**

| Setting | Options | Description |
|---------|---------|-------------|
| `grouping` | `by_voltage`, `ignore_voltage` | Group lines by voltage level or combine all |
| `circuits_rule` | `sum`, `max`, `mean` | How to aggregate circuit count |
| `s_nom_rule` | `sum`, `max`, `scale_by_circuits`, `keep_original` | How to aggregate capacity |
| `impedance_rule` | `weighted_by_circuits`, `mean`, `min`, `max` | How to aggregate impedance (r, x, b) |
| `length_rule` | `mean`, `max`, `min` | How to aggregate line length |
| `remove_self_loops` | `TRUE`, `FALSE` | Remove intra-regional lines |

**Grouping Examples:**

**by_voltage:**
```
Before:
강원-경기-345kV (2 circuits)
강원-경기-765kV (1 circuit)

After:
강원-경기-345kV (aggregated 345kV lines)
강원-경기-765kV (aggregated 765kV lines)
```

**ignore_voltage:**
```
Before:
강원-경기-345kV (2 circuits)
강원-경기-765kV (1 circuit)

After:
강원-경기 (single aggregated line)
```

**s_nom Rules:**

- `sum`: Total capacity (parallel lines add)
- `max`: Largest line capacity
- `scale_by_circuits`: Capacity scaled by circuit ratio
- `keep_original`: Use first line's capacity

**Impedance Rule Example:**

`weighted_by_circuits`:
```python
# Line 1: r=0.05, circuits=2
# Line 2: r=0.06, circuits=1
# Aggregated: r = (0.05×2 + 0.06×1) / (2+1) = 0.053
```

---

### 14. links_config† (Optional)

**Purpose:** Configure HVDC link aggregation (same structure as lines_config)

**Settings:**
```
setting           value
grouping          ignore_voltage
p_nom_rule        sum
efficiency_rule   mean
remove_self_loops TRUE
```

**Notes:**
- Only needed if network has links (HVDC connections)
- Similar rules to lines_config

---

### 15. province_mapping* (Required for province/group)

**Purpose:** Map province names and define groups

**Columns:**
- `short` (str): Short province name (used as bus name)
- `official` (str): Official long province name
- `group1` (str): First grouping level
- `group2` (str): Second grouping level

**Example:**
```
short    official              group1   group2
서울     서울특별시            육지     수도권
부산     부산광역시            육지     육지
대구     대구광역시            육지     육지
인천     인천광역시            육지     수도권
광주     광주광역시            육지     육지
대전     대전광역시            육지     육지
울산     울산광역시            육지     육지
세종     세종특별자치시        육지     육지
경기     경기도                육지     수도권
강원     강원특별자치도        육지     육지
충북     충청북도              육지     육지
충남     충청남도              육지     육지
전북     전북특별자치도        육지     육지
전남     전라남도              육지     육지
경북     경상북도              육지     육지
경남     경상남도              육지     육지
제주     제주특별자치도        제주     제주
```

**Notes:**
- `short` used as bus names in network
- `official` matched against original bus data
- `group1`: Simple grouping (mainland vs. islands)
- `group2`: More detailed grouping (metropolitan, mainland, islands)
- Specified by `region_groups` setting

---

### 16. province_demand† (Optional)

**Purpose:** Regional load distribution shares

**Columns:**
- Region columns (one per province)
- Values are shares (must sum to 1.0)

**Example:**
```
서울    경기    강원    충북    충남    ...
0.20    0.25    0.05    0.04    0.06    ...
```

**Calculation:**
```python
regional_load['서울'][t] = total_load[t] × 0.20
regional_load['경기'][t] = total_load[t] × 0.25
```

**Notes:**
- Shares should sum to 1.0 (100%)
- If not provided, loads distributed based on original bus locations

---

## Temporal Configuration

These sheets control time resolution and range (only in config_group.xlsx).

### 17. modelling_setting† (Optional)

**Purpose:** Temporal and modeling parameters

**Columns:**
- `attributes` (str): Setting name
- `value` (int, float, or str): Setting value

**Settings:**
```
attributes       value
year             2024
weights          4
snapshot_start   01/01/2024 00:00
snapshot_end     168
```

**Setting Descriptions:**

| Setting | Type | Description |
|---------|------|-------------|
| `year` | int | Modeling year (informational) |
| `weights` | int | Temporal aggregation factor (hours) |
| `snapshot_start` | str | Start date/time (DD/MM/YYYY HH:MM) |
| `snapshot_end` | int | Number of snapshots to include |

**Weights:**
- `1`: Hourly resolution (no resampling)
- `4`: 4-hour resolution (8760 → 2190 snapshots)
- `12`: 12-hour resolution (8760 → 730 snapshots)
- `24`: Daily resolution (8760 → 365 snapshots)

**Snapshot Selection:**
```python
# Example: First week of January
snapshot_start = '01/01/2024 00:00'  # Day-first format!
snapshot_end = 168  # 7 days × 24 hours
```

**Notes:**
- **Date format is day-first:** DD/MM/YYYY HH:MM
- Snapshot limiting applied BEFORE resampling
- If `weights=4` and `snapshot_end=168`, result is 42 snapshots (168/4)

---

### 18. resample_rules† (Optional)

**Purpose:** Define how to resample static component attributes

**Columns:**
- `component` (str): Component type (e.g., 'generators')
- `attribute` (str): Attribute name
- `rule` (str): Resampling rule
- `value` (float or str, optional): Value for 'fixed' rule

**Rules:**
- `scale`: Multiply by weights
- `fixed`: Set to specific value
- `default`: Reset to PyPSA default
- `skip`: Don't modify

**Example:**
```
component    attribute          rule     value
generators   ramp_limit_up      scale
generators   ramp_limit_down    scale
generators   min_up_time        scale
generators   min_down_time      scale
generators   start_up_cost      skip
generators   shut_down_cost     skip
lines        s_max_pu           skip
```

**Scaling Example:**
```python
# Original (1-hour): ramp_limit_up = 100 MW/hour
# weights = 4
# Resampled (4-hour): ramp_limit_up = 400 MW/4-hour
```

**Notes:**
- Only applies to static attributes (not time-series)
- Time-series automatically resampled using mean
- Critical for ramp limits and time-based constraints

---

## Configuration Examples

### Example 1: Basic Single-Node Configuration

**File:** `config/config_single.xlsx`

**Key Sheets:**
- carrier_mapping: Standard mappings
- generator_attributes: Default + carrier-specific
- file_paths: Point to 2024 base year data
- cc_merge_rules: Sum capacities, mean efficiency
- Years: [2024]
- carrier_order: nuclear, coal, gas, hydro, solar, wind

**Use Case:**
- Quick national-level analysis
- No transmission constraints
- Test configuration changes

---

### Example 2: Provincial Analysis with Generator Aggregation

**File:** `config/config_province.xlsx`

**Additional Configuration:**
```
regional_aggregation:
  aggregate_by_region: TRUE
  aggregate_by_carrier: TRUE
  region_column: province

generator_region_agg_rules:
  p_nom: sum
  efficiency: mean
  bus: region

lines_config:
  grouping: by_voltage
  circuits_rule: sum
  s_nom_rule: sum
  impedance_rule: weighted_by_circuits
  remove_self_loops: TRUE
```

**Result:**
- 17 provincial buses
- One generator per (carrier, province)
- Multiple transmission lines per voltage level
- No intra-provincial lines

---

### Example 3: Group-Level with Temporal Resampling

**File:** `config/config_group.xlsx`

**Additional Configuration:**
```
regional_aggregation:
  aggregate_by_region: TRUE
  aggregate_by_carrier: TRUE
  aggregate_regions_by_group: TRUE
  region_groups: group1

modelling_setting:
  year: 2024
  weights: 4
  snapshot_start: 01/01/2024 00:00
  snapshot_end: 8760

resample_rules:
  generators, ramp_limit_up, scale
  generators, ramp_limit_down, scale
```

**Result:**
- 2 group buses (육지, 제주)
- One generator per (carrier, group)
- 4-hour snapshots (2190 total)
- Full year simulation
- Ramp limits scaled to 4-hour intervals

---

## Best Practices

### 1. Configuration File Management

**Version Control:**
- Keep configuration files in git
- Use descriptive commit messages when changing configs
- Tag configurations for important runs

**Naming Convention:**
```
config_single.xlsx      # Base configuration
config_province_v2.xlsx # Provincial with modifications
config_group_test.xlsx  # Testing configuration
```

### 2. Carrier Configuration

**Consistent Naming:**
- Use lowercase English names
- Avoid spaces and special characters
- Examples: 'gas', 'coal', 'nuclear', 'solar', 'wind'

**Default Values:**
- Always define 'default' carrier in generator_attributes
- Provides fallback for new/unconfigured carriers
- Prevents missing attribute errors

### 3. Regional Aggregation

**Start Simple:**
1. First run: `aggregate_by_region=TRUE`, `aggregate_by_carrier=FALSE`
2. Verify bus mapping and load distribution
3. Then enable: `aggregate_by_carrier=TRUE`
4. Finally: `aggregate_regions_by_group=TRUE`

**Check Mappings:**
- Ensure province_mapping covers all provinces in data
- Verify load shares sum to 1.0
- Test with `remove_self_loops=FALSE` first

### 4. Temporal Configuration

**Testing:**
- Start with small snapshot range (e.g., 48 hours)
- Use higher weights (e.g., weights=12) for faster testing
- Expand to full year once validated

**Resampling:**
- Always scale ramp limits when resampling
- Be careful with min_up_time and min_down_time
- Test different weight values for sensitivity

### 5. Optimization Settings

**Generator Constraints:**
- Set realistic p_min_pu (avoid infeasibility)
- Use max_cf/min_cf for baseload (nuclear, coal)
- Leave solar/wind unconstrained (rely on p_max_pu)

**Storage:**
- Set appropriate max_hours (4-8 for batteries, 8-16 for pumped hydro)
- Include standing_loss for realistic modeling
- Use round-trip efficiency = 0.8-0.9

---

## Troubleshooting

### Issue 1: Optimization Infeasible

**Symptoms:**
```python
status = ('warning', 'infeasible')
```

**Checks:**
1. Total generation capacity > peak load?
2. Energy constraints too tight (e_sum_max)?
3. Transmission capacity sufficient after aggregation?
4. p_min_pu settings too restrictive?

**Solutions:**
- Temporarily remove energy constraints
- Disable `remove_self_loops`
- Reduce `aggregate_by_carrier` to identify capacity issues
- Check line aggregation rules (s_nom_rule)

---

### Issue 2: Missing Data

**Symptoms:**
```python
KeyError: 'fuel_cost'
```

**Checks:**
1. Does monthly_data.csv contain required attributes?
2. Are carrier names consistent (before/after standardization)?
3. Do aggregation levels match (national/province/generator)?

**Solutions:**
- Check `status` column (must be `TRUE`)
- Verify carrier names in both config and data files
- Ensure `aggregation` column matches expected level

---

### Issue 3: Regional Aggregation Errors

**Symptoms:**
```python
ValueError: Province '강원특별자치도' not in mapping
```

**Checks:**
1. Does province_mapping contain all provinces?
2. Are province names spelled correctly?
3. Do bus data use same province names?

**Solutions:**
- Add missing provinces to province_mapping
- Standardize province names in bus data
- Check for extra spaces or special characters

---

### Issue 4: Date Parsing Errors

**Symptoms:**
```python
ValueError: day is out of range for month
```

**Checks:**
1. Are dates in DD/MM/YYYY format?
2. Is dayfirst=True in pd.to_datetime()?
3. Are all dates valid (no Feb 30)?

**Solutions:**
- Use DD/MM/YYYY HH:MM format consistently
- Verify snapshot_start in modelling_setting
- Check date format in CSV files

---

### Issue 5: Aggregation Results Unexpected

**Symptoms:**
- Line capacities too small after aggregation
- Generator capacities don't match expected totals

**Checks:**
1. Is grouping='by_voltage' separating lines?
2. Is s_nom_rule using 'sum' or 'max'?
3. Are generator aggregation rules correct?

**Solutions:**
- Review lines_config settings
- Check circuit counts before/after aggregation
- Print debug info in aggregation functions
- Verify aggregation rules in config

---

## Related Documentation

- [Main Scripts Documentation](01_MAIN_SCRIPTS.md)
- [Library Modules Documentation](02_LIBRARY_MODULES.md)
- [Process Flow Documentation](03_PROCESS_FLOW.md)
