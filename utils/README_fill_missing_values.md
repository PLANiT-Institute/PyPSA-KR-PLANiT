# Fill Missing Values Utility

A comprehensive utility to intelligently fill missing values in CSV files using various imputation strategies.

## Problem Statement

When working with power system data (e.g., generators.csv), you often encounter missing values in important columns like `capital_cost`. Simply dropping these rows loses valuable data, while naive filling (e.g., with zero or overall mean) ignores important patterns in the data.

### Example Problem

In `generators.csv`, capital costs are missing for ~65% of generators, but we have values for some. The capital cost depends on:
- **Year** (build_year): Older plants vs newer plants have different costs
- **Type** (type): Steam turbines (ST) vs gas turbines (GT) vs renewables
- **Carrier** (carrier): Coal, natural gas, bio, etc.

**Issue**: Naive imputation can produce **negative values**, which doesn't make physical sense for capital costs!

## Solution Approaches

### 1. Regression-Based Imputation (Recommended)

Uses linear regression to predict missing values based on grouping variables.

**Pros:**
- Captures relationships between variables
- Most accurate when patterns exist
- Handles continuous predictors well

**Cons:**
- Can produce negative values (need constraint)
- Requires sufficient data in groups
- More complex

**When to use:** When you have enough data and believe relationships exist between variables

```bash
python utils/fill_missing_values.py \
    data/Singlenode2024/generators.csv \
    capital_cost \
    --group build_year type carrier \
    --method regression \
    --output generators_filled.csv
```

### 2. Group Mean/Median (Simple & Robust)

Fills missing values with the mean or median of similar groups.

**Pros:**
- Simple and interpretable
- Robust to outliers (median)
- Always produces sensible values
- Fast

**Cons:**
- Doesn't capture trends (e.g., costs decreasing over time)
- May not work if group is too small

**When to use:** When you want a simple, reliable approach or when regression fails

```bash
python utils/fill_missing_values.py \
    data/Singlenode2024/generators.csv \
    capital_cost \
    --group build_year type carrier \
    --method group_mean \
    --output generators_filled.csv
```

### 3. Forward/Backward Fill

Fills missing values by propagating the last known value forward (or first known value backward) within groups.

**Pros:**
- Preserves exact values from data
- Good for time series

**Cons:**
- Assumes value doesn't change much
- Not suitable for irregular patterns

**When to use:** When data is sorted and you expect continuity

```bash
python utils/fill_missing_values.py \
    data/Singlenode2024/generators.csv \
    capital_cost \
    --group build_year type carrier \
    --method forward_fill \
    --output generators_filled.csv
```

## Best Practice Recommendations

### For Capital Cost (or any cost/price data):

1. **Try regression first** with `--method regression`
2. **Use non-negative constraint** (default behavior) to prevent negative values
3. **Group by meaningful variables**: `build_year`, `type`, `carrier`
4. **Fallback to group mean**: If regression fails (not enough data), the tool automatically falls back to group mean
5. **Validate results**: Check the filled values make sense (min, max, mean)

### Recommended Command:

```bash
python utils/fill_missing_values.py \
    data/Singlenode2024/generators.csv \
    capital_cost \
    --group build_year type carrier \
    --method regression \
    --output generators_filled.csv
```

This will:
- ✅ Use regression within (year, type, carrier) groups
- ✅ Ensure no negative values (non-negative constraint)
- ✅ Fall back to group mean if regression fails
- ✅ Fall back to overall mean if group has no data
- ✅ Create backup of original file

## Usage

### Command Line

```bash
# Basic usage
python utils/fill_missing_values.py INPUT.csv TARGET_COLUMN --group COL1 COL2 ...

# Full options
python utils/fill_missing_values.py INPUT.csv TARGET_COLUMN \
    --group COL1 COL2 COL3 \
    --method {regression|group_mean|group_median|forward_fill|backward_fill} \
    --predictors COL1 COL2 \  # Optional, for regression
    --output OUTPUT.csv \
    --allow-negative \  # Allow negative values
    --no-backup \  # Don't create backup
    --quiet  # Less verbose output
```

### Python API

```python
from fill_missing_values import MissingValueFiller

# Create filler
filler = MissingValueFiller(verbose=True)

# Option 1: Process file
stats = filler.process_file(
    input_file='generators.csv',
    output_file='generators_filled.csv',
    target_column='capital_cost',
    grouping_columns=['build_year', 'type', 'carrier'],
    method='regression',
    non_negative=True,
    backup=True
)

# Option 2: Process DataFrame
import pandas as pd
df = pd.read_csv('generators.csv')
df_filled, stats = filler.fill_missing_values(
    df=df,
    target_column='capital_cost',
    grouping_columns=['build_year', 'type', 'carrier'],
    method='group_mean',
    non_negative=True
)
```

## Examples

See `examples/example_fill_missing_values.py` for detailed examples:

```bash
cd examples
python example_fill_missing_values.py
```

## Methods Comparison

| Method | Accuracy | Speed | Robustness | Handles Trends | Non-negative |
|--------|----------|-------|------------|----------------|--------------|
| **Regression** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ | With constraint |
| **Group Mean** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ✅ |
| **Group Median** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ✅ |
| **Forward Fill** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | Depends on data |
| **Backward Fill** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | Depends on data |

## Handling Edge Cases

The utility automatically handles several edge cases:

1. **Insufficient data for regression** → Falls back to group mean
2. **Group has no non-missing values** → Falls back to overall mean
3. **Categorical predictors** → Automatically encodes them for regression
4. **Negative predictions** → Clips to 0 when `non_negative=True`
5. **Missing predictors** → Handles gracefully with warning

## Output Statistics

The utility provides detailed statistics:

```python
stats = {
    'method': 'regression',
    'total_rows': 742,
    'originally_missing': 480,
    'filled_count': 480,
    'remaining_missing': 0,
    'predictors': ['build_year', 'type', 'carrier'],
    'r2_score': 0.1171  # For regression only
}
```

## Validation

After filling, validate your results:

```python
import pandas as pd

df_original = pd.read_csv('generators.csv')
df_filled = pd.read_csv('generators_filled.csv')

# Check missing values
print(f"Original missing: {df_original['capital_cost'].isna().sum()}")
print(f"After filling: {df_filled['capital_cost'].isna().sum()}")

# Check for negative values
print(f"Any negative: {(df_filled['capital_cost'] < 0).any()}")

# Check distribution
print(df_filled['capital_cost'].describe())
```

## Dependencies

- pandas
- numpy
- scikit-learn

Install with:
```bash
pip install pandas numpy scikit-learn
```

## Future Enhancements

Possible improvements:
- [ ] Multiple imputation (generate multiple filled datasets)
- [ ] More sophisticated models (Random Forest, KNN)
- [ ] Uncertainty quantification
- [ ] Interactive mode to review and approve filled values
- [ ] Support for multiple target columns at once
- [ ] Cross-validation to choose best method automatically

## Troubleshooting

### "X has 1 features, but LinearRegression is expecting 3 features"

This happens when some categorical values in the test set weren't in the training set. The utility automatically falls back to group mean in this case.

**Solution:** Use `--method group_mean` directly or check your grouping variables.

### "Not enough non-missing data for regression"

Your dataset has too few non-missing values for the chosen grouping.

**Solution:**
- Use fewer grouping columns (e.g., just `type` and `carrier`)
- Use `--method group_mean` instead

### Filled values are all the same

This means the groups didn't have enough data, so the overall mean was used.

**Solution:**
- Use broader groups (fewer grouping columns)
- Check if you have sufficient non-missing data

## References

- [Scikit-learn Imputation](https://scikit-learn.org/stable/modules/impute.html)
- [Pandas Missing Data](https://pandas.pydata.org/docs/user_guide/missing_data.html)
- Multiple Imputation: Rubin, D. B. (1987). Multiple Imputation for Nonresponse in Surveys

## License

This utility is part of the PyPSA Alternative project.
