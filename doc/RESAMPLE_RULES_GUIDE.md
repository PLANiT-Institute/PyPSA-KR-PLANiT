# Resample Rules Configuration Guide

## Overview

The resampling system is now **fully configurable** through the `resample_rules` sheet in `config_group.xlsx`. **Nothing is hardcoded** in the code - all resampling behavior is controlled by the configuration file.

## Quick Start

1. **Run the template generator**:
   ```bash
   python3 create_resample_rules_template.py
   ```

2. **Add the sheet to your config**:
   - Open `resample_rules_template.xlsx`
   - Copy the `resample_rules` sheet
   - Paste into your `config_group.xlsx`

3. **Customize as needed**:
   - Add/remove rows for specific components
   - Change rules (mean → max, scale → fixed, etc.)
   - Add fixed values where appropriate

## Configuration Format

The `resample_rules` sheet has the following columns:

| Column | Description | Examples |
|--------|-------------|----------|
| **component** | Component name (with `_t` suffix for time-series) | `generators_t`, `generators`, `loads_t`, `storage_units` |
| **attribute** | Attribute name to resample | `p_max_pu`, `ramp_limit_up`, `standing_loss` |
| **rule** | How to resample (see Rule Types below) | `mean`, `scale`, `sum`, `max`, `skip` |
| **value** | Fixed value (only used when rule='fixed') | `0.5`, `None` |
| **notes** | Documentation (ignored by code) | Any comments |

## Rule Types

### Time-Series Rules (for `_t` components)

| Rule | Description | Use Case | Example |
|------|-------------|----------|---------|
| **mean** | Average over period | Most time-series data | Solar availability: [0.8, 0.9, 1.0, 0.9] → [0.9] |
| **sum** | Sum over period | Energy flows | Hydro inflow: [100, 150, 120, 130] MWh → [500] MWh |
| **max** | Maximum value | Conservative estimates | Wind: [0.6, 0.8, 0.5, 0.7] → [0.8] |
| **min** | Minimum value | Conservative minimums | Rarely used |
| **fixed** | Set to constant | Override with value | Set all to 0.5 |
| **skip** | Do nothing | Leave unchanged | - |

### Static Attribute Rules

| Rule | Description | Use Case | Example |
|------|-------------|----------|---------|
| **scale** | Multiply by weights | Per-snapshot rates | ramp_limit=0.2, weights=4 → 0.8 |
| **fixed** | Set to value | Override attribute | Set p_min_pu=0.0 for all |
| **skip** | Do nothing | Leave unchanged | - |

## Critical Attributes (Must Be Configured)

These attributes **MUST** have rules defined, or your model may be incorrect:

### ✓ Must Scale with Weights

```
component: generators, attribute: ramp_limit_up, rule: scale
component: generators, attribute: ramp_limit_down, rule: scale
component: storage_units, attribute: standing_loss, rule: scale
component: stores, attribute: standing_loss, rule: scale
```

**Why?** These are "per-snapshot" or "per-hour" rates that change meaning when snapshot duration changes.

### ✓ Time-Series That Should Be Resampled

```
component: generators_t, attribute: p_max_pu, rule: mean
component: loads_t, attribute: p_set, rule: mean
component: storage_units_t, attribute: inflow, rule: sum
```

**Why?** Time-series data must be aggregated to match new snapshot frequency.

## Examples

### Example 1: Conservative Renewable Estimates

Use `max` instead of `mean` for renewable availability:

```excel
component       | attribute  | rule | value | notes
----------------|------------|------|-------|--------------------------------
generators_t    | p_max_pu   | max  | None  | Use peak availability (conservative)
```

**Effect**:
- 1h solar: [0.5, 0.8, 1.0, 0.7] → 4h: [1.0] instead of [0.75]
- Ensures you don't underestimate renewable capacity

### Example 2: Relax Nuclear Constraints for Coarse Resolution

```excel
component       | attribute  | rule  | value | notes
----------------|------------|-------|-------|--------------------------------
generators      | p_min_pu   | fixed | 0.4   | Relax nuclear minimum from 0.7 to 0.4
```

**Effect**:
- Helps avoid infeasibility with coarser temporal resolution
- Nuclear can operate at lower capacity when needed

### Example 3: Sum Energy Flows, Average Power

```excel
component       | attribute  | rule | value | notes
----------------|------------|------|-------|--------------------------------
storage_units_t | inflow     | sum  | None  | Total hydro inflow over period
generators_t    | p_max_pu   | mean | None  | Average renewable availability
loads_t         | p_set      | mean | None  | Average demand
```

**Effect**:
- Inflow: [10, 15, 12, 13] MWh/h → [50] MWh/4h (total)
- Solar: [0.8, 0.9, 1.0, 0.9] → [0.9] (average)
- Load: [1000, 1200, 1100, 1050] MW → [1087.5] MW (average)

## Adding New Attributes

To resample a new attribute:

1. **Identify the component**: Is it time-series (`_t`) or static?
2. **Choose the rule**: Based on the attribute's meaning
3. **Add a row** to `resample_rules` sheet:

```excel
component       | attribute      | rule  | value | notes
----------------|----------------|-------|-------|--------------------------------
generators      | your_attribute | scale | None  | Your description here
```

## Debugging

If resampling doesn't work as expected:

1. **Check console output**: The resampling function prints what it's doing
   ```
   [info] generators_t.p_max_pu: resampled with 'mean'
   [info] generators.ramp_limit_up: scaled by 4
   ```

2. **Verify attribute exists**: Warning if attribute not found
   ```
   [warn] generators.nonexistent_attr: not found, skipping
   ```

3. **Check rule validity**: Warning for unknown rules
   ```
   [warn] Unknown rule 'average' for generators_t.p_max_pu, using mean
   ```

## Advanced: Rule Priority

Rules are processed in the order they appear in the sheet. If you have multiple rules for the same component/attribute:
- **Last rule wins**
- Use this to override defaults

Example:
```excel
component       | attribute  | rule | value | notes
----------------|------------|------|-------|--------------------------------
generators_t    | p_max_pu   | mean | None  | Default: average
generators_t    | p_max_pu   | max  | None  | Override: use max instead
```
→ Will use `max` (last rule)

## Complete Example Configuration

See `resample_rules_template.xlsx` for a complete working example with all recommended rules.

## Summary

✅ **Fully configurable** - add any component/attribute
✅ **No hardcoding** - all logic driven by config
✅ **Extensible** - easy to add new rules
✅ **Documented** - notes column for explanations
✅ **Safe defaults** - template includes all critical attributes

---

**Generated by**: create_resample_rules_template.py
**Last updated**: 2024
