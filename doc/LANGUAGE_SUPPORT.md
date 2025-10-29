# Language Support for Reverse Geocoding

The reverse geocoding utility now supports **both English and Korean** language output!

## Quick Start

### Using GUI

1. Launch GUI: `python utils/utils_gui.py`
2. Go to "🔍 Reverse Geocode" tab
3. Select language:
   - ⭕ **English** (default)
   - ⭕ **한국어 (Korean)**
4. Click "▶ Run Reverse Geocoding"

### Using Command-Line

```bash
# English (default)
python utils/reverse_geocode.py --input buses.csv --output buses_en.csv

# Korean
python utils/reverse_geocode.py --input buses.csv --output buses_ko.csv --language ko
```

## Output Examples

### English Output

```csv
name,x,y,country,country_code,province,city
Bus_Seoul,126.9780,37.5665,South Korea,KR,,Seoul
Bus_Busan,129.0756,35.1796,South Korea,KR,,Busan
Bus_Incheon,126.7052,37.4563,South Korea,KR,Incheon,Incheon
```

**Region Names (English):**
- Country: `South Korea`
- Province: `Gyeonggi-do`, `North Jeolla Province`
- City: `Seoul`, `Busan`, `Incheon`, `Suwon`
- Town/Suburb: `Gangnam`, `Myeong-dong`

### Korean Output (한국어)

```csv
name,x,y,country,country_code,province,city
Bus_Seoul,126.9780,37.5665,대한민국,KR,,서울특별시
Bus_Busan,129.0756,35.1796,대한민국,KR,,부산광역시
Bus_Incheon,126.7052,37.4563,대한민국,KR,인천광역시,인천광역시
```

**Region Names (Korean):**
- Country: `대한민국`
- Province: `경기도`, `전라북도`
- City: `서울특별시`, `부산광역시`, `인천광역시`, `수원시`
- Town/Suburb: `강남구`, `명동`

## Language Codes

| Code | Language | Example Output |
|------|----------|----------------|
| `en` | English | South Korea, Seoul, Gyeonggi-do |
| `ko` | Korean (한국어) | 대한민국, 서울특별시, 경기도 |

## Cache Behavior

**Important:** English and Korean use **separate caches**!

- English cache: `cache/reverse_geocode_cache.json` (entries with `_en`)
- Korean cache: `cache/reverse_geocode_cache.json` (entries with `_ko`)
- Same cache file, different keys per language
- This means you can switch languages and re-geocode without losing cached data

## Usage Examples

### Example 1: English Names for International Analysis

```bash
python utils/reverse_geocode.py \
    --input networks/KR/buses.csv \
    --output networks/KR/buses_en.csv \
    --language en
```

**Use when:**
- Creating reports in English
- International collaboration
- Publishing data globally

### Example 2: Korean Names for Domestic Analysis

```bash
python utils/reverse_geocode.py \
    --input networks/KR/buses.csv \
    --output networks/KR/buses_ko.csv \
    --language ko
```

**Use when:**
- Korean-language reports
- Domestic analysis
- Need official Korean names (행정구역명)

### Example 3: Generate Both Languages

```bash
# English version
python utils/reverse_geocode.py \
    --input buses.csv \
    --output buses_en.csv \
    --language en

# Korean version
python utils/reverse_geocode.py \
    --input buses.csv \
    --output buses_ko.csv \
    --language ko
```

## Regional Name Differences

### Seoul (서울)

| Level | English | Korean |
|-------|---------|--------|
| Country | South Korea | 대한민국 |
| City | Seoul | 서울특별시 |
| District | Gangnam-gu | 강남구 |
| Neighborhood | Gangnam | 강남 |

### Gyeonggi Province (경기도)

| Level | English | Korean |
|-------|---------|--------|
| Country | South Korea | 대한민국 |
| Province | Gyeonggi-do | 경기도 |
| City | Suwon | 수원시 |
| District | Yeongtong-gu | 영통구 |

### Busan (부산)

| Level | English | Korean |
|-------|---------|--------|
| Country | South Korea | 대한민국 |
| City | Busan | 부산광역시 |
| District | Haeundae-gu | 해운대구 |

## API Details

**How it works:**
- Uses Nominatim API with `language` parameter
- Nominatim returns names in requested language when available
- Falls back to default if translation unavailable

**Language parameter:**
- `language='en'` → Returns English names
- `language='ko'` → Returns Korean names (한국어)
- Other languages supported by Nominatim: `de`, `fr`, `ja`, etc.

## Common Questions

### Q: Can I get both languages in one file?

A: No, you need to run twice and merge:

```python
import pandas as pd

# Load both versions
df_en = pd.read_csv('buses_en.csv')
df_ko = pd.read_csv('buses_ko.csv')

# Rename Korean columns
df_ko_renamed = df_ko.rename(columns={
    'country': 'country_ko',
    'province': 'province_ko',
    'city': 'city_ko'
})

# Merge
df_both = df_en.merge(
    df_ko_renamed[['name', 'country_ko', 'province_ko', 'city_ko']],
    on='name'
)

df_both.to_csv('buses_bilingual.csv', index=False)
```

### Q: Which language should I use?

**Use English if:**
- Sharing data internationally
- English reports/publications
- Integrating with English-language systems

**Use Korean if:**
- Korean reports (국내 보고서)
- Official administrative names needed
- Domestic audience only

### Q: Are all regions translated?

A: Most are, but:
- Major cities/provinces: ✅ Always translated
- Small villages: ⚠️ May only have Korean names
- New areas: ⚠️ May not be in Nominatim yet

### Q: Does it work for other countries?

A: Yes! Language support works worldwide:

```bash
# German locations in German
python utils/reverse_geocode.py --input germany.csv --output germany_de.csv --language de

# Japanese locations in Japanese
python utils/reverse_geocode.py --input japan.csv --output japan_ja.csv --language ja
```

## Performance

**Speed is the same** for both languages:
- Same API calls
- Same rate limit (1 req/sec)
- Separate caches mean no conflicts

**First run:**
- English: ~1 sec per location
- Korean: ~1 sec per location

**Cached run:**
- Both: Instant

## GUI Screenshots

**Language Selection in GUI:**
```
Options
├─ ☑ Overwrite existing region info
└─ Language:
   ├─ ⭕ English
   └─ ⭕ 한국어 (Korean)
```

**Simple and easy to switch!**

## Tips

1. **Choose language first** before running - can't change after without re-running

2. **Cache is your friend** - Running same coordinates again is instant

3. **Bilingual datasets** - Run twice with different outputs if you need both

4. **Check results** - Some locations may have better data in one language

5. **Official names** - Korean (`ko`) gives official administrative names (행정구역명)

## Support

For other languages supported by Nominatim:
- German: `--language de`
- French: `--language fr`
- Japanese: `--language ja`
- Spanish: `--language es`
- Italian: `--language it`
- And more...

Check [Nominatim language support](https://nominatim.org/release-docs/latest/api/Reverse/) for full list.

## Summary

✅ **English** - International standard names
✅ **Korean (한국어)** - Official Korean names
✅ **Easy switching** - Radio button in GUI or `--language` flag
✅ **Separate caches** - No conflicts between languages
✅ **Works worldwide** - Not just Korea!

Choose the language that fits your analysis needs!
