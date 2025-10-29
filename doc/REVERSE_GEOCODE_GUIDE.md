# Reverse Geocoding Guide

Complete guide for using the reverse geocoding utility.

## What is Reverse Geocoding?

**Forward Geocoding:** Address text → Coordinates (x, y)
- Example: "Seoul, South Korea" → (126.9780, 37.5665)
- Use: `geocode_addresses.py`

**Reverse Geocoding:** Coordinates (x, y) → Region names
- Example: (126.9780, 37.5665) → "South Korea, Seoul, Seoul"
- Use: `reverse_geocode.py` ← This tool

## Quick Start

### Using GUI (Easiest)

1. Launch GUI:
   ```bash
   cd utils
   python utils_gui.py
   ```

2. Click "🔍 Reverse Geocode" tab

3. Configure:
   - **Input File:** Click "Browse" → Select your CSV with coordinates
   - **Output File:** Click "Browse" → Choose where to save results
   - **Coordinate Columns:** Default is x, y (change if needed)

4. Click "▶ Run Reverse Geocoding"

5. Watch progress in console at bottom

6. Done! Check your output file

### Using Command-Line

```bash
# Basic usage
python utils/reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv

# With custom columns
python utils/reverse_geocode.py --input mydata.csv --output mydata_geo.csv --x-col lon --y-col lat

# Force re-geocoding
python utils/reverse_geocode.py --input mydata.csv --output mydata_geo.csv --overwrite
```

## Input Requirements

Your CSV file must have:
- **Coordinate columns** with numeric values (longitude, latitude)
- Default column names: `x` (longitude), `y` (latitude)
- Can use custom names: `lon`/`lat`, `longitude`/`latitude`, etc.

**Example Input (`buses.csv`):**
```csv
name,x,y,v_nom
Bus_Seoul,126.9780,37.5665,380
Bus_Busan,129.0756,35.1796,380
Bus_Gwangju,126.9157,35.1595,220
```

## Output

The tool adds 13 region columns to your CSV:

| Column | Description | Example |
|--------|-------------|---------|
| `country` | Country name | South Korea |
| `country_code` | ISO 2-letter code | KR |
| `state` | State/province (admin 1) | Gyeonggi-do |
| `province` | Province name | Gyeonggi-do |
| `region` | Region name | Seoul Capital Area |
| `city` | City name | Seoul |
| `town` | Town name | Gangnam |
| `village` | Village name | - |
| `county` | County name | - |
| `municipality` | Municipality | Gangnam-gu |
| `suburb` | Suburb/neighborhood | Gangnam |
| `district` | District name | - |
| `postcode` | Postal code | 06000 |

**Example Output (`buses_geocoded.csv`):**
```csv
name,x,y,v_nom,country,country_code,province,city,municipality
Bus_Seoul,126.9780,37.5665,380,South Korea,KR,Seoul,Seoul,Jung-gu
Bus_Busan,129.0756,35.1796,380,South Korea,KR,Busan,Busan,Yeonje-gu
Bus_Gwangju,126.9157,35.1595,220,South Korea,KR,Gwangju,Gwangju,Dong-gu
```

## Common Use Cases

### Use Case 1: Add Region Info to Network Buses

You downloaded power network data and want to know which city each bus is in:

```bash
# Using default x, y columns
python utils/reverse_geocode.py \
    --input data/networks/KR/buses.csv \
    --output data/networks/KR/buses_with_regions.csv
```

### Use Case 2: Custom Coordinate Column Names

Your file uses `lon` and `lat` instead of `x` and `y`:

```bash
python utils/reverse_geocode.py \
    --input mydata.csv \
    --output mydata_geo.csv \
    --x-col lon \
    --y-col lat
```

### Use Case 3: Update Existing Region Data

You already ran it once but want to update with fresh data:

```bash
python utils/reverse_geocode.py \
    --input buses.csv \
    --output buses_updated.csv \
    --overwrite
```

## Options Explained

### --input (Required)
Path to input CSV file with coordinates.

### --output (Required)
Path to output CSV file. Will be created if doesn't exist.
- **Tip:** Use a different name than input to keep original
- **GUI:** Click "Browse" button to select location

### --x-col (Optional, default: 'x')
Name of the longitude column.
- Common names: `x`, `lon`, `longitude`, `lng`

### --y-col (Optional, default: 'y')
Name of the latitude column.
- Common names: `y`, `lat`, `latitude`

### --overwrite (Optional, default: False)
If set, re-geocode even if country column already has data.
- Use when: You want fresh/updated region data
- Skip when: You just want to add missing regions

### --cache-file (Optional)
Path to cache file. Default: `cache/reverse_geocode_cache.json`
- Cache speeds up repeated runs
- Stores API results to avoid re-querying

## Performance & Rate Limits

**Speed:**
- First run: ~1 second per location (API rate limit)
- Cached runs: Instant (reads from cache)

**Rate Limiting:**
- Uses Nominatim API: 1 request per second maximum
- This is enforced automatically
- For 418 buses: ~7 minutes first run, instant afterward

**Caching:**
- Results are cached by coordinates (6 decimal places)
- Cache location: `cache/reverse_geocode_cache.json`
- Survives between runs
- Shared between GUI and command-line

## Troubleshooting

### "All rows already have region info"

**Problem:** Tool says rows already have region info but no output file.

**Solution:** Fixed in latest version! Output file is now always created. If you see this:
- Check that output file was created
- If you want to re-geocode, use `--overwrite`

### "Column 'x' not found"

**Problem:** Your CSV uses different column names.

**Solution:** Use `--x-col` and `--y-col`:
```bash
python utils/reverse_geocode.py --input myfile.csv --output output.csv --x-col longitude --y-col latitude
```

### Slow Performance

**Problem:** Taking a long time to process.

**Solution:** This is normal for first run!
- Nominatim requires 1 second per location
- Subsequent runs use cache (fast!)
- Progress is shown in console

### Empty Region Columns

**Problem:** Regions are blank or empty.

**Possible causes:**
1. **Coordinates are invalid** (NaN, out of range)
   - Check your input data
2. **No internet connection** (needs Nominatim API)
   - Ensure you're online
3. **Coordinates in ocean/remote area**
   - Nominatim might not have data

**Debug:** Check console output for warnings/errors

### Different Results Than Expected

**Problem:** Got city name but expected province, etc.

**Explanation:** Different locations have different administrative structures:
- Urban areas: More detailed (city, suburb, district)
- Rural areas: Less detailed (county, village)
- Different countries: Different hierarchies

The tool returns **all available** levels. Use the columns you need.

## Advanced Usage

### Processing Multiple Files

```bash
# Process multiple network files
for file in data/networks/*/buses.csv; do
    output="${file%.csv}_geocoded.csv"
    python utils/reverse_geocode.py --input "$file" --output "$output"
done
```

### Selective Column Usage

After reverse geocoding, you might only need some columns:

```python
import pandas as pd

# Load geocoded data
df = pd.read_csv('buses_geocoded.csv')

# Keep only needed columns
df_slim = df[['name', 'x', 'y', 'country', 'province', 'city']]

# Save
df_slim.to_csv('buses_slim.csv', index=False)
```

### Combining with Network Analysis

```python
import pypsa
import pandas as pd

# Load network
network = pypsa.Network()
network.import_from_csv_folder("networks/KR")

# Load geocoded buses
buses_geo = pd.read_csv('networks/KR/buses_geocoded.csv')

# Merge region info into network
network.buses = network.buses.merge(
    buses_geo[['name', 'province', 'city']],
    on='name',
    how='left'
)

# Now analyze by region
generation_by_province = network.generators.groupby(
    network.generators.bus.map(network.buses.province)
)['p_nom'].sum()

print(generation_by_province)
```

## API Information

**Service Used:** Nominatim (OpenStreetMap geocoding)
- Free and open source
- No API key required
- Rate limit: 1 request per second
- Terms: https://operations.osmfoundation.org/policies/nominatim/

**Data Quality:**
- Generally excellent for populated areas
- May be less detailed for remote locations
- Accuracy depends on OpenStreetMap data quality

**Privacy:**
- Queries are sent to Nominatim servers
- Only coordinates are sent (not other data)
- Results are cached locally

## Tips & Best Practices

1. **Use cache effectively**
   - First run is slow, subsequent runs are fast
   - Don't delete cache unless needed
   - Cache is shared across runs

2. **Choose meaningful output names**
   ```bash
   # Good
   python utils/reverse_geocode.py --input buses.csv --output buses_with_regions.csv

   # Also good (date stamped)
   python utils/reverse_geocode.py --input buses.csv --output buses_geo_2024-10-29.csv
   ```

3. **Check results**
   - Always verify first few rows
   - Make sure region names make sense
   - Check for unexpected blanks

4. **Use appropriate columns**
   - For country-level analysis: use `country`
   - For regional: use `province` or `state`
   - For local: use `city` or `municipality`

5. **Backup before overwrite**
   ```bash
   # Make backup first
   cp buses_geocoded.csv buses_geocoded_backup.csv

   # Then overwrite
   python utils/reverse_geocode.py --input buses.csv --output buses_geocoded.csv --overwrite
   ```

## Examples by Region

### South Korea
- **country:** South Korea
- **country_code:** KR
- **province:** Seoul, Gyeonggi-do, Busan, etc.
- **city:** Seoul, Busan, Incheon, etc.
- **municipality:** Gang nam-gu, Jung-gu, etc.

### Germany
- **country:** Germany
- **country_code:** DE
- **state:** Bavaria, Berlin, Hamburg, etc.
- **city:** Munich, Berlin, Hamburg, etc.

### United States
- **country:** United States
- **country_code:** US
- **state:** California, Texas, New York, etc.
- **county:** Los Angeles County, etc.
- **city:** Los Angeles, New York, etc.

## FAQs

**Q: Do I need internet?**
A: Yes, for first run. Cached results don't need internet.

**Q: Does it work worldwide?**
A: Yes! Works for any country with OpenStreetMap data.

**Q: Can I geocode millions of points?**
A: Technically yes, but it will take time (1 per second). Consider batching or using paid services for large datasets.

**Q: What if coordinates are outside any region?**
A: Those rows will have empty region columns.

**Q: Can I use this commercially?**
A: Yes, following Nominatim usage policy (1 req/sec, no bulk).

**Q: How accurate are the regions?**
A: Depends on OpenStreetMap data. Generally very accurate for populated areas.

## Support

For issues:
- Check console output for error messages
- Verify coordinate column names match your CSV
- Ensure coordinates are valid (lat: -90 to 90, lon: -180 to 180)
- Check internet connection
- Review cache file if needed: `cache/reverse_geocode_cache.json`
