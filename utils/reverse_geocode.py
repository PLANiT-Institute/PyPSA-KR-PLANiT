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

    def __init__(self, cache_file='cache/reverse_geocode_cache.json', user_agent='pypsa_reverse_geocoder', language='en', timeout=1):
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
        """
        self.cache_file = cache_file
        self.language = language
        self.timeout = timeout

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

            # Determine level 1 (province/state)
            level1 = (address.get('province') or
                     address.get('state') or
                     address.get('region') or
                     address.get('city') or '')

            # Determine level 2 (county/city/district)
            level2 = (address.get('county') or
                     address.get('city') or
                     address.get('municipality') or
                     address.get('district') or
                     address.get('town') or '')

            # For special cities like Seoul (서울특별시), if level1 is the city,
            # use district/suburb as level2
            if level1 == address.get('city') and not level2:
                level2 = address.get('district') or address.get('suburb') or ''

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

    args = parser.parse_args()

    # Create geocoder
    geocoder = ReverseGeocoder(cache_file=args.cache_file, language=args.language, timeout=args.timeout)

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
