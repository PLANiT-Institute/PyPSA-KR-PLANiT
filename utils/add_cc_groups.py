"""
CLI utility to add combined cycle (CC) generator group names to generators.csv

For CC generators with names like "광양#1 GT" and "광양#1 ST",
this utility adds a "cc_group" column with the common part (e.g., "광양#1").

Usage:
    python utils/add_cc_groups.py --input data/2024/generators.csv --output data/2024/generators.csv
    python utils/add_cc_groups.py --input data/2024/generators.csv --output data/2024/generators.csv --backup

Optional:
    --backup                    # create backup as generators.csv.bak
    --encoding cp949            # force a specific input encoding
    --detect                    # try to detect encoding from bytes
    --output-encoding utf-8-sig # override output encoding (default utf-8-sig)
"""

import argparse
import pandas as pd
import sys
from pathlib import Path
import shutil

TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"]  # latin1 as fallback (reads any byte)


def identify_cc_group(name, gen_type):
    """
    Identify the CC group name for a generator.

    Parameters:
    -----------
    name : str
        Generator name (e.g., "광양#1 GT", "서인천 #5-8 GT 1")
    gen_type : str
        Generator type (should be "CC" or "복합" for combined cycle)

    Returns:
    --------
    str or None : CC group name (e.g., "광양#1", "서인천 #5-8") or None if not a CC generator
    """
    if pd.isna(name) or pd.isna(gen_type):
        return None

    # Check for combined cycle type (both English and Korean)
    gen_type_str = str(gen_type).strip()
    if gen_type_str not in ["CC", "복합"]:
        return None

    name_str = str(name).strip()

    # Pattern 1: "name GT/ST_number" (e.g., "서인천 #5~8 GT_1")
    # Remove " GT_number" or " ST_number" to get group name
    import re
    pattern1 = re.match(r'^(.+)\s+(GT|ST)_\d+$', name_str)
    if pattern1:
        return pattern1.group(1)

    # Pattern 2: "name GT/ST number" (e.g., "서인천 #5-8 GT 1")
    # Remove " GT number" or " ST number" to get group name
    pattern2 = re.match(r'^(.+)\s+(GT|ST)\s+\d+$', name_str)
    if pattern2:
        return pattern2.group(1)

    # Pattern 3: "name GT/ST" (e.g., "광양#1 GT")
    # Remove " GT" or " ST" to get group name
    if name_str.endswith(" GT") or name_str.endswith(" ST"):
        return name_str.rsplit(" ", 1)[0]

    return None


def detect_encoding(path: Path) -> str | None:
    try:
        from charset_normalizer import from_path
        res = from_path(str(path)).best()
        if res and res.encoding:
            return res.encoding
    except Exception:
        pass
    return None


def read_csv_safely(path: Path, forced_encoding: str | None, do_detect: bool) -> tuple[pd.DataFrame, str]:
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


def add_cc_groups(df):
    """
    Add cc_group column to generators dataframe.

    Parameters:
    -----------
    df : pd.DataFrame
        Generators dataframe

    Returns:
    --------
    pd.DataFrame : Modified dataframe with cc_group column
    """
    df = df.copy()

    # Add cc_group column
    df['cc_group'] = df.apply(
        lambda row: identify_cc_group(row['name'], row['type']),
        axis=1
    )

    return df


def main():
    parser = argparse.ArgumentParser(description="Add CC group column to generators CSV")
    parser.add_argument("--input", "-i", required=True, help="Input generators CSV file path")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file path")
    parser.add_argument("--backup", action="store_true", help="Create backup file (.bak) before modifying")
    parser.add_argument("--encoding", help="Force input encoding (e.g., cp949, utf-8, utf-8-sig)")
    parser.add_argument("--detect", action="store_true", help="Attempt to detect input encoding from bytes")
    parser.add_argument("--output-encoding", default="utf-8-sig",
                        help="Output encoding (default: utf-8-sig; good for Excel)")

    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[error] Input file not found: {args.input}")
        sys.exit(1)

    # Create backup if requested
    if args.backup:
        backup_path = Path(str(in_path) + ".bak")
        print(f"[info] Creating backup: {backup_path}")
        shutil.copy2(in_path, backup_path)

    print(f"[info] Loading: {args.input}")
    df, used_enc = read_csv_safely(in_path, args.encoding, args.detect)
    print(f"[info] Loaded {len(df)} rows; columns: {list(df.columns)}")

    # Check required columns
    if 'name' not in df.columns or 'type' not in df.columns:
        print("[error] 'name' and 'type' columns required in input CSV")
        sys.exit(1)

    # Add cc_group column
    result_df = add_cc_groups(df)

    # Print summary
    cc_count = result_df['cc_group'].notna().sum()
    unique_groups = result_df['cc_group'].dropna().nunique()
    print(f"[info] Found {cc_count} CC generators in {unique_groups} groups")

    # Print example groups
    if unique_groups > 0:
        print("[info] Example CC groups:")
        for group in result_df['cc_group'].dropna().unique()[:5]:
            generators = result_df[result_df['cc_group'] == group]['name'].tolist()
            print(f"  {group}: {generators}")

    # Save output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    enc_out = args.output_encoding
    print(f"[info] Saving: {args.output} (encoding={enc_out})")
    result_df.to_csv(out_path, index=False, encoding=enc_out)
    print(f"[done] Wrote {len(result_df)} rows. (input_encoding={used_enc}, output_encoding={enc_out})")


if __name__ == "__main__":
    main()
