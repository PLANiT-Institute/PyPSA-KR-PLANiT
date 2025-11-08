#!/usr/bin/env python3
"""
Fill Missing Values Utility

This utility fills missing values in CSV files using intelligent imputation methods.
Supports regression-based imputation with user-defined grouping variables and fallback strategies.

Features:
- Regression imputation based on grouping variables (e.g., year, type, carrier)
- Group mean/median fallback when regression is not possible
- Non-negative constraints to prevent negative values
- Detailed logging and reporting
- Multiple imputation methods: regression, group_mean, group_median, forward_fill, backward_fill
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union
import warnings
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import logging


class MissingValueFiller:
    """Fill missing values using various imputation strategies."""

    def __init__(self, verbose: bool = True):
        """
        Initialize the filler.

        Args:
            verbose: Whether to print detailed progress information
        """
        self.verbose = verbose
        self.report = []
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO if self.verbose else logging.WARNING,
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def log(self, message: str):
        """Log a message."""
        if self.verbose:
            self.logger.info(message)
        self.report.append(message)

    def fill_missing_values(
        self,
        df: pd.DataFrame,
        target_column: str,
        grouping_columns: List[str],
        method: str = 'regression',
        non_negative: bool = True,
        predictor_columns: Optional[List[str]] = None,
        time_window: Optional[int] = None,
        year_column: Optional[str] = None,
        exclude_outliers: int = 0
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fill missing values in target column using specified method.

        Args:
            df: Input DataFrame
            target_column: Column with missing values to fill
            grouping_columns: Columns to group by for imputation (e.g., ['build_year', 'type', 'carrier'])
            method: Imputation method - 'regression', 'group_mean', 'group_median', 'forward_fill', 'backward_fill',
                    'recent_mean', 'recent_median'
            non_negative: If True, ensure filled values are non-negative
            predictor_columns: Columns to use as predictors for regression (if None, uses grouping_columns)
            time_window: For recent_mean/recent_median methods, total time window in years
                        (e.g., 10 means use 10-year window: target_year-5 to target_year+5)
            year_column: Column containing year information for time-window based methods
            exclude_outliers: Number of min/max values to exclude (e.g., 1 excludes 1 min and 1 max)

        Returns:
            Tuple of (filled DataFrame, statistics dictionary)
        """
        df = df.copy()

        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame")

        for col in grouping_columns:
            if col not in df.columns:
                raise ValueError(f"Grouping column '{col}' not found in DataFrame")

        missing_count = df[target_column].isna().sum()
        total_count = len(df)

        self.log(f"\n{'='*60}")
        self.log(f"Filling Missing Values: {target_column}")
        self.log(f"{'='*60}")
        self.log(f"Total rows: {total_count}")
        self.log(f"Missing values: {missing_count} ({missing_count/total_count*100:.1f}%)")
        self.log(f"Non-missing values: {total_count - missing_count} ({(total_count-missing_count)/total_count*100:.1f}%)")
        self.log(f"Method: {method}")
        self.log(f"Grouping by: {', '.join(grouping_columns)}")
        self.log(f"Non-negative constraint: {non_negative}")
        if method in ['recent_mean', 'recent_median'] and time_window:
            self.log(f"Time window: {time_window} years")
        if exclude_outliers > 0:
            self.log(f"Outlier exclusion: {exclude_outliers} min and {exclude_outliers} max values")

        if method == 'regression':
            df_filled, stats = self._fill_with_regression(
                df, target_column, grouping_columns, predictor_columns, non_negative
            )
        elif method == 'group_mean':
            df_filled, stats = self._fill_with_group_aggregate(
                df, target_column, grouping_columns, 'mean', non_negative
            )
        elif method == 'group_median':
            df_filled, stats = self._fill_with_group_aggregate(
                df, target_column, grouping_columns, 'median', non_negative
            )
        elif method == 'recent_mean':
            df_filled, stats = self._fill_with_time_window_aggregate(
                df, target_column, grouping_columns, 'mean', non_negative, time_window, year_column, exclude_outliers
            )
        elif method == 'recent_median':
            df_filled, stats = self._fill_with_time_window_aggregate(
                df, target_column, grouping_columns, 'median', non_negative, time_window, year_column, exclude_outliers
            )
        elif method == 'forward_fill':
            df_filled, stats = self._fill_with_forward_backward(
                df, target_column, grouping_columns, 'ffill', non_negative
            )
        elif method == 'backward_fill':
            df_filled, stats = self._fill_with_forward_backward(
                df, target_column, grouping_columns, 'bfill', non_negative
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        # Final check
        remaining_missing = df_filled[target_column].isna().sum()
        filled_count = missing_count - remaining_missing

        self.log(f"\n{'='*60}")
        self.log(f"Results:")
        self.log(f"  Filled: {filled_count} values ({filled_count/missing_count*100:.1f}% of missing)")
        self.log(f"  Still missing: {remaining_missing} values")

        if non_negative and filled_count > 0:
            # Check if any negative values were clipped
            original_filled = stats.get('filled_values', [])
            if original_filled:
                negative_count = sum(1 for v in original_filled if v < 0)
                if negative_count > 0:
                    self.log(f"  Clipped {negative_count} negative values to 0")

        stats['total_rows'] = total_count
        stats['originally_missing'] = missing_count
        stats['filled_count'] = filled_count
        stats['remaining_missing'] = remaining_missing

        return df_filled, stats

    def _fill_with_regression(
        self,
        df: pd.DataFrame,
        target_column: str,
        grouping_columns: List[str],
        predictor_columns: Optional[List[str]],
        non_negative: bool
    ) -> Tuple[pd.DataFrame, Dict]:
        """Fill missing values using regression within groups."""
        self.log(f"\nUsing regression imputation...")

        if predictor_columns is None:
            predictor_columns = grouping_columns

        # Validate predictor columns
        for col in predictor_columns:
            if col not in df.columns:
                self.log(f"  Warning: Predictor column '{col}' not found, removing from predictors")
                predictor_columns = [c for c in predictor_columns if c in df.columns]

        if not predictor_columns:
            self.log(f"  No valid predictor columns, falling back to group mean")
            return self._fill_with_group_aggregate(df, target_column, grouping_columns, 'mean', non_negative)

        self.log(f"  Predictors: {', '.join(predictor_columns)}")

        df_filled = df.copy()
        filled_values = []
        filled_indices = []

        # Create a mask for rows with missing target values
        missing_mask = df[target_column].isna()

        # Try to fit regression on non-missing data
        non_missing_df = df[~missing_mask].copy()

        if len(non_missing_df) < 2:
            self.log(f"  Not enough non-missing data for regression, falling back to group mean")
            return self._fill_with_group_aggregate(df, target_column, grouping_columns, 'mean', non_negative)

        # Prepare features
        X_train, y_train, encoders = self._prepare_features(
            non_missing_df, predictor_columns, target_column
        )

        if X_train is None:
            self.log(f"  Could not prepare features, falling back to group mean")
            return self._fill_with_group_aggregate(df, target_column, grouping_columns, 'mean', non_negative)

        # Fit regression model
        try:
            model = LinearRegression()
            model.fit(X_train, y_train)

            # Show coefficients
            self.log(f"  Model fitted successfully")
            self.log(f"  R² score on training data: {model.score(X_train, y_train):.4f}")

            # Predict missing values
            missing_df = df[missing_mask].copy()
            X_missing, _, _ = self._prepare_features(
                missing_df, predictor_columns, target_column, encoders
            )

            if X_missing is not None and len(X_missing) > 0:
                predictions = model.predict(X_missing)

                # Apply non-negative constraint
                if non_negative:
                    predictions = np.maximum(predictions, 0)

                # Fill the values
                missing_indices = df[missing_mask].index
                df_filled.loc[missing_indices, target_column] = predictions
                filled_values = predictions.tolist()
                filled_indices = missing_indices.tolist()

                self.log(f"  Predicted {len(predictions)} values using regression")
                self.log(f"  Predicted range: [{predictions.min():.2e}, {predictions.max():.2e}]")
                self.log(f"  Predicted mean: {predictions.mean():.2e}")

        except Exception as e:
            self.log(f"  Error during regression: {str(e)}")
            self.log(f"  Falling back to group mean")
            return self._fill_with_group_aggregate(df, target_column, grouping_columns, 'mean', non_negative)

        stats = {
            'method': 'regression',
            'predictors': predictor_columns,
            'filled_values': filled_values,
            'filled_indices': filled_indices,
            'r2_score': model.score(X_train, y_train) if len(filled_values) > 0 else None
        }

        return df_filled, stats

    def _prepare_features(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        target_column: str,
        encoders: Optional[Dict] = None
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Dict]:
        """Prepare features for regression by encoding categorical variables."""
        if encoders is None:
            encoders = {}

        X_list = []

        for col in feature_columns:
            if col not in df.columns:
                continue

            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                X_list.append(df[col].values.reshape(-1, 1))
            else:
                # Encode categorical
                if col not in encoders:
                    encoders[col] = LabelEncoder()
                    try:
                        encoders[col].fit(df[col].dropna().astype(str))
                    except:
                        continue

                try:
                    encoded = encoders[col].transform(df[col].fillna('missing').astype(str))
                    X_list.append(encoded.reshape(-1, 1))
                except:
                    continue

        if not X_list:
            return None, None, encoders

        X = np.hstack(X_list)
        y = df[target_column].values if target_column in df.columns else None

        return X, y, encoders

    def _fill_with_group_aggregate(
        self,
        df: pd.DataFrame,
        target_column: str,
        grouping_columns: List[str],
        agg_method: str,
        non_negative: bool
    ) -> Tuple[pd.DataFrame, Dict]:
        """Fill missing values using group mean or median."""
        self.log(f"\nUsing group {agg_method} imputation...")

        df_filled = df.copy()
        filled_values = []
        filled_indices = []

        # Calculate group aggregates
        if agg_method == 'mean':
            group_agg = df.groupby(grouping_columns)[target_column].mean()
        else:  # median
            group_agg = df.groupby(grouping_columns)[target_column].median()

        self.log(f"  Calculated {agg_method} for {len(group_agg)} groups")

        # Fill missing values
        missing_mask = df[target_column].isna()

        for idx in df[missing_mask].index:
            row = df.loc[idx]
            group_key = tuple(row[col] for col in grouping_columns)

            if group_key in group_agg.index:
                fill_value = group_agg[group_key]

                # Apply non-negative constraint
                if non_negative and fill_value < 0:
                    fill_value = 0

                df_filled.loc[idx, target_column] = fill_value
                filled_values.append(fill_value)
                filled_indices.append(idx)

        self.log(f"  Filled {len(filled_values)} values using group {agg_method}")

        if filled_values:
            self.log(f"  Filled range: [{min(filled_values):.2e}, {max(filled_values):.2e}]")
            self.log(f"  Filled mean: {np.mean(filled_values):.2e}")

        # Check remaining missing values (NO fallback - leave as NaN)
        remaining_missing = df_filled[target_column].isna().sum()
        if remaining_missing > 0:
            self.log(f"  {remaining_missing} values remain missing (no matching group found)")
            self.log(f"  These will be left as NaN - consider using regression or a different grouping")

        stats = {
            'method': f'group_{agg_method}',
            'grouping': grouping_columns,
            'filled_values': filled_values,
            'filled_indices': filled_indices,
            'group_count': len(group_agg)
        }

        return df_filled, stats

    def _fill_with_time_window_aggregate(
        self,
        df: pd.DataFrame,
        target_column: str,
        grouping_columns: List[str],
        agg_method: str,
        non_negative: bool,
        time_window: Optional[int] = None,
        year_column: Optional[str] = None,
        exclude_outliers: int = 0
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fill missing values using mean/median of nearby values within a time window.

        Args:
            df: Input DataFrame
            target_column: Column to fill
            grouping_columns: Columns to group by (excluding year)
            agg_method: 'mean' or 'median'
            non_negative: Whether to enforce non-negative constraint
            time_window: Total time window in years (e.g., 10 means target_year-5 to target_year+5)
            year_column: Column containing year information
            exclude_outliers: Number of min/max values to exclude (e.g., 1 excludes 1 min and 1 max)

        Returns:
            Tuple of (filled DataFrame, statistics)
        """
        self.log(f"\nUsing recent {agg_method} imputation with time window...")

        # Detect year column if not specified
        if year_column is None:
            # Try to find a year column
            year_candidates = [col for col in df.columns if 'year' in col.lower()]
            if year_candidates:
                year_column = year_candidates[0]
                self.log(f"  Auto-detected year column: {year_column}")
            else:
                raise ValueError("No year column specified and couldn't auto-detect one")

        if year_column not in df.columns:
            raise ValueError(f"Year column '{year_column}' not found in DataFrame")

        # Set default time window if not specified
        if time_window is None:
            time_window = 10
            self.log(f"  Using default time window: {time_window} years (±{time_window//2})")

        df_filled = df.copy()
        filled_values = []
        filled_indices = []

        # Get non-year grouping columns
        non_year_grouping = [col for col in grouping_columns if col != year_column]

        # Process each row with missing value
        missing_mask = df[target_column].isna()
        missing_indices = df[missing_mask].index

        for idx in missing_indices:
            row = df.loc[idx]
            row_year = row[year_column]

            # Build filter for same group
            group_filter = pd.Series([True] * len(df), index=df.index)
            for col in non_year_grouping:
                group_filter &= (df[col] == row[col])

            # Add time window filter (window is total span, so divide by 2 for each side)
            # e.g., window=10 means 1977-5 to 1977+5 (total 10 years)
            half_window = time_window // 2
            year_filter = (df[year_column] >= row_year - half_window) & (df[year_column] <= row_year + half_window)

            # Combine filters and exclude missing values
            combined_filter = group_filter & year_filter & df[target_column].notna()

            # Get values within the window
            window_values = df.loc[combined_filter, target_column]

            if len(window_values) > 0:
                # Exclude outliers if specified
                if exclude_outliers > 0 and len(window_values) > 2 * exclude_outliers:
                    # Sort values and exclude min/max
                    sorted_values = window_values.sort_values()
                    # Remove 'exclude_outliers' from each end
                    trimmed_values = sorted_values.iloc[exclude_outliers:-exclude_outliers]

                    # Calculate aggregate on trimmed data
                    if agg_method == 'mean':
                        fill_value = trimmed_values.mean()
                    else:  # median
                        fill_value = trimmed_values.median()
                else:
                    # Not enough values to exclude outliers, use all
                    if agg_method == 'mean':
                        fill_value = window_values.mean()
                    else:  # median
                        fill_value = window_values.median()

                # Apply non-negative constraint
                if non_negative and fill_value < 0:
                    fill_value = 0

                df_filled.loc[idx, target_column] = fill_value
                filled_values.append(fill_value)
                filled_indices.append(idx)

        self.log(f"  Filled {len(filled_values)} values using recent {agg_method} ({time_window}-year window, ±{time_window//2})")

        if filled_values:
            self.log(f"  Filled range: [{min(filled_values):.2e}, {max(filled_values):.2e}]")
            self.log(f"  Filled mean: {np.mean(filled_values):.2e}")

        # Check remaining missing values (NO fallback for recent methods)
        remaining_missing = df_filled[target_column].isna().sum()
        if remaining_missing > 0:
            self.log(f"  {remaining_missing} values remain missing (no similar values found in time window)")
            self.log(f"  These will be left as NaN - consider using a different method or wider time window")

        stats = {
            'method': f'recent_{agg_method}',
            'grouping': grouping_columns,
            'time_window': time_window,
            'year_column': year_column,
            'exclude_outliers': exclude_outliers,
            'filled_values': filled_values,
            'filled_indices': filled_indices
        }

        return df_filled, stats

    def _fill_with_forward_backward(
        self,
        df: pd.DataFrame,
        target_column: str,
        grouping_columns: List[str],
        fill_method: str,
        non_negative: bool
    ) -> Tuple[pd.DataFrame, Dict]:
        """Fill missing values using forward fill or backward fill within groups."""
        self.log(f"\nUsing {fill_method} imputation within groups...")

        df_filled = df.copy()
        filled_count = 0

        # Apply forward/backward fill within groups
        if fill_method == 'ffill':
            df_filled[target_column] = df_filled.groupby(grouping_columns)[target_column].transform(
                lambda x: x.ffill()
            )
        else:  # bfill
            df_filled[target_column] = df_filled.groupby(grouping_columns)[target_column].transform(
                lambda x: x.bfill()
            )

        filled_count = df[target_column].isna().sum() - df_filled[target_column].isna().sum()

        self.log(f"  Filled {filled_count} values using {fill_method}")

        # Apply non-negative constraint
        if non_negative:
            negative_mask = df_filled[target_column] < 0
            if negative_mask.any():
                df_filled.loc[negative_mask, target_column] = 0
                self.log(f"  Clipped {negative_mask.sum()} negative values to 0")

        stats = {
            'method': fill_method,
            'grouping': grouping_columns,
            'filled_count': filled_count
        }

        return df_filled, stats

    def process_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]],
        target_column: str,
        grouping_columns: List[str],
        method: str = 'regression',
        non_negative: bool = True,
        predictor_columns: Optional[List[str]] = None,
        backup: bool = True,
        time_window: Optional[int] = None,
        year_column: Optional[str] = None,
        exclude_outliers: int = 0
    ) -> Dict:
        """
        Process a single CSV file.

        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (if None, overwrites input)
            target_column: Column to fill missing values
            grouping_columns: Columns to group by
            method: Imputation method
            non_negative: Ensure non-negative values
            predictor_columns: Predictor columns for regression
            backup: Create backup file
            time_window: Total time window in years for recent_mean/recent_median methods
                        (default: 10, means 10-year span e.g., 1977-5 to 1977+5)
            year_column: Column containing year information (auto-detected if not specified)
            exclude_outliers: Number of min/max values to exclude (e.g., 1 excludes 1 min and 1 max)

        Returns:
            Statistics dictionary
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        self.log(f"\nProcessing: {input_path}")

        # Read CSV
        df = pd.read_csv(input_path, encoding='utf-8-sig')

        # Fill missing values
        df_filled, stats = self.fill_missing_values(
            df, target_column, grouping_columns, method, non_negative, predictor_columns,
            time_window, year_column, exclude_outliers
        )

        # Determine output file
        if output_file is None:
            output_path = input_path
        else:
            output_path = Path(output_file)

        # Create backup
        if backup and output_path == input_path:
            backup_path = output_path.with_suffix('.bak')
            import shutil
            shutil.copy2(output_path, backup_path)
            self.log(f"  Created backup: {backup_path}")

        # Save result
        df_filled.to_csv(output_path, index=False, encoding='utf-8-sig')
        self.log(f"  Saved: {output_path}")

        return stats

    def get_report(self) -> str:
        """Get full report as string."""
        return '\n'.join(self.report)


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fill missing values in CSV files using intelligent imputation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fill capital_cost using regression on year, type, carrier
  python fill_missing_values.py input.csv capital_cost --group build_year type carrier

  # Use group mean instead of regression
  python fill_missing_values.py input.csv capital_cost --group build_year type carrier --method group_mean

  # Allow negative values
  python fill_missing_values.py input.csv capital_cost --group build_year type carrier --allow-negative

  # Specify output file
  python fill_missing_values.py input.csv capital_cost --group build_year type carrier -o output.csv
        """
    )

    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('target_column', help='Column to fill missing values')
    parser.add_argument('--group', '-g', nargs='+', required=True,
                       help='Columns to group by (e.g., build_year type carrier)')
    parser.add_argument('--method', '-m',
                       choices=['regression', 'group_mean', 'group_median', 'forward_fill', 'backward_fill',
                               'recent_mean', 'recent_median'],
                       default='regression',
                       help='Imputation method (default: regression)')
    parser.add_argument('--predictors', '-p', nargs='+',
                       help='Predictor columns for regression (default: same as grouping columns)')
    parser.add_argument('--time-window', '-w', type=int,
                       help='Total time window in years for recent_mean/recent_median (default: 10, e.g., 10 = year-5 to year+5)')
    parser.add_argument('--year-column', '-y',
                       help='Column containing year information for time-window methods (auto-detected if not specified)')
    parser.add_argument('--exclude-outliers', '-e', type=int, default=0,
                       help='Exclude N min and N max values (e.g., 1 excludes 1 min and 1 max, default: 0)')
    parser.add_argument('--output', '-o', help='Output CSV file (default: overwrite input)')
    parser.add_argument('--allow-negative', action='store_true',
                       help='Allow negative values (default: constrain to non-negative)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Do not create backup file')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress detailed output')

    args = parser.parse_args()

    # Create filler
    filler = MissingValueFiller(verbose=not args.quiet)

    # Process file
    try:
        stats = filler.process_file(
            input_file=args.input_file,
            output_file=args.output,
            target_column=args.target_column,
            grouping_columns=args.group,
            method=args.method,
            non_negative=not args.allow_negative,
            predictor_columns=args.predictors,
            backup=not args.no_backup,
            time_window=args.time_window,
            year_column=args.year_column,
            exclude_outliers=args.exclude_outliers
        )

        print(f"\nSuccess! Filled {stats['filled_count']} values")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
