# Comprehensive Analysis: PyPSA Attributes & Temporal Scaling

This document analyzes ALL PyPSA attributes to identify which ones require scaling when changing temporal resolution (e.g., from 1-hour to 4-hour snapshots).

## Analysis Basis

When resampling from 1-hour to 4-hour snapshots with `weights=4`:
- **Per-snapshot attributes**: Need scaling (×4) because snapshot duration changes
- **Per-hour attributes**: Need scaling to maintain physical meaning
- **Absolute values**: No scaling needed (MW, MWh capacity, efficiency ratios)
- **Time-series**: Automatically resampled (handled by pandas `.resample().mean()`)

---

## 1. GENERATOR ATTRIBUTES

### ✓ NEEDS SCALING (×4 for weights=4)

| Attribute | Unit | Reason |
|-----------|------|--------|
| `ramp_limit_up` | per-unit/snapshot | PyPSA applies per snapshot, not per hour |
| `ramp_limit_down` | per-unit/snapshot | PyPSA applies per snapshot, not per hour |
| `ramp_limit_start_up` | per-unit/snapshot | Applied during startup transition |
| `ramp_limit_shut_down` | per-unit/snapshot | Applied during shutdown transition |
| `e_sum_max` | MWh | Total energy constraint over period (if pre-calculated) |
| `e_sum_min` | MWh | Total energy constraint over period (if pre-calculated) |

**Note on e_sum_max/min**: These should be calculated AFTER resampling using `total_hours = len(snapshots) × weights`, so they don't need explicit scaling if calculated correctly.

### ✗ NO SCALING NEEDED

| Attribute | Unit | Reason |
|-----------|------|--------|
| `p_nom` | MW | Absolute capacity |
| `p_nom_min/max` | MW | Capacity bounds |
| `p_min_pu` | per-unit | Fraction of capacity (0-1) |
| `p_max_pu` | per-unit | Fraction of capacity (0-1) |
| `efficiency` | per-unit | Conversion efficiency ratio |
| `capital_cost` | €/MW | Annualized cost per MW |
| `marginal_cost` | €/MWh | Cost per energy (already energy-based) |
| `marginal_cost_quadratic` | €/MWh² | Quadratic cost term |
| `start_up_cost` | € | One-time cost |
| `shut_down_cost` | € | One-time cost |
| `min_up_time` | snapshots | Already in snapshot units |
| `min_down_time` | snapshots | Already in snapshot units |
| `committable` | boolean | Flag |
| `build_year` | year | Date |

### ⚡ TIME-SERIES (Resampled Automatically)

All `generators_t` attributes are automatically handled by `resample()`:
- `p_max_pu` → resampled with `.mean()`
- `p_min_pu` → resampled with `.mean()`
- `p_set` → resampled with `.mean()`
- `marginal_cost` → resampled with `.mean()`
- `efficiency` → resampled with `.mean()`

---

## 2. STORAGE UNIT ATTRIBUTES

### ✓ NEEDS SCALING (×4 for weights=4)

| Attribute | Unit | Reason |
|-----------|------|--------|
| `standing_loss` | per hour | **CRITICAL**: Loss rate per hour needs scaling! |
| `marginal_cost_storage` | €/(MWh·hour) | Cost per MWh per hour |

**IMPORTANT**: `standing_loss` is specified as "losses per hour to state of charge"
- 1-hour snapshot: `standing_loss = 0.01` → 1% loss per hour ✓
- 4-hour snapshot: needs `standing_loss = 0.04` → 4% loss per 4 hours = 1% per hour ✓

### ⚠️ SPECIAL CONSIDERATION

| Attribute | Current Handling | Notes |
|-----------|-----------------|--------|
| `max_hours` | hours | Storage duration in hours - likely OK as-is |
| `state_of_charge_initial` | MWh | Absolute energy - no scaling |
| `cyclic_state_of_charge` | boolean | No scaling |

### ✗ NO SCALING NEEDED

| Attribute | Unit | Reason |
|-----------|------|--------|
| `p_nom` | MW | Power capacity |
| `efficiency_store` | per-unit | Charging efficiency (0-1) |
| `efficiency_dispatch` | per-unit | Discharging efficiency (0-1) |
| `p_min_pu` | per-unit | Minimum power fraction |
| `p_max_pu` | per-unit | Maximum power fraction |

---

## 3. STORE ATTRIBUTES

### ✓ NEEDS SCALING (×4 for weights=4)

| Attribute | Unit | Reason |
|-----------|------|--------|
| `standing_loss` | per hour | **CRITICAL**: Loss rate per hour |
| `marginal_cost_storage` | €/(MWh·hour) | Cost per MWh per hour |

### ✗ NO SCALING NEEDED

| Attribute | Unit | Reason |
|-----------|------|--------|
| `e_nom` | MWh | Energy capacity |
| `e_min_pu` | per-unit | Minimum state fraction |
| `e_max_pu` | per-unit | Maximum state fraction |
| `e_initial` | MWh | Initial stored energy |
| `e_cyclic` | boolean | Cyclic constraint flag |
| `marginal_cost` | €/MWh | Cost per energy |

---

## 4. LINK ATTRIBUTES

### ✓ NEEDS SCALING (×4 for weights=4)

| Attribute | Unit | Reason |
|-----------|------|--------|
| `ramp_limit_up` | per-unit/snapshot | Applied per snapshot |
| `ramp_limit_down` | per-unit/snapshot | Applied per snapshot |
| `ramp_limit_start_up` | per-unit/snapshot | Startup ramp limit |
| `ramp_limit_shut_down` | per-unit/snapshot | Shutdown ramp limit |

### ✗ NO SCALING NEEDED

| Attribute | Unit | Reason |
|-----------|------|--------|
| `p_nom` | MW | Power capacity |
| `efficiency` | per-unit | Transfer efficiency |
| `efficiency2, efficiency3...` | per-unit | Multi-bus efficiencies |
| `p_min_pu` | per-unit | Minimum dispatch fraction |
| `p_max_pu` | per-unit | Maximum dispatch fraction |
| `marginal_cost` | €/MWh | Cost per energy |
| `min_up_time` | snapshots | Already in snapshot units |
| `min_down_time` | snapshots | Already in snapshot units |
| `length` | km | Physical length |

---

## 5. LOAD ATTRIBUTES

### ✗ ALL ATTRIBUTES: NO SCALING NEEDED

Loads only have power setpoints (MW) which are either:
- Static (`p_set` in MW) - no scaling
- Time-series (`loads_t.p_set`) - automatically resampled

---

## 6. LINE/TRANSFORMER ATTRIBUTES

### ✗ ALL ATTRIBUTES: NO SCALING NEEDED

Lines and transformers have electrical parameters that don't depend on temporal resolution:
- `s_nom`, `r`, `x`, `b`, `g`, `v_nom` - all electrical/physical parameters
- No ramp limits or time-dependent constraints

---

## SUMMARY: Complete List of Attributes Needing Scaling

### When using weights=4 (1h → 4h snapshots), multiply by 4:

```python
# GENERATORS
- ramp_limit_up
- ramp_limit_down
- ramp_limit_start_up
- ramp_limit_shut_down

# STORAGE UNITS
- standing_loss           # ⚠️ CRITICAL - currently NOT handled
- marginal_cost_storage   # ⚠️ Currently NOT handled

# STORES
- standing_loss           # ⚠️ CRITICAL - currently NOT handled
- marginal_cost_storage   # ⚠️ Currently NOT handled

# LINKS
- ramp_limit_up
- ramp_limit_down
- ramp_limit_start_up
- ramp_limit_shut_down
```

---

## CURRENT IMPLEMENTATION STATUS

### ✅ Currently Handled (in `libs/resample.py`)
- Generator ramp limits (all 4 types)
- Storage unit ramp limits (all 4 types)
- Link ramp limits (all 4 types)
- Time-series resampling (all `_t` attributes)

### ❌ NOT Currently Handled (MISSING!)
- **StorageUnit.standing_loss** - Loss rate per hour
- **Store.standing_loss** - Loss rate per hour
- **StorageUnit.marginal_cost_storage** - Cost per MWh per hour
- **Store.marginal_cost_storage** - Cost per MWh per hour

### ✅ Correctly Handled via Calculation
- `e_sum_max/min` - Calculated using `total_hours` in `energy_constraints.py`

---

## RECOMMENDATIONS

1. **CRITICAL FIX NEEDED**: Add scaling for `standing_loss` in both StorageUnits and Stores
2. **OPTIONAL**: Add scaling for `marginal_cost_storage` if used
3. **VERIFY**: Check if your network uses storage components with standing losses
4. **DOCUMENT**: Clearly document which attributes are scaled and why

---

## PyPSA Documentation Reference

- Ramp limits are "per snapshot" and NOT weighted by snapshot duration
- Standing loss is explicitly "per hour"
- Energy constraints use snapshot weightings when calculating totals
- Time-varying attributes use snapshot-indexed series

**Source**: https://docs.pypsa.org/latest/
