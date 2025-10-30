#!/usr/bin/env python3
"""
Reverse Geocoding Utility
Add region information (country, province, city, county, etc.) to CSV files with coordinates.

Usage:
    python reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv
    python reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv --x-col lon --y-col lat
"""

import argparse
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
import time


class ReverseGeocoder:
    """Reverse geocode coordinates to get region information."""

    def __init__(self, cache_file='cache/reverse_geocode_cache.json', user_agent='pypsa_reverse_geocoder', language='en', timeout=1, province_mapping=None):
        """
        Initialize reverse geocoder with caching.

        Parameters:
        -----------
        cache_file : str
            Path to cache file (default: cache/reverse_geocode_cache.json)
        user_agent : str
            User agent for Nominatim API
        language : str
            Language for region names: 'en' (English) or 'ko' (Korean)
        timeout : int
            Request timeout in seconds (default: 1)
        province_mapping : dict, optional
            Province mapping dictionary to standardize region_1 names.
            If provided, will map region_1 to standard short names.
        """
        self.cache_file = cache_file
        self.language = language
        self.timeout = timeout
        self.province_mapping = province_mapping

        # Create cache directory if needed
        cache_dir = Path(cache_file).parent
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True)
            print(f"Created cache directory: {cache_dir}")

        self.cache = self._load_cache()

        # Initialize geocoder with specified timeout
        self.geolocator = Nominatim(user_agent=user_agent, timeout=self.timeout)
        # Rate limiter: 1 request per second for Nominatim
        self.reverse = RateLimiter(self.geolocator.reverse, min_delay_seconds=1)

    def _load_cache(self):
        """Load cache from file."""
        if Path(self.cache_file).exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _infer_province_from_city(self, city_name):
        """
        Try to infer province from city name when API doesn't provide province.
        This is a fallback mechanism for Korean locations.

        Parameters:
        -----------
        city_name : str
            City name from geocoding

        Returns:
        --------
        str : Inferred province short name, or empty if cannot infer
        """
        if not city_name or not self.province_mapping:
            return ''

        # Major Korean cities and their provinces
        city_to_province = {
            # Gyeonggi cities
            '수원시': '경기', 'Suwon': '경기',
            '성남시': '경기', 'Seongnam': '경기',
            '고양시': '경기', 'Goyang': '경기',
            '용인시': '경기', 'Yongin': '경기',
            '부천시': '경기', 'Bucheon': '경기',
            '안산시': '경기', 'Ansan': '경기',
            '안양시': '경기', 'Anyang': '경기',
            '남양주시': '경기', 'Namyangju': '경기',
            '화성시': '경기', 'Hwaseong': '경기',
            '평택시': '경기', 'Pyeongtaek': '경기',
            '의정부시': '경기', 'Uijeongbu': '경기',
            '시흥시': '경기', 'Siheung': '경기',
            '파주시': '경기', 'Paju': '경기',
            '김포시': '경기', 'Gimpo': '경기',
            '광명시': '경기', 'Gwangmyeong': '경기',
            '광주시': '경기', 'Gwangju': '경기',  # Note: different from Gwangju Metropolitan City
            '군포시': '경기', 'Gunpo': '경기',
            '하남시': '경기', 'Hanam': '경기',
            '오산시': '경기', 'Osan': '경기',
            '양주시': '경기', 'Yangju': '경기',
            '이천시': '경기', 'Icheon': '경기',
            '안성시': '경기', 'Anseong': '경기',
            '구리시': '경기', 'Guri': '경기',
            '포천시': '경기', 'Pocheon': '경기',
            '의왕시': '경기', 'Uiwang': '경기',
            '양평군': '경기', 'Yangpyeong': '경기',
            '여주시': '경기', 'Yeoju': '경기',
            '동두천시': '경기', 'Dongducheon': '경기',
            '가평군': '경기', 'Gapyeong': '경기',
            '과천시': '경기', 'Gwacheon': '경기',
            '연천군': '경기', 'Yeoncheon': '경기',

            # Gangwon cities
            '춘천시': '강원', 'Chuncheon': '강원',
            '원주시': '강원', 'Wonju': '강원',
            '강릉시': '강원', 'Gangneung': '강원',
            '동해시': '강원', 'Donghae': '강원',
            '태백시': '강원', 'Taebaek': '강원',
            '속초시': '강원', 'Sokcho': '강원',
            '삼척시': '강원', 'Samcheok': '강원',

            # Add more as needed...
        }

        city_str = str(city_name).strip()
        if city_str in city_to_province:
            province_short = city_to_province[city_str]
            # Return standardized version
            if province_short in self.province_mapping:
                return self.province_mapping[province_short]

        return ''

    def _standardize_province(self, province_name):
        """
        Standardize province name using province mapping.

        Parameters:
        -----------
        province_name : str
            Raw province name from geocoding

        Returns:
        --------
        str : Standardized province name, or original if no mapping found
        """
        if not self.province_mapping or not province_name:
            return province_name

        # Try to find a match in the mapping
        province_str = str(province_name).strip()

        # Direct match
        if province_str in self.province_mapping:
            return self.province_mapping[province_str]

        # Try partial matches for cases like "Gangwon State" -> "강원"
        # Remove common suffixes
        for suffix in [' State', ' Province', ' Metropolitan City', ' Special City',
                      '특별자치도', '광역시', '특별시', '도', '시']:
            if province_str.endswith(suffix):
                cleaned = province_str[:-len(suffix)].strip()
                if cleaned in self.province_mapping:
                    return self.province_mapping[cleaned]

        # Try English to Korean mapping
        english_to_korean = {
            'Seoul': '서울',
            'Busan': '부산',
            'Daegu': '대구',
            'Incheon': '인천',
            'Gwangju': '광주',
            'Daejeon': '대전',
            'Ulsan': '울산',
            'Sejong': '세종',
            'Gyeonggi': '경기',
            'Gangwon': '강원',
            'North Chungcheong': '충북',
            'South Chungcheong': '충남',
            'North Jeolla': '전북',
            'South Jeolla': '전남',
            'North Gyeongsang': '경북',
            'South Gyeongsang': '경남',
            'Jeju': '제주'
        }

        # Try English name match
        for eng, kor in english_to_korean.items():
            if province_str == eng or province_str.startswith(eng + ' '):
                if kor in self.province_mapping:
                    return self.province_mapping[kor]

        # If no match found, return original
        return province_name

    def reverse_geocode(self, x, y):
        """
        Reverse geocode coordinates to get address components.

        Parameters:
        -----------
        x : float
            Longitude
        y : float
            Latitude

        Returns:
        --------
        dict : Dictionary with address components, or empty dict if failed
            Keys: country, country_code, state, province, city, county,
                  town, village, suburb, postcode
        """
        if pd.isna(x) or pd.isna(y):
            return {}

        # Create cache key (include language)
        cache_key = f"{y:.6f},{x:.6f}_{self.language}"

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Reverse geocode with specified language and timeout
            location = self.reverse((y, x), language=self.language, timeout=self.timeout)

            if not location or not location.raw.get('address'):
                print(f"  Warning: No address found for ({y:.4f}, {x:.4f})")
                self.cache[cache_key] = {}
                return {}

            # Extract address components
            address = location.raw['address']

            # Determine level 1 (province/state) - must be province-level only
            # Priority: state > province > region
            level1_raw = (address.get('state') or
                         address.get('province') or
                         address.get('region') or '')

            # Special cities (Seoul, Busan, etc.) in Korea are considered province-level
            special_cities = ['Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon', 'Ulsan', 'Sejong',
                            '서울', '서울특별시', '부산', '부산광역시', '대구', '대구광역시',
                            '인천', '인천광역시', '광주', '광주광역시', '대전', '대전광역시',
                            '울산', '울산광역시', '세종', '세종특별자치시']

            # If no state/province/region found, check if city is a special city
            if not level1_raw:
                city = address.get('city', '')
                # Only use city as level1 if it's a special administrative city
                if city in special_cities or any(city.startswith(sc) for sc in special_cities if sc):
                    level1_raw = city
                else:
                    # Try to infer province from city name (fallback mechanism)
                    inferred_province = self._infer_province_from_city(city)
                    if inferred_province:
                        print(f"  Info - Inferred province '{inferred_province}' from city '{city}'")
                        level1_raw = inferred_province

            # Try to standardize province name using mapping
            level1 = ''
            if level1_raw:
                # Check if level1_raw is already a valid province (exists in mapping as key)
                if self.province_mapping and level1_raw in self.province_mapping:
                    # It's already a valid province name (short or official)
                    level1 = self.province_mapping[level1_raw]
                else:
                    # Try to standardize using the mapping
                    level1 = self._standardize_province(level1_raw)
                    # If standardization didn't change the value and mapping exists,
                    # it means we couldn't find a match in the mapping
                    if self.province_mapping and level1 == level1_raw:
                        # Check if it looks like a province-level entity
                        if any(suffix in level1_raw for suffix in ['State', 'Province', '도', '특별시', '광역시', '특별자치도']):
                            # Keep it as is - it's clearly a province
                            pass
                        else:
                            # Not clearly a province and not in mapping - leave region_1 empty
                            level1 = ''
                            level1_raw = ''

            # Determine level 2 (county/city/district)
            # Strategy: region_1 = province level, region_2 = city/county/district level
            if not level1:
                # No province found - put city/county in region_2, leave region_1 empty
                level2 = (address.get('city') or
                         address.get('county') or
                         address.get('municipality') or
                         address.get('district') or
                         address.get('town') or
                         address.get('village') or '')
            elif address.get('city') in special_cities or any(sc in str(level1_raw) for sc in special_cities if sc):
                # Special city case: use district/suburb/county for level2
                level2 = (address.get('district') or
                         address.get('suburb') or
                         address.get('county') or
                         address.get('town') or '')
            else:
                # Regular province case: use city/county for level2
                level2 = (address.get('city') or
                         address.get('county') or
                         address.get('municipality') or
                         address.get('district') or
                         address.get('town') or '')

            # Build result with only 2 administrative levels
            result = {
                'region_1': level1,
                'region_2': level2
            }

            # Cache the result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            print(f"  Error reverse geocoding ({y:.4f}, {x:.4f}): {e}")
            self.cache[cache_key] = {}
            return {}

    def process_csv(self, input_file, output_file, x_column='x', y_column='y',
                    overwrite=False, language=None, dry_run=False):
        """
        Process CSV file to add region information.

        Parameters:
        -----------
        input_file : str or Path
            Path to input CSV file with coordinates
        output_file : str or Path
            Path to output CSV file
        x_column : str
            Name of longitude column (default: 'x')
        y_column : str
            Name of latitude column (default: 'y')
        overwrite : bool
            If True, overwrite existing region columns
        language : str, optional
            Language override ('en' or 'ko'). If None, uses instance language.
        dry_run : bool
            If True, process only first 10 rows for testing

        Returns:
        --------
        bool : True if successful, False otherwise
        """
        # Override language if specified
        if language:
            self.language = language
        input_file = Path(input_file)
        output_file = Path(output_file)

        if not input_file.exists():
            print(f"Error: File not found: {input_file}")
            return False

        try:
            # Read CSV
            print(f"\nReading: {input_file.name}")
            df = pd.read_csv(input_file, encoding='utf-8-sig')

            # Check if coordinate columns exist
            if x_column not in df.columns:
                print(f"Error: Column '{x_column}' not found")
                return False
            if y_column not in df.columns:
                print(f"Error: Column '{y_column}' not found")
                return False

            print(f"  Found {len(df)} rows")

            # Region columns to add (only 2 levels)
            region_cols = ['region_1', 'region_2']

            # Initialize columns if they don't exist (with string dtype to avoid warnings)
            for col in region_cols:
                if col not in df.columns or overwrite:
                    df[col] = ''
                # Ensure column is string type to avoid dtype warnings
                if col in df.columns:
                    df[col] = df[col].astype(str).replace('nan', '')

            # Find rows that need reverse geocoding
            if overwrite:
                needs_geocoding = df[[x_column, y_column]].notna().all(axis=1)
            else:
                # Skip rows that already have region info
                has_coords = df[[x_column, y_column]].notna().all(axis=1)
                # Check if region_1 column exists and has meaningful data
                if 'region_1' in df.columns:
                    # Consider empty or whitespace as "needs geocoding"
                    has_no_region = (
                        df['region_1'].isna() |
                        (df['region_1'].astype(str).str.strip() == '')
                    )
                    needs_geocoding = has_coords & has_no_region
                else:
                    # If region_1 column doesn't exist, geocode all rows with coords
                    needs_geocoding = has_coords

            rows_to_geocode = df[needs_geocoding]

            if len(rows_to_geocode) == 0:
                print("  All rows already have region info (use --overwrite to force)")
                print("  Creating output file with existing data...")
                # Still save the output file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"  Saved: {output_file}")
                return True

            # Limit to first 10 rows for dry run
            if dry_run:
                rows_to_geocode = rows_to_geocode.head(10)
                print(f"  DRY RUN MODE: Processing first 10 rows only")

            print(f"  Rows needing reverse geocoding: {len(rows_to_geocode)}")

            # Process each row
            geocoded_count = 0
            for idx, row in rows_to_geocode.iterrows():
                x = row[x_column]
                y = row[y_column]

                # Create cache key for checking
                cache_key = f"{y:.6f},{x:.6f}"

                if cache_key not in self.cache or not self.cache[cache_key]:
                    print(f"  Reverse geocoding ({geocoded_count + 1}/{len(rows_to_geocode)}): "
                          f"({y:.4f}, {x:.4f})")
                    geocoded_count += 1

                # Get region info
                region_info = self.reverse_geocode(x, y)

                # Update dataframe
                for col in region_cols:
                    if col in region_info:
                        df.at[idx, col] = region_info[col]

                # Save cache periodically
                if geocoded_count > 0 and geocoded_count % 10 == 0:
                    self._save_cache()

            # Count successful reverse geocodes
            success_count = (df['region_1'] != '').sum()
            print(f"  Successfully reverse geocoded: {success_count}/{len(df)} rows")

            # Save output file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"  Saved: {output_file}")

            # Save cache
            self._save_cache()
            print(f"  Cache saved: {self.cache_file}")

            return True

        except Exception as e:
            print(f"Error processing {input_file}: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Reverse geocode coordinates to get region information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv

  # Specify coordinate columns
  python reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv --x-col lon --y-col lat

  # Overwrite existing region info
  python reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv --overwrite

  # Use custom cache file
  python reverse_geocode.py --input data/networks/buses.csv --output data/networks/buses_geocoded.csv --cache-file cache/my_cache.json

Output columns added:
  - region_1: Administrative level 1 (province/state/city)
    Examples: "Gangwon State", "Gyeonggi", "Seoul", "강원도", "경기도", "서울특별시"
  - region_2: Administrative level 2 (county/city/district)
    Examples: "Taebaek-si", "Gapyeong-gun", "Gangnam-gu", "평창군", "가평군", "양천구"

Notes:
  - Uses Nominatim API (rate limited to 1 request/second)
  - Results are cached to avoid re-querying
  - Skips rows that already have country info (unless --overwrite)
        """
    )

    parser.add_argument('--input', required=True, help='Input CSV file with coordinates')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--x-col', default='x', help='Longitude column name (default: x)')
    parser.add_argument('--y-col', default='y', help='Latitude column name (default: y)')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing region columns')
    parser.add_argument('--cache-file', default='cache/reverse_geocode_cache.json',
                       help='Cache file path (default: cache/reverse_geocode_cache.json)')
    parser.add_argument('--language', default='en', choices=['en', 'ko'],
                       help='Language for region names: en (English) or ko (Korean)')
    parser.add_argument('--timeout', type=int, default=1,
                       help='API request timeout in seconds (default: 1)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Process only first 10 rows for testing')
    parser.add_argument('--province-mapping', default='data/others/province_mapping.csv',
                       help='Province mapping file to standardize region_1 names (default: data/others/province_mapping.csv)')

    args = parser.parse_args()

    # Load province mapping if file exists
    province_mapping = None
    if Path(args.province_mapping).exists():
        try:
            print(f"\nLoading province mapping from: {args.province_mapping}")
            import csv
            mapping_dict = {}
            with open(args.province_mapping, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    short = row['short'].strip()
                    official = row['official'].strip()
                    # Map both official -> short and short -> short
                    mapping_dict[official] = short
                    mapping_dict[short] = short
            province_mapping = mapping_dict
            print(f"  Loaded {len(mapping_dict)} province mapping entries")
        except Exception as e:
            print(f"  Warning: Could not load province mapping: {e}")
            print(f"  Continuing without province mapping...")

    # Create geocoder with province mapping
    geocoder = ReverseGeocoder(
        cache_file=args.cache_file,
        language=args.language,
        timeout=args.timeout,
        province_mapping=province_mapping
    )

    # Process file
    success = geocoder.process_csv(
        input_file=args.input,
        output_file=args.output,
        x_column=args.x_col,
        y_column=args.y_col,
        overwrite=args.overwrite,
        dry_run=args.dry_run
    )

    if success:
        print("\n✓ Reverse geocoding completed successfully!")
    else:
        print("\n✗ Reverse geocoding failed or skipped")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
