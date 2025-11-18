"""
Helper script to create a template resample_rules sheet for config_group.xlsx

Run this to generate a sample resample_rules configuration that you can
add to your config_group.xlsx file.
"""
import pandas as pd

# Create comprehensive resample rules
resample_rules = pd.DataFrame([
    # ========================================================================
    # TIME-SERIES COMPONENTS (resampled with pandas .resample())
    # ========================================================================

    # Generators time-series - DEFAULT RULES (apply to all carriers)
    {'component': 'generators_t', 'attribute': 'p_max_pu', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Default: Average renewable availability over period'},

    # Generators time-series - CARRIER-SPECIFIC OVERRIDES (examples)
    {'component': 'generators_t', 'attribute': 'p_max_pu', 'carrier': 'solar', 'rule': 'max', 'value': None,
     'notes': 'EXAMPLE: Solar uses max (conservative estimate)'},
    {'component': 'generators_t', 'attribute': 'p_max_pu', 'carrier': 'wind', 'rule': 'max', 'value': None,
     'notes': 'EXAMPLE: Wind uses max (conservative estimate)'},

    # Other time-series attributes (no carrier override usually needed)
    {'component': 'generators_t', 'attribute': 'p_min_pu', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average minimum output constraint'},
    {'component': 'generators_t', 'attribute': 'p_set', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average power setpoint'},
    {'component': 'generators_t', 'attribute': 'marginal_cost', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average marginal cost (e.g., fuel prices)'},
    {'component': 'generators_t', 'attribute': 'fuel_cost', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average fuel cost'},

    # Loads time-series
    {'component': 'loads_t', 'attribute': 'p_set', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average load demand over period'},

    # Storage units time-series
    {'component': 'storage_units_t', 'attribute': 'inflow', 'carrier': None, 'rule': 'sum', 'value': None,
     'notes': 'Total inflow over period (e.g., hydro reservoir)'},
    {'component': 'storage_units_t', 'attribute': 'p_max_pu', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average maximum power availability'},

    # Links time-series
    {'component': 'links_t', 'attribute': 'p_max_pu', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average link capacity availability'},
    {'component': 'links_t', 'attribute': 'efficiency', 'carrier': None, 'rule': 'mean', 'value': None,
     'notes': 'Average efficiency (e.g., temperature-dependent heat pump COP)'},

    # ========================================================================
    # STATIC COMPONENTS - ATTRIBUTES THAT NEED SCALING
    # ========================================================================

    # Generator ramp limits (per-snapshot attributes) - DEFAULT for all carriers
    {'component': 'generators', 'attribute': 'ramp_limit_up', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'CRITICAL: Ramp limits are per snapshot, must scale with weights'},
    {'component': 'generators', 'attribute': 'ramp_limit_down', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'CRITICAL: Ramp limits are per snapshot, must scale with weights'},
    {'component': 'generators', 'attribute': 'ramp_limit_start_up', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'Startup ramp limit, per snapshot'},
    {'component': 'generators', 'attribute': 'ramp_limit_shut_down', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'Shutdown ramp limit, per snapshot'},

    # EXAMPLE: Carrier-specific ramp limit override (optional)
    # {'component': 'generators', 'attribute': 'ramp_limit_up', 'carrier': 'nuclear', 'rule': 'fixed', 'value': 0.2,
    #  'notes': 'EXAMPLE: Override nuclear ramp limit to 0.2 (more flexible for coarse resolution)'},

    # Storage unit attributes
    {'component': 'storage_units', 'attribute': 'ramp_limit_up', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'Ramp limit per snapshot'},
    {'component': 'storage_units', 'attribute': 'ramp_limit_down', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'Ramp limit per snapshot'},
    {'component': 'storage_units', 'attribute': 'standing_loss', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'CRITICAL: Standing loss is per hour, must scale to per snapshot'},

    # Store attributes
    {'component': 'stores', 'attribute': 'standing_loss', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'CRITICAL: Standing loss is per hour, must scale to per snapshot'},

    # Link ramp limits
    {'component': 'links', 'attribute': 'ramp_limit_up', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'Ramp limit per snapshot'},
    {'component': 'links', 'attribute': 'ramp_limit_down', 'carrier': None, 'rule': 'scale', 'value': None,
     'notes': 'Ramp limit per snapshot'},

    # ========================================================================
    # OPTIONAL: EXAMPLES OF OTHER RULES
    # ========================================================================

    # Example: Use max for conservative renewable estimates
    # {'component': 'generators_t', 'attribute': 'p_max_pu', 'rule': 'max', 'value': None,
    #  'notes': 'Use maximum availability (more conservative for renewables)'},

    # Example: Set fixed value
    # {'component': 'generators', 'attribute': 'p_min_pu', 'rule': 'fixed', 'value': 0.0,
    #  'notes': 'Override all minimum power to 0'},

    # Example: Skip resampling for specific attribute
    # {'component': 'generators', 'attribute': 'efficiency', 'rule': 'skip', 'value': None,
    #  'notes': 'Do not modify efficiency during resampling'},
])

# Display the template
print("=" * 100)
print("RESAMPLE RULES TEMPLATE")
print("=" * 100)
print("\nThis template shows all recommended resampling rules.")
print("Add this as a new sheet named 'resample_rules' to your config_group.xlsx\n")
print(resample_rules.to_string(index=False))

# Save to Excel for easy import
output_file = 'resample_rules_template.xlsx'
resample_rules.to_excel(output_file, index=False, sheet_name='resample_rules')
print(f"\n{'=' * 100}")
print(f"Template saved to: {output_file}")
print("You can:")
print("  1. Open this file in Excel")
print("  2. Copy the 'resample_rules' sheet")
print("  3. Paste into your config_group.xlsx")
print("  4. Customize the rules as needed")
print("=" * 100)

print("\n" + "=" * 100)
print("RULE TYPES EXPLAINED:")
print("=" * 100)
print("""
Rule Type | Used For                    | Example
----------+-----------------------------+------------------------------------------
mean      | Time-series averaging       | Solar p_max_pu: average over 4 hours
sum       | Energy/flow totals          | Hydro inflow: sum over 4 hours
max       | Conservative estimates      | Renewable p_max_pu: peak availability
min       | Conservative minimums       | Rarely used
scale     | Per-snapshot rates          | Ramp limits: 0.2/h → 0.8/4h
fixed     | Override with value         | Set all p_min_pu to 0.0
skip      | Do not modify               | Leave attribute unchanged

CARRIER-SPECIFIC RULES:
-----------------------
carrier column can be used to apply different rules to different carriers.
- Leave carrier empty/None for default rule (applies to all)
- Specify carrier name to override for that carrier only

Examples:
  component='generators_t', attribute='p_max_pu', carrier=None, rule='mean'
  component='generators_t', attribute='p_max_pu', carrier='solar', rule='max'

  Result: Solar uses 'max', all other generators use 'mean'

  component='generators', attribute='p_min_pu', carrier=None, rule='skip'
  component='generators', attribute='p_min_pu', carrier='nuclear', rule='fixed', value=0.5

  Result: Nuclear p_min_pu set to 0.5, all others unchanged
""")
print("=" * 100)
