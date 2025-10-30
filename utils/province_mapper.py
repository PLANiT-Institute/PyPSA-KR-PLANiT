"""
Province Name Mapper Utility

Maps province names in CSV files to official names using a mapping CSV file.
Supports both single file and directory processing with proper encoding detection.

Usage:
    python utils/province_mapper.py --mapping data/others/province_mapping.csv --input data/2024/generators.csv
    python utils/province_mapper.py --mapping data/others/province_mapping.csv --input data/2024/ --recursive
    python utils/province_mapper.py --mapping data/others/province_mapping.csv --input data/2024/generators.csv --backup

Options:
    --backup                    # create backup as .bak before modifying
    --encoding cp949            # force a specific input encoding
    --detect                    # try to detect encoding from bytes
    --output-encoding utf-8-sig # override output encoding (default utf-8-sig)
    --column province           # specify the column name to map (default: province)
    --recursive                 # process all CSV files in directory recursively
"""

import argparse
import pandas as pd
import sys
from pathlib import Path
import shutil

TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"]  # latin1 as fallback


def detect_encoding(path: Path) -> str | None:
    """Detect file encoding using charset_normalizer if available."""
    try:
        from charset_normalizer import from_path
        res = from_path(str(path)).best()
        if res and res.encoding:
            return res.encoding
    except Exception:
        pass
    return None


def read_csv_safely(path: Path, forced_encoding: str | None, do_detect: bool) -> tuple[pd.DataFrame, str]:
    """
    Read CSV file with encoding detection.

    Parameters:
    -----------
    path : Path
        Path to CSV file
    forced_encoding : str | None
        Force specific encoding
    do_detect : bool
        Try to detect encoding

    Returns:
    --------
    tuple[pd.DataFrame, str] : DataFrame and encoding used
    """
    encodings_to_try = []

    if forced_encoding:
        encodings_to_try = [forced_encoding]
        print(f"[info] Forcing input encoding: {forced_encoding}")
    else:
        if do_detect:
            enc = detect_encoding(path)
            if enc:
                print(f"[info] Detected encoding: {enc}")
                encodings_to_try = [enc]
        if not encodings_to_try:
            encodings_to_try = TRY_ENCODINGS

    last_err = None
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(path, low_memory=False, encoding=enc)
            print(f"[info] Read OK with encoding='{enc}'")
            return df, enc
        except UnicodeDecodeError as e:
            print(f"[warn] Failed with encoding='{enc}': {e}")
            last_err = e
        except Exception as e:
            print(f"[warn] Read error with encoding='{enc}': {e}")
            last_err = e

    print("[error] Unable to decode CSV with tried encodings:", encodings_to_try, file=sys.stderr)
    if last_err:
        raise last_err
    raise UnicodeDecodeError("unknown", b"", 0, 1, "decoding failed")


def load_province_mapping(mapping_file: Path, direction: str = "to_short", forced_encoding: str | None = None, do_detect: bool = False) -> dict:
    """
    Load province mapping from CSV file.

    Expected CSV format:
    short,official
    강원,강원특별자치도
    경기,경기도
    ...

    Parameters:
    -----------
    mapping_file : Path
        Path to mapping CSV file
    direction : str
        Mapping direction: "to_short" or "to_official"
    forced_encoding : str | None
        Force specific encoding
    do_detect : bool
        Try to detect encoding

    Returns:
    --------
    dict : Province name mapping based on direction
    """
    print(f"\n{'='*60}")
    print(f"Loading province mapping from: {mapping_file}")
    print(f"Direction: {direction}")
    print(f"{'='*60}")

    df, _ = read_csv_safely(mapping_file, forced_encoding, do_detect)

    if 'short' not in df.columns or 'official' not in df.columns:
        raise ValueError(f"Mapping file must have 'short' and 'official' columns. Found: {df.columns.tolist()}")

    # Create mapping based on direction
    mapping = {}

    if direction == "to_short":
        # Map official -> short
        for _, row in df.iterrows():
            short = str(row['short']).strip()
            official = str(row['official']).strip()
            mapping[official] = short
            # Also allow short -> short (in case already in short form)
            mapping[short] = short
        print(f"[info] Mapping direction: Official names → Short names")
    elif direction == "to_official":
        # Map short -> official
        for _, row in df.iterrows():
            short = str(row['short']).strip()
            official = str(row['official']).strip()
            mapping[short] = official
            # Also allow official -> official (in case already in official form)
            mapping[official] = official
        print(f"[info] Mapping direction: Short names → Official names")
    else:
        raise ValueError(f"Invalid direction: {direction}. Must be 'to_short' or 'to_official'")

    print(f"[info] Loaded {len(df)} province mappings")
    print(f"[info] Total mapping entries: {len(mapping)}")

    return mapping, df


def map_province_names(df: pd.DataFrame, mapping: dict, column: str = 'province') -> tuple[pd.DataFrame, list, int]:
    """
    Map province names in dataframe using mapping dictionary.

    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    mapping : dict
        Province name mapping
    column : str
        Column name to map (default: 'province')

    Returns:
    --------
    tuple[pd.DataFrame, list, int] : Modified dataframe, unmapped names, changed count
    """
    if column not in df.columns:
        print(f"[warn] Column '{column}' not found in dataframe. Columns: {df.columns.tolist()}")
        return df, [], 0

    df = df.copy()
    unmapped = []
    changed_count = 0

    # Map province names
    for idx, value in df[column].items():
        if pd.isna(value):
            continue

        value_str = str(value).strip()

        if value_str in mapping:
            new_value = mapping[value_str]
            if new_value != value_str:
                df.at[idx, column] = new_value
                changed_count += 1
        else:
            if value_str not in unmapped and value_str:  # Don't add empty strings
                unmapped.append(value_str)

    return df, unmapped, changed_count


def process_file(input_file: Path, mapping: dict, column: str, output_file: Path | None,
                 backup: bool, output_encoding: str, forced_encoding: str | None, do_detect: bool,
                 _direction: str = "to_short") -> tuple[int, list]:
    """
    Process a single CSV file.

    Parameters:
    -----------
    _direction : str
        Mapping direction (unused, for signature compatibility)

    Returns:
    --------
    tuple[int, list] : Number of changes made, list of unmapped province names
    """
    print(f"\n{'='*60}")
    print(f"Processing: {input_file}")
    print(f"{'='*60}")

    # Read input file
    df, _ = read_csv_safely(input_file, forced_encoding, do_detect)

    # Check if column exists
    if column not in df.columns:
        print(f"[warn] Column '{column}' not found. Skipping this file.")
        print(f"       Available columns: {df.columns.tolist()}")
        return 0, []

    # Map province names
    df_mapped, unmapped, changed_count = map_province_names(df, mapping, column)

    # Report results
    print(f"\n[info] Mapping results:")
    print(f"       - Rows processed: {len(df)}")
    print(f"       - Names changed: {changed_count}")
    print(f"       - Unmapped names found: {len(unmapped)}")

    if unmapped:
        print(f"\n[warn] Unmapped province names:")
        for name in sorted(unmapped):
            print(f"       - {name}")

    # Save if changes were made
    if changed_count > 0:
        output_path = output_file if output_file else input_file

        # Create backup if requested
        if backup and output_path == input_file:
            backup_path = Path(str(input_file) + '.bak')
            shutil.copy(input_file, backup_path)
            print(f"\n[info] Created backup: {backup_path}")

        # Save modified file
        df_mapped.to_csv(output_path, index=False, encoding=output_encoding)
        print(f"[info] Saved: {output_path}")
        print(f"[info] Output encoding: {output_encoding}")
    else:
        print(f"\n[info] No changes needed. File not modified.")

    return changed_count, unmapped


def process_directory(input_dir: Path, mapping: dict, column: str, recursive: bool,
                      backup: bool, output_encoding: str, forced_encoding: str | None, do_detect: bool,
                      _direction: str = "to_short") -> tuple[int, int, set]:
    """
    Process all CSV files in a directory.

    Parameters:
    -----------
    _direction : str
        Mapping direction (unused, for signature compatibility)

    Returns:
    --------
    tuple[int, int, set] : Total files processed, total changes, set of all unmapped names
    """
    pattern = "**/*.csv" if recursive else "*.csv"
    csv_files = list(input_dir.glob(pattern))

    if not csv_files:
        print(f"[warn] No CSV files found in {input_dir}")
        return 0, 0, set()

    print(f"\n{'='*60}")
    print(f"Found {len(csv_files)} CSV file(s) to process")
    print(f"{'='*60}")

    total_changes = 0
    all_unmapped = set()

    for csv_file in csv_files:
        try:
            changes, unmapped = process_file(
                csv_file, mapping, column, None, backup,
                output_encoding, forced_encoding, do_detect, _direction
            )
            total_changes += changes
            all_unmapped.update(unmapped)
        except Exception as e:
            print(f"\n[error] Failed to process {csv_file}: {e}")
            import traceback
            traceback.print_exc()

    return len(csv_files), total_changes, all_unmapped


def main():
    parser = argparse.ArgumentParser(
        description="Map province names in CSV files to official names",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Map provinces in a single file
  python province_mapper.py --mapping data/others/province_mapping.csv --input data/2024/generators.csv

  # Map provinces in all CSV files in a directory
  python province_mapper.py --mapping data/others/province_mapping.csv --input data/2024/

  # Map with backup and custom column name
  python province_mapper.py --mapping data/others/province_mapping.csv --input data/2024/generators.csv --backup --column region
        """
    )

    parser.add_argument("--mapping", "-m", required=True, help="Path to province mapping CSV file")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file or directory")
    parser.add_argument("--output", "-o", help="Output CSV file (only for single file mode)")
    parser.add_argument("--direction", choices=["to_short", "to_official"], default="to_short",
                       help="Mapping direction: to_short (default) or to_official")
    parser.add_argument("--column", "-c", default="province", help="Column name to map (default: province)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process directory recursively")
    parser.add_argument("--backup", "-b", action="store_true", help="Create backup file (.bak) before modifying")
    parser.add_argument("--encoding", "-e", help="Force input encoding (e.g., cp949, utf-8, utf-8-sig)")
    parser.add_argument("--detect", "-d", action="store_true", help="Attempt to detect input encoding from bytes")
    parser.add_argument("--output-encoding", default="utf-8-sig",
                       help="Output file encoding (default: utf-8-sig)")

    args = parser.parse_args()

    # Validate paths
    mapping_path = Path(args.mapping)
    if not mapping_path.exists():
        print(f"[error] Mapping file not found: {mapping_path}", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[error] Input path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load mapping
    try:
        mapping, _mapping_df = load_province_mapping(mapping_path, args.direction, args.encoding, args.detect)
    except Exception as e:
        print(f"[error] Failed to load mapping file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Process input
    try:
        if input_path.is_file():
            # Single file mode
            output_path = Path(args.output) if args.output else None
            changes, unmapped = process_file(
                input_path, mapping, args.column, output_path,
                args.backup, args.output_encoding, args.encoding, args.detect, args.direction
            )

            print(f"\n{'='*60}")
            print(f"SUMMARY")
            print(f"{'='*60}")
            print(f"Total changes: {changes}")
            if unmapped:
                print(f"Unmapped names: {len(unmapped)}")
                print(f"\nAction required: Add these to mapping file:")
                for name in sorted(unmapped):
                    print(f"  {name},<official_name>")
            else:
                print(f"All province names successfully mapped!")

        elif input_path.is_dir():
            # Directory mode
            if args.output:
                print(f"[warn] --output ignored in directory mode", file=sys.stderr)

            files_processed, total_changes, all_unmapped = process_directory(
                input_path, mapping, args.column, args.recursive,
                args.backup, args.output_encoding, args.encoding, args.detect, args.direction
            )

            print(f"\n{'='*60}")
            print(f"SUMMARY")
            print(f"{'='*60}")
            print(f"Files processed: {files_processed}")
            print(f"Total changes: {total_changes}")
            if all_unmapped:
                print(f"Unmapped names: {len(all_unmapped)}")
                print(f"\nAction required: Add these to mapping file:")
                for name in sorted(all_unmapped):
                    print(f"  {name},<official_name>")
            else:
                print(f"All province names successfully mapped!")
        else:
            print(f"[error] Input path is neither file nor directory: {input_path}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"\n[error] Processing failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Done!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
