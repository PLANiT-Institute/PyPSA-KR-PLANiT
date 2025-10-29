"""
Geocoding utility to add x and y coordinates to CSV components.

This utility reads CSV files from a folder and adds x, y coordinate columns
by geocoding address fields (supports both Korean and English addresses).
"""

import pandas as pd
import os
import argparse
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import json
import numpy as np


class AddressGeocoder:
    """
    Geocodes addresses and adds x, y coordinates to CSV files.
    """

    def __init__(self, cache_file='cache/geocode_cache.json', user_agent='pypsa_geocoder'):
        """
        Initialize geocoder with caching support.

        Parameters:
        -----------
        cache_file : str
            Path to cache file for storing geocoded addresses (default: cache/geocode_cache.json)
        user_agent : str
            User agent string for Nominatim API
        """
        self.cache_file = cache_file

        # Create cache directory if it doesn't exist
        cache_dir = os.path.dirname(cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            print(f"Created cache directory: {cache_dir}")

        self.cache = self._load_cache()

        # Initialize geocoder with Nominatim (supports Korean addresses)
        self.geolocator = Nominatim(user_agent=user_agent)
        # Add rate limiting (1 request per second for Nominatim's policy)
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)

    def _load_cache(self):
        """Load geocoding cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Save geocoding cache to file."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def geocode_address(self, address):
        """
        Geocode a single address to get x (longitude) and y (latitude).

        Uses smart fallback strategy:
        1. Removes content in/after parentheses
        2. If geocoding fails, progressively removes smallest region (last part)
        3. If address contains 군 (county), tries replacing with 시 (city)
        4. Stops at province+city level (minimum 2 parts)

        Parameters:
        -----------
        address : str
            Address string (Korean or English)

        Returns:
        --------
        tuple : (x, y) or (None, None) if geocoding fails
        """
        if pd.isna(address) or address == '':
            return None, None

        # Check cache first (using original address as key)
        # Only use cache if it has valid coordinates (not None)
        if address in self.cache:
            cached = self.cache[address]
            x, y = cached.get('x'), cached.get('y')
            if x is not None and y is not None:
                return x, y
            # If cached value is None, continue to re-try geocoding

        try:
            # Clean address: remove content in/after parentheses
            clean_addr = address.split('(')[0].strip()

            # Try geocoding with progressively smaller regions
            # Stop at 2 parts minimum (province + city/county)
            addr_parts = clean_addr.split()

            for i in range(len(addr_parts), 1, -1):  # Stop at 2 parts (province + city)
                attempt_addr = ' '.join(addr_parts[:i])

                # Try with country suffix first
                location = self.geocode(attempt_addr + ', South Korea')

                if location:
                    x, y = location.longitude, location.latitude
                    # Save to cache using original address as key
                    self.cache[address] = {'x': x, 'y': y}
                    if i < len(addr_parts):
                        print(f"    → Geocoded using: '{attempt_addr}'")
                    return x, y

                # Try without country suffix
                location = self.geocode(attempt_addr)

                if location:
                    x, y = location.longitude, location.latitude
                    self.cache[address] = {'x': x, 'y': y}
                    if i < len(addr_parts):
                        print(f"    → Geocoded using: '{attempt_addr}'")
                    return x, y

                # If this attempt has 군 (county), try replacing with 시 (city)
                if '군' in attempt_addr:
                    # Replace all occurrences of 군 with 시
                    si_addr = attempt_addr.replace('군', '시')

                    # Try with country suffix
                    location = self.geocode(si_addr + ', South Korea')

                    if location:
                        x, y = location.longitude, location.latitude
                        self.cache[address] = {'x': x, 'y': y}
                        print(f"    → Geocoded using: '{si_addr}' (replaced 군→시)")
                        return x, y

                    # Try without country suffix
                    location = self.geocode(si_addr)

                    if location:
                        x, y = location.longitude, location.latitude
                        self.cache[address] = {'x': x, 'y': y}
                        print(f"    → Geocoded using: '{si_addr}' (replaced 군→시)")
                        return x, y

            # All attempts failed (even at province+city level)
            print(f"  Warning: Could not geocode address: {address} (tried down to province+city, including 군→시)")
            # DO NOT cache failures - allows retrying with improved logic later
            return None, None

        except Exception as e:
            print(f"  Error geocoding '{address}': {e}")
            # DO NOT cache errors - allows retrying later
            return None, None

    def check_duplicate_coordinates(self, df):
        """
        Check if all rows have the same coordinates.

        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with x and y columns

        Returns:
        --------
        bool : True if all non-null coordinates are identical
        """
        # Filter rows with valid coordinates
        valid_coords = df[['x', 'y']].dropna()

        if len(valid_coords) == 0:
            return False

        # Check if all x values are the same and all y values are the same
        return (valid_coords['x'].nunique() == 1) and (valid_coords['y'].nunique() == 1)

    def apply_jitter(self, df, jitter_km=1.0, seed=None):
        """
        Apply random jitter to coordinates to spread them around the original location.

        Jitter is applied as random offsets within a circle of radius jitter_km.
        Approximation: 1 km ≈ 0.009 degrees at mid-latitudes (like Korea).

        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with x and y columns
        jitter_km : float
            Radius in kilometers for jitter (default: 1.0 km)
        seed : int, optional
            Random seed for reproducibility

        Returns:
        --------
        pandas.DataFrame : DataFrame with jittered coordinates
        """
        if seed is not None:
            np.random.seed(seed)

        # Conversion factor: 1 km ≈ 0.009 degrees at mid-latitudes
        km_to_deg = 0.009
        jitter_deg = jitter_km * km_to_deg

        # Create a copy to avoid modifying original
        df_jittered = df.copy()

        # Get rows with valid coordinates
        valid_mask = df_jittered['x'].notna() & df_jittered['y'].notna()
        n_valid = valid_mask.sum()

        if n_valid == 0:
            return df_jittered

        # Generate random offsets within a circle of radius jitter_deg
        # Use polar coordinates for uniform distribution within circle
        angles = np.random.uniform(0, 2 * np.pi, n_valid)
        # Use sqrt for uniform distribution within circle
        radii = np.sqrt(np.random.uniform(0, 1, n_valid)) * jitter_deg

        # Convert to Cartesian offsets
        dx = radii * np.cos(angles)
        dy = radii * np.sin(angles)

        # Apply jitter to valid coordinates
        df_jittered.loc[valid_mask, 'x'] = df_jittered.loc[valid_mask, 'x'] + dx
        df_jittered.loc[valid_mask, 'y'] = df_jittered.loc[valid_mask, 'y'] + dy

        print(f"  Applied jitter: ±{jitter_km} km to {n_valid} locations")

        return df_jittered

    def process_csv(self, csv_path, address_column='address', overwrite=False, jitter=None):
        """
        Process a CSV file to add x and y coordinate columns.

        Parameters:
        -----------
        csv_path : str or Path
            Path to the CSV file
        address_column : str
            Name of the column containing addresses
        overwrite : bool
            If True, overwrite existing x and y columns
        jitter : str or float, optional
            If provided, apply jitter to coordinates. Can be:
            - Float: jitter radius in kilometers (e.g., 1.0 for 1 km)
            - String: 'jitter-X' format where X is km (e.g., 'jitter-5' for 5 km)
            - 'auto': prompt user if all coordinates are identical

        Returns:
        --------
        bool : True if processing was successful, False otherwise
        """
        csv_path = Path(csv_path)

        if not csv_path.exists():
            print(f"Error: File not found: {csv_path}")
            return False

        try:
            # Read CSV with proper encoding for Korean text
            # Use utf-8-sig to handle BOM if present
            df = pd.read_csv(csv_path, encoding='utf-8-sig')

            # Check if address column exists
            if address_column not in df.columns:
                print(f"  Skipping {csv_path.name}: No '{address_column}' column found")
                return False

            print(f"\nProcessing: {csv_path.name}")
            print(f"  Found {len(df)} rows")

            # Initialize x, y columns if they don't exist
            if 'x' not in df.columns:
                df['x'] = None
            if 'y' not in df.columns:
                df['y'] = None

            # Find addresses that need geocoding (missing x or y, or overwrite is True)
            if overwrite:
                # Overwrite mode: geocode all addresses
                needs_geocoding = df[address_column].notna()
            else:
                # Skip rows that already have both x and y coordinates
                needs_geocoding = df[address_column].notna() & (df['x'].isna() | df['y'].isna())

            addresses_to_geocode = df.loc[needs_geocoding, address_column]

            if len(addresses_to_geocode) == 0:
                print(f"  All rows already have coordinates (use --overwrite to force re-geocoding)")
                return False

            # Get unique addresses to geocode
            unique_addresses = addresses_to_geocode.unique()
            print(f"  Rows needing geocoding: {len(addresses_to_geocode)}")
            print(f"  Unique addresses to geocode: {len(unique_addresses)}")

            # Geocode each unique address
            geocoded_count = 0
            for i, address in enumerate(unique_addresses, 1):
                if address not in self.cache or self.cache[address]['x'] is None:
                    print(f"  Geocoding ({i}/{len(unique_addresses)}): {address[:50]}...")
                    self.geocode_address(address)
                    geocoded_count += 1

                    # Save cache periodically
                    if geocoded_count % 10 == 0:
                        self._save_cache()

            # Apply coordinates to dataframe for rows that need geocoding
            for idx in addresses_to_geocode.index:
                addr = df.loc[idx, address_column]
                if pd.notna(addr) and addr in self.cache:
                    df.loc[idx, 'x'] = self.cache[addr].get('x')
                    df.loc[idx, 'y'] = self.cache[addr].get('y')

            # Count successful geocodes
            success_count = df[['x', 'y']].notna().all(axis=1).sum()
            print(f"  Successfully geocoded: {success_count}/{len(df)} rows")

            # Check for duplicate coordinates and apply jitter if requested
            jitter_km = None

            if jitter is not None:
                # Parse jitter parameter
                if isinstance(jitter, str):
                    if jitter.lower() == 'auto':
                        # Check if all coordinates are identical
                        if self.check_duplicate_coordinates(df):
                            print("\n  WARNING: All geocoded locations are identical!")
                            response = input("  Do you want to add jitter? (yes/no or specify km, e.g., '5' for 5 km): ").strip().lower()

                            if response and response not in ['no', 'n']:
                                if response in ['yes', 'y']:
                                    jitter_km = 1.0  # Default 1 km
                                else:
                                    try:
                                        jitter_km = float(response)
                                    except ValueError:
                                        print(f"  Invalid jitter value: {response}. Using default 1 km.")
                                        jitter_km = 1.0
                    elif jitter.lower().startswith('jitter-'):
                        # Parse 'jitter-X' format
                        try:
                            jitter_km = float(jitter.split('-')[1])
                        except (IndexError, ValueError):
                            print(f"  Invalid jitter format: {jitter}. Expected 'jitter-X' where X is km.")
                    else:
                        # Try to parse as float
                        try:
                            jitter_km = float(jitter)
                        except ValueError:
                            print(f"  Invalid jitter value: {jitter}")
                elif isinstance(jitter, (int, float)):
                    jitter_km = float(jitter)

                # Apply jitter if requested
                if jitter_km is not None and jitter_km > 0:
                    df = self.apply_jitter(df, jitter_km=jitter_km)

            # Save updated CSV with proper encoding for Korean text
            # Use utf-8-sig for Excel compatibility (adds BOM)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  Saved updated file: {csv_path.name}")

            # Save cache
            self._save_cache()

            return True

        except Exception as e:
            print(f"Error processing {csv_path}: {e}")
            return False

    def process_folder(self, folder_path, address_column='address', overwrite=False, file_pattern='*.csv', jitter=None):
        """
        Process all CSV files in a folder.

        Parameters:
        -----------
        folder_path : str or Path
            Path to folder containing CSV files
        address_column : str
            Name of the column containing addresses
        overwrite : bool
            If True, overwrite existing x and y columns
        file_pattern : str
            Glob pattern for CSV files (default: '*.csv')
        jitter : str or float, optional
            Jitter parameter to pass to process_csv

        Returns:
        --------
        dict : Summary of processing results
        """
        folder_path = Path(folder_path)

        if not folder_path.exists():
            print(f"Error: Folder not found: {folder_path}")
            return {'success': 0, 'failed': 0, 'skipped': 0}

        csv_files = list(folder_path.glob(file_pattern))

        if not csv_files:
            print(f"No CSV files found in: {folder_path}")
            return {'success': 0, 'failed': 0, 'skipped': 0}

        print(f"Found {len(csv_files)} CSV file(s) in {folder_path}")

        results = {'success': 0, 'failed': 0, 'skipped': 0}

        for csv_file in csv_files:
            result = self.process_csv(csv_file, address_column, overwrite, jitter)
            if result:
                results['success'] += 1
            else:
                results['skipped'] += 1

        print("\n" + "="*60)
        print(f"Processing complete!")
        print(f"  Success: {results['success']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Cache file: {self.cache_file}")
        print("="*60)

        return results


def main():
    """Command-line interface for geocoding utility."""
    parser = argparse.ArgumentParser(
        description='Add x, y coordinates to CSV files by geocoding addresses.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Geocode using 'address' column (default)
  python geocode_addresses.py data/2024

  # Geocode using 'province' column instead
  python geocode_addresses.py data/2024 --address-column province

  # Geocode using any custom column
  python geocode_addresses.py data/2024 --address-column location

  # Overwrite existing x, y coordinates
  python geocode_addresses.py data/2024 --overwrite

  # Process specific CSV file pattern
  python geocode_addresses.py data/2024 --pattern "generators*.csv"

  # Use custom cache file location
  python geocode_addresses.py data/2024 --cache-file cache/my_cache.json

  # Automatically prompt for jitter if all locations are identical
  python geocode_addresses.py data/2024 --jitter auto

  # Apply 5 km jitter to all coordinates
  python geocode_addresses.py data/2024 --jitter jitter-5

  # Apply 1 km jitter (numeric format)
  python geocode_addresses.py data/2024 --jitter 1

Notes:
  - The utility will skip rows that already have both x and y coordinates
  - Fallback strategy removes smallest regions if geocoding fails
  - If address has 군 (county), automatically tries replacing with 시 (city)
  - Stops at province+city level (minimum 2 parts) to avoid province-only results
  - Content in/after parentheses is automatically ignored
  - Only successful geocoding results are cached (failures are NOT cached)
  - Jitter adds random offsets within specified radius to spread identical locations
        """
    )

    parser.add_argument('folder', type=str, help='Folder containing CSV files to process')
    parser.add_argument('--address-column', type=str, default='address',
                       help='Column name to use for geocoding (e.g., "address", "province", "location"). Default: address')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing x and y coordinates')
    parser.add_argument('--cache-file', type=str, default='cache/geocode_cache.json',
                       help='Path to cache file (default: cache/geocode_cache.json)')
    parser.add_argument('--pattern', type=str, default='*.csv',
                       help='File pattern to match (default: *.csv)')
    parser.add_argument('--jitter', type=str, default=None,
                       help='Add jitter to coordinates. Options: "auto" (prompt if all same), "jitter-X" (X km), or numeric value (km)')

    args = parser.parse_args()

    # Create geocoder
    geocoder = AddressGeocoder(cache_file=args.cache_file)

    # Process folder
    geocoder.process_folder(
        folder_path=args.folder,
        address_column=args.address_column,
        overwrite=args.overwrite,
        file_pattern=args.pattern,
        jitter=args.jitter
    )


if __name__ == '__main__':
    main()
