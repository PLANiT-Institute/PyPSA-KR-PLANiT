# Configuration Quick Reference Guide

Quick lookup for common configuration tasks and options.

## Config Sections at a Glance

| Section | Location | Main Use | Active |
|---------|----------|----------|--------|
| `carrier_mapping` | Config root | Standardize carrier names | Before optimization |
| `generator_attributes` | Config root | Set gen limits/costs per carrier | After standardization |
| `global_constraints` | Config root | System-wide gen limits | Not yet active |
| `cc_merge_rules` | Config root | Merge multi-unit generators | Early in workflow |
| `generator_region_aggregator_rules` | Config root | Aggregate gens by region | Regional workflows |
| `regional_aggregation` | Config root | Regional network aggregation | Regional workflows |
| `monthly_data` | Config root | Monthly time-series file | Data loading |
| `snapshot_data` | Config root | Hourly time-series file | Data loading |
| `Base_year` | Config root | Network data location | Network loading |
| `Years` | Config root | Multi-year analysis | Not yet active |
| `regional_settings` | Config root | Regional parameters | Throughout |

---

## Carrier Mapping Quick Setup

**What it does:** Maps diverse fuel type names to standardized carrier names.

**Typical setup:**

```yaml
carrier_mapping:
  # Coal types → coal
  bituminous: coal
  anthracite: coal
  # Gas types → gas
  LNG: gas
  # Keep as-is
  nuclear: nuclear
  wind: wind
  solar: solar
```

**Key points:**
- Applied as FINAL step before optimization
- Data loading uses original names, output uses standardized names
- Reduces model complexity by grouping similar resources

---

## Generator Attributes Quick Setup

**What it does:** Sets constraints for all generators of a carrier type.

**Typical setup:**

```yaml
generator_attributes:
  gas:
    p_min_pu: 0.2      # Min 20% of capacity
    p_max_pu: 1.0      # Max 100% of capacity
  coal:
    p_min_pu: 0.4      # Min 40% (longer startup)
    p_max_pu: 1.0
  nuclear:
    p_min_pu: 0.6      # Min 60% (baseload plant)
    p_max_pu: 1.0
```

**Key points:**
- p_min_pu = technical minimum (ramp-down time)
- p_max_pu = maximum (usually 1.0)
- Applied to ALL generators of matching carrier
- Applied AFTER carrier standardization

---

## CC Merge Rules Quick Setup

**What it does:** Combines multi-unit plants into single model units.

**Typical setup:**

```yaml
cc_merge_rules:
  p_nom: sum              # Sum capacities
  build_year: oldest      # Use earliest year
  efficiency: mean        # Average efficiency
  others: p_nom          # Default rule
```

**Available rules:**

```
oldest/smallest → min()      (for years, costs)
newest/largest → max()       (for years, capacities)
sum → sum()                  (for capacities)
mean → mean()                (for efficiencies)
p_nom → from largest unit    (for unit-specific attrs)
```

**Key points:**
- Applied early, BEFORE data loading
- Requires `cc_group` column in generators CSV
- Creates generator named `{cc_group}_CC`

---

## Regional Aggregation Quick Setup

**What it does:** Groups network by geography (provinces, states, etc).

**Minimal setup:**

```yaml
regional_aggregation:
  region_column: province
  demand_file: data/others/province_demand.xlsx
  aggregate_generators_by_carrier: true
  
  lines:
    grouping: by_voltage
    circuits: sum
    impedance: weighted_by_circuits
```

**Aggregation per type:**

| Component | Aggregation | Rule |
|-----------|-------------|------|
| **Buses** | One per region | Average coordinates |
| **Generators** | By carrier+region (optional) | p_nom: sum, cost: mean |
| **Lines** | By region pair+voltage | circuits: sum, impedance: weighted |
| **Links** | By region pair | p_nom: sum, efficiency: 1.0 |
| **Loads** | One per region | Distributed by demand |

**Key points:**
- region_column must exist in buses, generators, loads
- demand_file format: columns = [region_column, 'demand']
- Creates buses named after regions
- Creates generators named `{carrier}_{region}` if enabled

---

## Data File Quick Reference

### monthly_data Format

```csv
snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
2024-01-01,LNG,generators,generators_t,fuel_cost,50000,TRUE,KR,national
```

**Columns:**
- `snapshot`: Date (first day of month)
- `carrier`: Original carrier name (before mapping)
- `components`: Table name (generators, loads, etc)
- `components_t`: Time-series table name
- `attribute`: Column to set (fuel_cost, p_max_pu, etc)
- `value`: Value to apply
- `status`: TRUE to apply, FALSE to skip
- `region`: Region name (for matching)
- `aggregation`: "national", "province", or "generator"

### snapshot_data Format

Same as monthly_data but with hourly timestamps:

```csv
snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
2024-01-01 00:00,wind,generators,generators_t,p_max_pu,0.8,TRUE,KR,national
2024-01-01 01:00,wind,generators,generators_t,p_max_pu,0.7,TRUE,KR,national
```

---

## Workflow Comparison

### Single-Node (main_singlenode.py)

```
Load Config
  ↓
Load Network (single "KR" bus)
  ↓
Merge CC Generators
  ↓
Apply Monthly/Snapshot Data (original names)
  ↓
Standardize Carrier Names
  ↓
Apply Generator Attributes
  ↓
Optimize
```

### Regional (main_region.py)

```
Load Config
  ↓
Load Network (multiple buses per province)
  ↓
Merge CC Generators
  ↓
Apply Monthly/Snapshot Data (original names)
  ↓
Aggregate by Region
  ├─ Create regional buses
  ├─ Map/aggregate components
  ├─ Optionally aggregate generators by carrier+region
  └─ Create regional loads
  ↓
Standardize Carrier Names
  ↓
Apply Generator Attributes
  ↓
Optimize
```

---

## Line Aggregation Rules

**grouping:**
- `by_voltage` - Keeps 230kV and 345kV separate
- `ignore_voltage` - Combines all voltages

**circuits (parallel lines):**
- `sum` - Total parallel capacity
- `max` - Use maximum
- `mean` - Average

**s_nom (power rating):**
- `sum` - Total power
- `scale_by_circuits` - Scale by circuit count
- `keep_original` - Use one line's rating

**impedance (r, x, b):**
- `weighted_by_circuits` - Most accurate (weighted by circuit count)
- `mean` - Simple average
- `min/max` - Use minimum or maximum

**Typical setup:**

```yaml
lines:
  grouping: by_voltage        # Keep voltages separate
  circuits: sum               # Total circuits
  s_nom: scale_by_circuits    # Scale by circuits
  impedance: weighted_by_circuits  # Accurate weighting
  length: mean                # Average distance
  remove_self_loops: true     # No intra-region lines
```

---

## Generator Region Aggregator Rules

**Purpose:** Define how to merge generators by (carrier, region) pair.

**Key rules:**

```yaml
generator_region_aggregator_rules:
  carrier: carrier              # Keep carrier
  province: region              # Use region
  bus: region                   # Map to regional bus
  p_nom: sum                    # Sum capacities
  efficiency: mean              # Average efficiency
  marginal_cost: mean           # Average cost
  capital_cost: mean
  control: PQ                   # Fixed value
  others: ignore                # Skip other attrs
```

**Result names:** `{carrier}_{region}`

Examples:
- `coal_경기`
- `gas_서울`
- `wind_강원`

---

## Common Configurations

### Conservative (Low Carbon Friendly)

```yaml
generator_attributes:
  coal:
    p_min_pu: 0.5              # High minimum
    p_max_pu: 0.9              # Limited max
  wind:
    p_min_pu: 0.0              # No minimum
    p_max_pu: 1.0
    max_cf: 0.35
  solar:
    p_min_pu: 0.0
    p_max_pu: 1.0
    max_cf: 0.25
```

### Flexible (Gas-Heavy)

```yaml
generator_attributes:
  coal:
    p_min_pu: 0.2              # Low minimum
    p_max_pu: 1.0
  gas:
    p_min_pu: 0.0              # Very flexible
    p_max_pu: 1.0
  nuclear:
    p_min_pu: 0.8              # Baseload
    p_max_pu: 1.0
```

### Detailed Regional

```yaml
regional_aggregation:
  region_column: province
  aggregate_generators_by_carrier: true
  
  lines:
    grouping: by_voltage           # Detailed
    impedance: weighted_by_circuits # Accurate
    remove_self_loops: false       # Keep all
  
  links:
    grouping: by_voltage
    default_efficiency: 0.98       # Account for losses
```

---

## Troubleshooting Checklist

**Carrier mapping not working?**
- [ ] Are original carrier names in data files?
- [ ] Is mapping spelled correctly?
- [ ] Are names case-sensitive?

**Generator attributes not applied?**
- [ ] Did you standardize carriers first?
- [ ] Do generator carriers match attribute keys?
- [ ] Are attributes valid PyPSA columns?

**Regional aggregation fails?**
- [ ] Does region_column exist in CSV?
- [ ] Is demand_file path correct?
- [ ] Does demand file have correct region names?

**CC merge not working?**
- [ ] Is cc_group column in generators.csv?
- [ ] Are cc_group values non-empty strings?
- [ ] Is config['cc_merge_rules'] present?

**Data not applying?**
- [ ] Is status column TRUE?
- [ ] Do carriers match (original names)?
- [ ] Is aggregation level correct?
- [ ] Is file path accessible?

---

## File Paths Reference

### Typical project structure:

```
project/
├── config/
│   ├── config_single.yaml
│   └── config_province.yaml
├── data/
│   ├── Singlenode2024/        (Base network)
│   │   ├── buses.csv
│   │   ├── generators.csv
│   │   └── ...
│   ├── Provincenode2024/      (Regional network)
│   │   ├── buses.csv
│   │   ├── generators.csv
│   │   └── ...
│   ├── add/                    (Time-series data)
│   │   ├── monthly_t.csv
│   │   └── snapshot_t.csv
│   └── others/
│       ├── province_demand.xlsx
│       └── province_mapping.csv
├── main_singlenode.py
├── main_region.py
└── libs/
    ├── config.py
    ├── data_loader.py
    ├── cost_mapping.py
    ├── cc_merger.py
    ├── region_aggregator.py
    └── aggregators.py
```

---

## Config Loading Examples

### Load YAML

```python
from libs.config import load_config

config = load_config("config/config_single.yaml")
print(config['carrier_mapping'])
print(config['generator_attributes']['coal'])
```

### Load Excel

```python
config = load_config("config/config_single.xlsx")
# Will automatically parse all sheets into dict structure
```

### Access config values

```python
# Single value
national_region = config['regional_settings']['national_region']

# Carrier mapping
new_name = config['carrier_mapping'].get('LNG', 'LNG')  # 'gas' or 'LNG'

# Generator attributes for all carriers
for carrier, attrs in config['generator_attributes'].items():
    print(f"{carrier}: min={attrs.get('p_min_pu', 0)}, max={attrs.get('p_max_pu', 1)}")
```

---

## Key Functions Quick Reference

| Function | Module | Purpose | Input |
|----------|--------|---------|-------|
| `load_config()` | config.py | Load config from YAML/Excel | file path |
| `load_network()` | data_loader.py | Load network from CSV | config |
| `load_monthly_data()` | data_loader.py | Load monthly time-series | config |
| `load_snapshot_data()` | data_loader.py | Load snapshot time-series | config |
| `merge_cc_generators()` | cc_merger.py | Merge CC units | network, config |
| `standardize_carrier_names()` | cost_mapping.py | Apply carrier mapping | network, mapping |
| `apply_generator_attributes()` | cost_mapping.py | Set gen limits per carrier | network, attributes |
| `apply_monthly_data_to_network()` | cost_mapping.py | Apply monthly data | network, config, data |
| `apply_snapshot_data_to_network()` | cost_mapping.py | Apply snapshot data | network, config, data |
| `aggregate_network_by_region()` | region_aggregator.py | Regional aggregation | network, config |
| `aggregate_generators_by_carrier_and_region()` | aggregators.py | Gen aggregation by region | network, config, region_col |

---

## YAML vs Excel

### YAML Advantages
- Human-readable
- Easy to version control
- Simpler structure
- Good for manual editing

### Excel Advantages
- Visual layout
- Easy for non-programmers
- Structured validation
- Good for complex hierarchies

### Using YAML

```yaml
carrier_mapping:
  LNG: gas
  
generator_attributes:
  coal:
    p_min_pu: 0.4
```

### Using Excel

| Sheet | Column 1 | Column 2 |
|-------|----------|----------|
| carrier_mapping | LNG | gas |
| generator_attributes (coal row) | p_min_pu | 0.4 |

Both produce identical config dict internally.

