"""
CLI utility to expand mainland (육지) data to individual provinces.

Usage:
    python utils/expand_mainland_data.py --input data/add/monthly_t.csv --output data/add/monthly_t_expanded.csv
    python utils/expand_mainland_data.py --input data/add/snapshot_t.csv --output data/add/snapshot_t_expanded.csv

Optional:
    --encoding cp949            # force a specific input encoding
    --detect                    # try to detect encoding from bytes (charset-normalizer)
    --output-encoding utf-8-sig # override output encoding (default utf-8-sig)
"""
import argparse
from pathlib import Path
import sys

import pandas as pd

TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]  # practical order in KR environments


def normalize_region_value(val: object) -> str:
    """
    Normalize region values for robust matching:
    - ensure string
    - strip leading/trailing whitespace
    - collapse internal whitespace
    """
    if pd.isna(val):
        return ""
    s = str(val)
    s = s.strip()
    # collapse multiple spaces / unusual whitespace to single space
    s = " ".join(s.split())
    return s


def parse_mainland_labels(single_label: str | None, multi_labels: str | None) -> list[str]:
    """
    Return a list of labels to treat as mainland.
    - If multi_labels (comma-separated) is provided, use that.
    - Else, use single_label (default: '육지').
    The returned labels are normalized with normalize_region_value.
    """
    if multi_labels:
        labels = [normalize_region_value(x) for x in multi_labels.split(",")]
        return [x for x in labels if x]
    if single_label is None:
        single_label = "육지"
    return [normalize_region_value(single_label)]


def expand_mainland_to_provinces(df, mainland_label="육지"):
    # Normalize region values to make comparisons robust to stray spaces etc.
    if "region" not in df.columns:
        raise KeyError("'region' column not found in input DataFrame")
    df = df.copy()
    df["region"] = df["region"].map(normalize_region_value)

    mainland_provinces = [
        "강원특별자치도", "경기도", "경상남도", "경상북도", "광주광역시", "대구광역시", "대전광역시",
        "부산광역시", "서울특별시", "세종특별자치시", "울산광역시", "인천광역시", "전라남도",
        "전북특별자치도", "충청남도", "충청북도",
    ]

    # Support multiple labels separated by commas (handled in main) by accepting a list
    labels = mainland_label if isinstance(mainland_label, list) else [mainland_label]
    mainland_mask = df["region"].isin(labels)
    mainland_data = df[mainland_mask].copy()
    other_data = df[~mainland_mask].copy()

    if mainland_data.empty:
        print(f"[info] No mainland data found (region='{mainland_label}'). Nothing to expand.")
        return df

    print(f"[info] Found {len(mainland_data)} mainland rows; expanding to {len(mainland_provinces)} provinces.")
    expanded = []
    for province in mainland_provinces:
        tmp = mainland_data.copy()
        tmp["region"] = province
        expanded.append(tmp)

    out = pd.concat([other_data] + expanded, ignore_index=True)
    print(f"[info] Expanded {len(mainland_data)} → {len(mainland_data) * len(mainland_provinces)} rows.")
    return out


def detect_encoding(path: Path) -> str | None:
    try:
        # Prefer charset-normalizer (stdlib alternative to chardet in many envs)
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


def main():
    parser = argparse.ArgumentParser(description="Expand mainland (육지) data to individual provinces")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file path")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file path")
    parser.add_argument("--mainland-label", default="육지", help="Label for mainland data (default: 육지)")
    parser.add_argument("--mainland-labels", default=None,
                        help="Comma-separated list of labels treated as mainland (overrides --mainland-label). Example: '육지,본토,대한민국(육지)'")
    parser.add_argument("--list-regions", action="store_true",
                        help="List unique region values (after normalization) and exit without modifying data.")
    parser.add_argument("--encoding", help="Force input encoding (e.g., cp949, utf-8, utf-8-sig)")
    parser.add_argument("--detect", action="store_true", help="Attempt to detect input encoding from bytes")
    parser.add_argument("--output-encoding", default="utf-8-sig",
                        help="Output encoding (default: utf-8-sig; good for Excel)")

    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[error] Input file not found: {args.input}")
        sys.exit(1)

    print(f"[info] Loading: {args.input}")
    df, used_enc = read_csv_safely(in_path, args.encoding, args.detect)
    print(f"[info] Loaded {len(df)} rows; columns: {list(df.columns)}")

    # Normalize region for consistent behavior
    if "region" not in df.columns:
        print("[error] 'region' column not found in input CSV")
        sys.exit(1)
    df = df.copy()
    df["region"] = df["region"].map(normalize_region_value)

    if args.list_regions:
        unique_regions = sorted(set(df["region"].dropna().unique()))
        print("[info] Unique regions (normalized):")
        for r in unique_regions:
            print(" -", r)
        # exit early if only listing
        sys.exit(0)

    labels = parse_mainland_labels(args.mainland_label, args.mainland_labels)
    print(f"[info] Mainland labels in use (normalized): {labels}")

    expanded = expand_mainland_to_provinces(df, mainland_label=labels)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    enc_out = args.output_encoding
    print(f"[info] Saving: {args.output} (encoding={enc_out})")
    expanded.to_csv(out_path, index=False, encoding=enc_out)
    print(f"[done] Wrote {len(expanded)} rows. (input_encoding={used_enc}, output_encoding={enc_out})")


if __name__ == "__main__":
    main()