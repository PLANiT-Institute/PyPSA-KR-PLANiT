"""
Utility to merge combined cycle (CC) generators by their cc_group.

For each CC group, this creates a single merged generator that:
- Sums the p_nom (capacity) of all GT and ST units
- Uses other attribute values from the GT unit
- Keeps non-CC generators unchanged
"""

import pandas as pd
from pathlib import Path
import argparse
import sys
import shutil

TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"]


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


def merge_cc_by_group(df):
    """
    Merge CC generators by their cc_group.

    For each CC group:
    - Sum p_nom from all units (GT and ST)
    - Use other values from the GT unit (first GT found in the group)
    - Use the cc_group name as the new generator name

    Parameters:
    -----------
    df : pd.DataFrame
        Generators dataframe with cc_group column

    Returns:
    --------
    pd.DataFrame : Modified dataframe with CC groups merged
    """
    if 'cc_group' not in df.columns:
        print("[error] 'cc_group' column not found. Run add_cc_groups.py first.")
        return df

    df = df.copy()

    # Split into CC and non-CC generators
    cc_mask = df['cc_group'].notna()
    cc_generators = df[cc_mask].copy()
    non_cc_generators = df[~cc_mask].copy()

    if cc_generators.empty:
        print("[info] No CC generators found to merge.")
        return df

    # Group CC generators and merge
    merged_cc = []
    for group_name, group_df in cc_generators.groupby('cc_group'):
        # Find a GT unit to use as template (prefer GT over ST)
        gt_units = group_df[group_df['name'].str.contains('GT', na=False)]
        if not gt_units.empty:
            template = gt_units.iloc[0].copy()
        else:
            # Fallback to first unit if no GT found
            template = group_df.iloc[0].copy()

        # Sum the p_nom from all units in the group
        total_p_nom = group_df['p_nom'].sum()

        # Create merged generator
        merged = template.copy()
        merged['name'] = group_name  # Use group name as the new generator name
        merged['p_nom'] = total_p_nom  # Sum of all capacities
        merged['cc_group'] = group_name  # Keep cc_group for reference

        merged_cc.append(merged)

    # Convert list to dataframe
    merged_cc_df = pd.DataFrame(merged_cc)

    # Combine non-CC and merged CC generators
    result_df = pd.concat([non_cc_generators, merged_cc_df], ignore_index=True)

    print(f"[info] Merged {len(cc_generators)} CC generators into {len(merged_cc_df)} combined units")
    print(f"[info] Total generators: {len(df)} → {len(result_df)}")

    return result_df


def main():
    parser = argparse.ArgumentParser(description="Merge CC generators by their cc_group")
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
    if 'name' not in df.columns or 'p_nom' not in df.columns:
        print("[error] 'name' and 'p_nom' columns required in input CSV")
        sys.exit(1)

    # Merge CC groups
    result_df = merge_cc_by_group(df)

    # Print examples
    if 'cc_group' in result_df.columns:
        merged_cc = result_df[result_df['cc_group'].notna()]
        if not merged_cc.empty:
            print("\n[info] Example merged CC generators:")
            for idx, row in merged_cc.head(5).iterrows():
                print(f"  {row['name']}: p_nom={row['p_nom']}")

    # Save output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    enc_out = args.output_encoding
    print(f"\n[info] Saving: {args.output} (encoding={enc_out})")
    result_df.to_csv(out_path, index=False, encoding=enc_out)
    print(f"[done] Wrote {len(result_df)} rows. (input_encoding={used_enc}, output_encoding={enc_out})")


if __name__ == "__main__":
    main()
