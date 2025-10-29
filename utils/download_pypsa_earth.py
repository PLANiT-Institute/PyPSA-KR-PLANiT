"""
PyPSA One-Click: Entry point for PyPSA network creation.
Handles user arguments and delegates to the midend backend.
"""

import sys
import argparse
import logging
from pathlib import Path

from libs.pypsa_earth_backend import (
    create_pypsa_network_with_earth,
    cleanup_temp_files
)


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='PyPSA One-Click: Create PyPSA networks from OSM data')
    parser.add_argument('country_code', help='2-letter ISO country code (e.g., KR, DE, US)')
    parser.add_argument('--voltage-min', type=int, default=220, help='Minimum voltage level in kV (default: 220)')
    parser.add_argument('--output-dir', default='./networks', help='Output directory (default: ./networks)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    print(f"🚀 Creating PyPSA network for {args.country_code.upper()} using PyPSA-Earth backend...")

    try:
        network_path = create_pypsa_network_with_earth(
            country_code=args.country_code,
            voltage_min=args.voltage_min,
            output_dir=args.output_dir
        )

        print(f"\n✅ PyPSA Network Created and exported to: {network_path}")
        print(f"   📁 Files available:")

        for csv_file in Path(network_path).glob('*.csv'):
            print(f"   - {csv_file.name}")

        import pandas as pd
        buses_df = pd.read_csv(Path(network_path) / 'buses.csv')
        lines_df = pd.read_csv(Path(network_path) / 'lines.csv')

        print(f"\n📊 Network Summary:")
        print(f"   🚌 Buses: {len(buses_df)}")
        print(f"   📊 Lines: {len(lines_df)}")
        print(f"   ⚡ Voltage levels: {buses_df.v_nom.value_counts().sort_index().to_dict()}")

        cleanup_temp_files()
        print("   🧹 Cleaned up temporary files")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()