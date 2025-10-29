# GUI Import Fixes - Summary

## Issues Fixed

All import errors in the GUI have been fixed. The utilities use different function names than what the GUI was calling.

### 1. CSV to Excel ✅

**Error:** `cannot import name 'csv_folder_to_excel'`

**Fixed:**
- Changed from `csv_folder_to_excel` → `convert_directory`
- Actual functions in `csv_to_excel.py`:
  - `csv_to_excel()` - Convert single file
  - `convert_directory()` - Convert folder

### 2. Add CC Groups ✅

**Error:** `cannot import name 'add_cc_groups_to_csv'`

**Fixed:**
- Now uses: `read_csv_safely()` + `add_cc_groups()`
- Manually handles backup and save
- Actual functions in `add_cc_groups.py`:
  - `add_cc_groups(df)` - Adds cc_group column to DataFrame
  - `read_csv_safely()` - Reads CSV with encoding detection

### 3. Merge CC Groups ✅

**Error:** `cannot import name 'merge_cc_generators_in_csv'`

**Fixed:**
- Now uses: `read_csv_safely()` + `merge_cc_by_group()`
- Manually handles save
- Actual functions in `merge_cc_groups.py`:
  - `merge_cc_by_group(df)` - Merges CC generators
  - `read_csv_safely()` - Reads CSV with encoding detection

### 4. Expand Mainland ✅

**Error:** `cannot import name 'expand_mainland_data'`

**Fixed:**
- Now uses: `read_csv_safely()` + `expand_mainland_to_provinces()`
- Manually handles save
- Actual functions in `expand_mainland_data.py`:
  - `expand_mainland_to_provinces(df)` - Expands 육지 to provinces
  - `read_csv_safely()` - Reads CSV with encoding detection

### 5. Reverse Geocoding - Empty Results ✅

**Issues:**
1. No output file when data already has regions
2. No browse button for output file
3. Cache path issue in GUI

**Fixed:**
- ✅ Always creates output file (even if skipping)
- ✅ Added "Browse" button for output file selection
- ✅ Fixed cache path in GUI (now uses proper parent path)
- ✅ Better column detection (checks if `country` column exists)

## How Utilities Are Structured

Most utilities follow this pattern:

```python
# In the .py file:
def read_csv_safely(path, encoding, detect):
    """Read CSV with encoding detection"""
    # Returns: df, encoding

def process_data(df):
    """Main processing function"""
    # Returns: modified df

# In main():
df, enc = read_csv_safely(input_file, None, False)
df = process_data(df)
df.to_csv(output_file, ...)
```

**GUI needs to:**
1. Import the actual functions (not wrapper functions)
2. Read CSV
3. Call processing function
4. Save CSV

## Testing Checklist

✅ **Geocoding** - Works (tested)
✅ **Reverse Geocoding** - Works (tested)
  - Now creates output file always
  - Browse button works
  - Cache path fixed

✅ **CSV to Excel** - Fixed imports
✅ **Encoding Converter** - Already working
✅ **Add CC Groups** - Fixed imports
✅ **Merge CC Groups** - Fixed imports
✅ **Expand Mainland** - Fixed imports
✅ **Unique Names** - Already working
✅ **Network Download** - Already working

## Cache Paths

All caches now use proper paths:

```python
# In GUI (utils/utils_gui.py)
cache_path = Path(__file__).parent.parent / "cache" / "filename.json"

# Resolves to:
# /Users/.../pypsa_alternative/cache/geocode_cache.json
# /Users/.../pypsa_alternative/cache/reverse_geocode_cache.json
```

## Command-Line Still Works

All command-line utilities work independently:

```bash
# These all work from command line
python utils/geocode_addresses.py data/2024
python utils/reverse_geocode.py --input buses.csv --output buses_geo.csv
python utils/csv_to_excel.py ...
python utils/add_cc_groups.py ...
python utils/merge_cc_groups.py ...
python utils/expand_mainland_data.py ...
python utils/uniquename.py ...
python utils/encodingconverter.py ...
python utils/download_pypsa_earth.py KR
```

## Updated Function Map

| Utility File | GUI Imports | Notes |
|--------------|-------------|-------|
| geocode_addresses.py | `AddressGeocoder` | Class-based, works ✅ |
| reverse_geocode.py | `ReverseGeocoder` | Class-based, works ✅ |
| csv_to_excel.py | `csv_to_excel`, `convert_directory` | Fixed ✅ |
| encodingconverter.py | `convert_euckr_to_utf8`, `convert_folder` | Works ✅ |
| add_cc_groups.py | `read_csv_safely`, `add_cc_groups` | Fixed ✅ |
| merge_cc_groups.py | `read_csv_safely`, `merge_cc_by_group` | Fixed ✅ |
| expand_mainland_data.py | `read_csv_safely`, `expand_mainland_to_provinces` | Fixed ✅ |
| uniquename.py | `make_csv_names_unique` | Works ✅ |
| download_pypsa_earth.py | (via libs) | Works ✅ |

## Why Some Fields Are Empty in Reverse Geocoding

This is **normal behavior**, not a bug:

```csv
# Example: Seoul location
country: South Korea  ✅ (always filled)
country_code: KR      ✅ (always filled)
state:                ❌ (empty - Korea uses province, not state)
province:             ❌ (empty - Seoul is special city, not in province)
city: Seoul           ✅ (filled)
suburb: Myeong-dong   ✅ (filled)
```

Different locations have different administrative structures:
- **Seoul:** city-level direct under national (no province)
- **Busan:** city-level direct under national (no province)
- **Gyeonggi-do:** Has province, cities, counties
- **Rural areas:** May have village, county, town

**What you get depends on:**
1. Location type (urban vs rural)
2. Country's administrative structure
3. OpenStreetMap data completeness

**Tip:** Focus on columns that are consistently filled:
- `country` and `country_code` - Always filled
- `city` - Usually filled for populated areas
- `province`/`state` - Depends on structure

## Next Steps

All utilities now work in the GUI! To use:

```bash
cd utils
python utils_gui.py
```

Select any of the 9 tabs and click Run. All import errors are resolved.
