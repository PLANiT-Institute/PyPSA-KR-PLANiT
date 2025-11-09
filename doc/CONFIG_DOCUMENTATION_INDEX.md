# PyPSA Configuration System - Documentation Index

## Overview

This directory contains comprehensive documentation for the PyPSA configuration system. Three documents are provided at different levels of detail.

## Documentation Files

### 1. CONFIG_SYSTEM_DOCUMENTATION.md (Recommended: Start Here)
**Comprehensive Reference - 30 KB, 984 lines**

Complete detailed guide covering:
- Configuration overview and principles
- All 11 configuration sections with full explanations
- When each setting is used
- Available options and rules
- Complete workflows (single-node and regional)
- Data flow diagrams
- Detailed examples and use cases
- Configuration best practices
- Debugging guide

**Use this for:**
- Learning the config system thoroughly
- Understanding how components interact
- Creating new configurations
- Debugging configuration issues
- Understanding data flow

**Navigate to sections:**
- Configuration Sections (p.3)
- Workflow and Execution Order (p.5)
- Examples (p.8)

---

### 2. CONFIG_QUICK_REFERENCE.md (Quick Lookup - 12 KB)
**Quick Reference Guide - 490 lines**

Quick lookup guide featuring:
- Config sections at a glance (table format)
- Quick setup examples for each section
- Common configurations (Conservative, Flexible, Detailed Regional)
- Line aggregation rules summary
- Troubleshooting checklist
- File paths reference
- Function quick reference

**Use this for:**
- Quick lookups while working
- Remembering available options
- Troubleshooting specific issues
- Finding function locations
- Quick copy-paste examples

**Navigate to sections:**
- Config Sections at a Glance (p.1)
- Line Aggregation Rules (p.4)
- Troubleshooting Checklist (p.5)
- Key Functions Quick Reference (p.8)

---

### 3. CONFIG_SUMMARY.txt (Executive Summary - This File)
**Executive Summary - Quick Overview**

High-level overview covering:
- Documentation files overview
- All 11 config sections (one-line descriptions)
- Workflow comparison
- Available rules for CC merge, regional aggregation, generator attributes
- Data file format specification
- Key functions by module
- Important notes and requirements

**Use this for:**
- Quick understanding of what exists
- Getting an overview before diving deep
- Reference during presentations
- Understanding relationships between sections

---

## Configuration Sections Quick Reference

| # | Section | Purpose | When Used |
|---|---------|---------|-----------|
| 1 | **carrier_mapping** | Map fuel type names to standard carriers | Final step before optimization |
| 2 | **generator_attributes** | Set operational limits per carrier | After carrier standardization |
| 3 | **global_constraints** | System-wide generation limits | Prepared (not yet active) |
| 4 | **cc_merge_rules** | Merge multi-unit generators | Early in workflow |
| 5 | **generator_region_aggregator_rules** | Aggregate generators by region | Regional workflows |
| 6 | **regional_aggregation** | Control regional network aggregation | Regional workflows |
| 7 | **monthly_data** | Path to monthly time-series data | Data loading |
| 8 | **snapshot_data** | Path to hourly time-series data | Data loading |
| 9 | **Base_year** | Network data location | Network loading |
| 10 | **Years** | Modeling years list | Multi-year analysis |
| 11 | **regional_settings** | Regional parameters | Throughout workflow |

---

## How to Use These Documents

### Scenario 1: Learning the System (New User)
1. Start with this index for overview
2. Read CONFIG_SYSTEM_DOCUMENTATION.md sections:
   - Configuration Overview
   - Configuration Sections (read 1-3 sections of interest)
   - Workflow and Execution Order
3. Use CONFIG_QUICK_REFERENCE.md for hands-on examples

### Scenario 2: Quick Lookup (During Development)
1. Consult CONFIG_QUICK_REFERENCE.md tables
2. If more detail needed, reference CONFIG_SYSTEM_DOCUMENTATION.md
3. Use CONFIG_SUMMARY.txt for a reminder of what exists

### Scenario 3: Debugging Configuration (Troubleshooting)
1. Check CONFIG_QUICK_REFERENCE.md Troubleshooting Checklist
2. Find relevant section in CONFIG_SYSTEM_DOCUMENTATION.md
3. Check examples in that section

### Scenario 4: Creating New Configuration
1. Reference CONFIG_SUMMARY.txt for all sections needed
2. Use examples from CONFIG_QUICK_REFERENCE.md
3. Check CONFIG_SYSTEM_DOCUMENTATION.md for detailed options
4. Verify with best practices section

---

## Key Concepts

### Critical: Carrier Name Ordering
The system uses a specific order for carrier names:
```
Data Files (original names)
    ↓ (Load Data)
Network (original names)
    ↓ (CC Merge, Monthly/Snapshot Data)
Network (still original names)
    ↓ (STANDARDIZE - FINAL STEP)
Network (standardized names)
    ↓ (Apply Generator Attributes)
Network Ready for Optimization
```

This order ensures data loads correctly while final network uses clean, standardized names.

### Three Main Workflows

**Single-Node:**
- All components connect to single "KR" bus
- No regional aggregation
- Simpler, faster optimization
- Used for national-level analysis

**Regional:**
- Components grouped by geography (provinces)
- Regional aggregation of all components
- Generators optionally aggregated by carrier+region
- More detailed spatial representation

**Future: Multi-Year:**
- Currently defined (Years section) but not active
- Will allow temporal analysis across multiple years

---

## Data File Formats

### monthly_data.csv / snapshot_data.csv
```
snapshot,carrier,components,components_t,attribute,value,status,region,aggregation
2024-01-01,LNG,generators,generators_t,fuel_cost,50000,TRUE,KR,national
```

Key points:
- `carrier`: Original carrier name (BEFORE mapping)
- `status`: TRUE to apply, FALSE to skip
- `aggregation`: "national", "province", or "generator"

---

## Configuration Examples

### Example 1: Minimal Configuration
```yaml
carrier_mapping:
  LNG: gas
generator_attributes:
  gas:
    p_min_pu: 0.2
monthly_data:
  file_path: "data/add/monthly_t.csv"
Base_year:
  year: 2024
  file_path: "data/Singlenode2024"
regional_settings:
  national_region: "KR"
```

### Example 2: Regional with CC Merge
```yaml
carrier_mapping:
  bituminous: coal
  LNG: gas
generator_attributes:
  coal:
    p_min_pu: 0.4
cc_merge_rules:
  p_nom: sum
  build_year: oldest
regional_aggregation:
  region_column: province
  aggregate_generators_by_carrier: true
  lines:
    grouping: by_voltage
    circuits: sum
    impedance: weighted_by_circuits
```

---

## Available Rules Summary

### CC Merge Rules
- `oldest`, `newest` - Min/Max (for dates)
- `smallest`, `largest` - Min/Max (for values)
- `sum`, `mean` - Aggregation operations
- `p_nom` - Use from largest generator
- `cc_group` - Use group identifier
- `remove` - Skip this attribute

### Regional Aggregation Rules
- **Lines**: by_voltage/ignore_voltage, circuits (sum/max/mean), impedance (weighted/mean/min/max)
- **Links**: p_nom (sum), default_efficiency, unlimited_capacity
- **Generators**: carrier, region, p_nom, oldest/newest, sum, mean, ignore

---

## File Organization

```
pypsa_alternative/
├── CONFIG_DOCUMENTATION_INDEX.md     (This file - Navigation)
├── CONFIG_SYSTEM_DOCUMENTATION.md    (Detailed - Start here)
├── CONFIG_QUICK_REFERENCE.md         (Quick lookup)
├── CONFIG_SUMMARY.txt                (Executive summary)
├── config/
│   ├── config_single.yaml            (Example: Single-node)
│   ├── config_province.yaml          (Example: Regional)
│   └── config_single.xlsx            (Example: Excel format)
├── libs/
│   ├── config.py                     (Configuration loading)
│   ├── cost_mapping.py              (Carrier mapping, attributes)
│   ├── cc_merger.py                 (CC merging)
│   ├── region_aggregator.py         (Regional aggregation)
│   ├── aggregators.py               (Generator aggregation)
│   ├── data_loader.py               (Network & data loading)
│   └── bus_mapper.py                (Bus mapping utility)
└── main_*.py                         (Execution scripts)
```

---

## Next Steps

1. **First Time?** Read CONFIG_SYSTEM_DOCUMENTATION.md sections on:
   - Configuration Overview
   - Workflow and Execution Order

2. **Need Examples?** Check:
   - CONFIG_QUICK_REFERENCE.md Common Configurations section
   - CONFIG_SYSTEM_DOCUMENTATION.md Examples section
   - config/ folder for actual YAML/Excel files

3. **Stuck?** Check:
   - CONFIG_QUICK_REFERENCE.md Troubleshooting Checklist
   - CONFIG_SYSTEM_DOCUMENTATION.md Debugging Guide
   - Example config files

4. **Ready to Configure?** Use:
   - CONFIG_QUICK_REFERENCE.md for quick setup templates
   - CONFIG_SYSTEM_DOCUMENTATION.md for detailed option reference
   - Example configs as templates

---

## Support for Different Users

### Data Analyst / Power System Specialist
- Start: CONFIG_SYSTEM_DOCUMENTATION.md Configuration Sections
- Then: CONFIG_QUICK_REFERENCE.md Common Configurations
- Reference: CONFIG_SUMMARY.txt Available Rules tables

### Software Developer / Engineer
- Start: CONFIG_SYSTEM_DOCUMENTATION.md Workflow and Execution Order
- Then: CONFIG_SYSTEM_DOCUMENTATION.md Data Flow section
- Reference: Source code files in libs/

### Project Manager / Non-Technical User
- Start: CONFIG_SUMMARY.txt
- Then: CONFIG_SYSTEM_DOCUMENTATION.md Examples
- Reference: CONFIG_QUICK_REFERENCE.md File Paths Reference

---

## Document Statistics

| File | Size | Lines | Content |
|------|------|-------|---------|
| CONFIG_SYSTEM_DOCUMENTATION.md | 30 KB | 984 | Complete reference guide |
| CONFIG_QUICK_REFERENCE.md | 12 KB | 490 | Quick lookup tables |
| CONFIG_SUMMARY.txt | 8 KB | 300+ | Executive summary |
| This file | ~6 KB | 250+ | Navigation index |

Total documentation: ~56 KB of comprehensive reference material

---

## Version Information

Created: November 9, 2025
Based on codebase analysis of:
- libs/config.py - Configuration loading (YAML and Excel support)
- libs/cost_mapping.py - Carrier mapping and generator attributes
- libs/cc_merger.py - Combined cycle generator merging
- libs/region_aggregator.py - Regional network aggregation
- libs/aggregators.py - Generator aggregation rules
- libs/data_loader.py - Network and data loading
- main_singlenode.py - Single-node workflow
- main_region.py - Regional workflow
- config/*.yaml - Example configurations

---

Last Updated: November 9, 2025
