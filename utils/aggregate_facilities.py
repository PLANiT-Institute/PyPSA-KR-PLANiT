"""
CLI and programmatic utility to aggregate generation facility data.

Usage:
    python utils/aggregate_facilities.py --input data/raw/generation_by_facility.xlsx --output data/aggregated_facilities.csv
    python utils/aggregate_facilities.py --input data/raw/generation_by_facility.csv --output data/aggregated_facilities.csv --filter market=중앙 carrier=wind,solar --group-by province carrier

Examples:
    # Aggregate by province and carrier (default), filter by market
    python utils/aggregate_facilities.py -i data/raw/generation_by_facility.xlsx -o output.csv --filter market=중앙

    # Aggregate by province only, filter by carrier
    python utils/aggregate_facilities.py -i data/raw/generation_by_facility.xlsx -o output.csv --filter carrier=wind,solar --group-by province

    # No filtering, aggregate by province, carrier, and market
    python utils/aggregate_facilities.py -i data/raw/generation_by_facility.xlsx -o output.csv --group-by province carrier market
"""
import argparse
from pathlib import Path
import sys
from typing import Dict, List, Optional

import pandas as pd


TRY_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]


def parse_filters(filter_args: List[str]) -> Dict[str, List[str]]:
    """
    Parse filter arguments in the format: column=value1,value2,value3

    Args:
        filter_args: List of strings like ["market=중앙", "carrier=wind,solar"]

    Returns:
        Dictionary mapping column names to list of values
    """
    filters = {}
    for arg in filter_args:
        if "=" not in arg:
            raise ValueError(f"Invalid filter format: {arg}. Expected format: column=value1,value2")

        column, values = arg.split("=", 1)
        column = column.strip()
        value_list = [v.strip() for v in values.split(",")]
        filters[column] = value_list

    return filters


def apply_filters(df: pd.DataFrame, filters: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Apply filters to dataframe.

    Args:
        df: Input dataframe
        filters: Dictionary mapping column names to list of acceptable values

    Returns:
        Filtered dataframe
    """
    if not filters:
        return df

    result = df.copy()
    for column, values in filters.items():
        if column not in result.columns:
            print(f"[warning] Filter column '{column}' not found in dataframe. Skipping.", file=sys.stderr)
            continue

        print(f"[info] Filtering {column} in {values}")
        result = result[result[column].isin(values)]

    return result


def aggregate_facilities(
    df: pd.DataFrame,
    group_by: List[str],
    agg_column: str = "p_nom",
    name_order: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate facility data by specified columns.

    Args:
        df: Input dataframe
        group_by: List of columns to group by
        agg_column: Column to aggregate (sum), default is 'p_nom'
        name_order: Optional list specifying order of columns in name.
                   If None, uses group_by order. Must be subset of group_by.

    Returns:
        Aggregated dataframe with 'name' and summed agg_column
    """
    # Validate group_by columns exist
    missing_cols = [col for col in group_by if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Group-by columns not found in dataframe: {missing_cols}")

    if agg_column not in df.columns:
        raise ValueError(f"Aggregation column '{agg_column}' not found in dataframe")

    # Validate name_order if provided
    if name_order is not None:
        invalid_cols = [col for col in name_order if col not in group_by]
        if invalid_cols:
            raise ValueError(
                f"name_order contains columns not in group_by: {invalid_cols}\n"
                f"Available group_by columns: {group_by}\n"
                f"Note: name_order should be a list of column names, not a single concatenated string"
            )
        # Use provided order
        name_cols = name_order
    else:
        # Use group_by order
        name_cols = group_by

    print(f"[info] Grouping by: {group_by}")
    print(f"[info] Name will be created from: {name_cols}")
    print(f"[info] Aggregating: {agg_column} (sum)")

    # Group and aggregate
    grouped = df.groupby(group_by, as_index=False)[agg_column].sum()

    # Create name column by joining specified columns in order
    if len(name_cols) == 1:
        grouped["name"] = grouped[name_cols[0]].astype(str)
    else:
        grouped["name"] = grouped[name_cols].astype(str).agg("_".join, axis=1)

    # Reorder columns: name, group_by columns (in original order), then agg_column
    cols = ["name"] + group_by + [agg_column]
    grouped = grouped[cols]

    print(f"[info] Aggregated {len(df)} rows → {len(grouped)} rows")

    return grouped


def read_input_file(path: Path, encoding: Optional[str] = None) -> pd.DataFrame:
    """
    Read input file (CSV or Excel) with encoding handling.

    Args:
        path: Path to input file
        encoding: Optional encoding for CSV files

    Returns:
        DataFrame
    """
    suffix = path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        print(f"[info] Reading Excel file: {path}")
        return pd.read_excel(path)

    elif suffix == ".csv":
        print(f"[info] Reading CSV file: {path}")

        encodings_to_try = [encoding] if encoding else TRY_ENCODINGS

        last_err = None
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(path, encoding=enc)
                print(f"[info] Read OK with encoding='{enc}'")
                return df
            except UnicodeDecodeError as e:
                print(f"[warn] Failed with encoding='{enc}': {e}")
                last_err = e
            except Exception as e:
                print(f"[warn] Read error with encoding='{enc}': {e}")
                last_err = e

        if last_err:
            raise last_err
        raise ValueError(f"Unable to decode CSV with encodings: {encodings_to_try}")

    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv, .xlsx, or .xls")


def save_output_file(
    df: pd.DataFrame,
    path: Path,
    encoding: str = "utf-8-sig"
) -> None:
    """
    Save output file (CSV or Excel).

    Args:
        df: DataFrame to save
        path: Output path
        encoding: Encoding for CSV files
    """
    suffix = path.suffix.lower()

    path.parent.mkdir(parents=True, exist_ok=True)

    if suffix in [".xlsx", ".xls"]:
        print(f"[info] Saving Excel file: {path}")
        df.to_excel(path, index=False)
    elif suffix == ".csv":
        print(f"[info] Saving CSV file: {path} (encoding={encoding})")
        df.to_csv(path, index=False, encoding=encoding)
    else:
        raise ValueError(f"Unsupported output format: {suffix}. Use .csv or .xlsx")


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate generation facility data by specified columns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input file path (CSV or Excel)"
    )

    parser.add_argument(
        "--output", "-o",
        help="Output file path (CSV or Excel)"
    )

    parser.add_argument(
        "--filter", "-f",
        nargs="+",
        default=[],
        help="Filter conditions in format: column=value1,value2. Can specify multiple filters."
    )

    parser.add_argument(
        "--group-by", "-g",
        nargs="+",
        default=["province", "carrier"],
        help="Columns to group by for aggregation (default: province carrier)"
    )

    parser.add_argument(
        "--name-order",
        nargs="+",
        help="Order of columns in generated name (must be subset of --group-by). If not specified, uses --group-by order."
    )

    parser.add_argument(
        "--agg-column",
        default="p_nom",
        help="Column to aggregate (sum). Default: p_nom"
    )

    parser.add_argument(
        "--input-encoding",
        help="Force input encoding for CSV files (e.g., cp949, utf-8)"
    )

    parser.add_argument(
        "--output-encoding",
        default="utf-8-sig",
        help="Output encoding for CSV files (default: utf-8-sig)"
    )

    parser.add_argument(
        "--list-columns",
        action="store_true",
        help="List available columns and exit"
    )

    parser.add_argument(
        "--show-unique",
        nargs="+",
        help="Show unique values for specified columns and exit"
    )

    args = parser.parse_args()

    # Read input file
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[error] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    df = read_input_file(in_path, args.input_encoding)
    print(f"[info] Loaded {len(df)} rows, {len(df.columns)} columns")

    # List columns if requested
    if args.list_columns:
        print("\n[info] Available columns:")
        for col in df.columns:
            print(f"  - {col}")
        sys.exit(0)

    # Show unique values if requested
    if args.show_unique:
        for col in args.show_unique:
            if col not in df.columns:
                print(f"[warning] Column '{col}' not found", file=sys.stderr)
                continue
            unique_vals = df[col].dropna().unique()
            print(f"\n[info] Unique values in '{col}' ({len(unique_vals)} total):")
            for val in sorted(unique_vals):
                print(f"  - {val}")
        sys.exit(0)

    # Check output is provided for actual aggregation
    if not args.output:
        print("[error] --output/-o is required for aggregation", file=sys.stderr)
        sys.exit(1)

    # Parse and apply filters
    filters = parse_filters(args.filter)
    if filters:
        print(f"[info] Applying filters: {filters}")
        df_filtered = apply_filters(df, filters)
        print(f"[info] After filtering: {len(df_filtered)} rows remain")
    else:
        print("[info] No filters applied")
        df_filtered = df

    if df_filtered.empty:
        print("[error] No data remains after filtering. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Aggregate
    df_aggregated = aggregate_facilities(
        df_filtered,
        group_by=args.group_by,
        agg_column=args.agg_column,
        name_order=args.name_order
    )

    # Save output
    out_path = Path(args.output)
    save_output_file(df_aggregated, out_path, args.output_encoding)

    print(f"[done] Saved {len(df_aggregated)} aggregated rows to {args.output}")

    # Show preview
    print("\n[info] Preview of output:")
    print(df_aggregated.head(10))


if __name__ == "__main__":
    main()
