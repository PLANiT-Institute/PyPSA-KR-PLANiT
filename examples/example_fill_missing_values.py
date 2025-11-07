#!/usr/bin/env python3
"""
Example: Fill Missing Values

This script demonstrates how to use the fill_missing_values utility
to intelligently fill missing capital_cost values in generators.csv.
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

from fill_missing_values import MissingValueFiller


def example_1_basic_usage():
    """Example 1: Basic usage with regression method."""
    print("="*60)
    print("Example 1: Fill missing capital_cost using regression")
    print("="*60)

    filler = MissingValueFiller(verbose=True)

    stats = filler.process_file(
        input_file='data/Singlenode2024/generators.csv',
        output_file='data/Singlenode2024/generators_filled.csv',
        target_column='capital_cost',
        grouping_columns=['build_year', 'type', 'carrier'],
        method='regression',
        non_negative=True,
        backup=True
    )

    print(f"\nFilled {stats['filled_count']} values!")


def example_2_group_mean():
    """Example 2: Use group mean instead of regression."""
    print("\n" + "="*60)
    print("Example 2: Fill using group mean (simpler, faster)")
    print("="*60)

    filler = MissingValueFiller(verbose=True)

    stats = filler.process_file(
        input_file='data/Singlenode2024/generators.csv',
        output_file='data/Singlenode2024/generators_groupmean.csv',
        target_column='capital_cost',
        grouping_columns=['build_year', 'type', 'carrier'],
        method='group_mean',
        non_negative=True,
        backup=False
    )

    print(f"\nFilled {stats['filled_count']} values!")


def example_3_different_grouping():
    """Example 3: Use different grouping variables."""
    print("\n" + "="*60)
    print("Example 3: Fill using only type and carrier (ignore year)")
    print("="*60)

    filler = MissingValueFiller(verbose=True)

    stats = filler.process_file(
        input_file='data/Singlenode2024/generators.csv',
        output_file='data/Singlenode2024/generators_typecarrier.csv',
        target_column='capital_cost',
        grouping_columns=['type', 'carrier'],
        method='group_mean',
        non_negative=True,
        backup=False
    )

    print(f"\nFilled {stats['filled_count']} values!")


def example_4_programmatic():
    """Example 4: Programmatic usage without file I/O."""
    print("\n" + "="*60)
    print("Example 4: Programmatic usage (DataFrame to DataFrame)")
    print("="*60)

    import pandas as pd

    # Load data
    df = pd.read_csv('data/Singlenode2024/generators.csv')
    print(f"Original missing values: {df['capital_cost'].isna().sum()}")

    # Fill missing values
    filler = MissingValueFiller(verbose=True)
    df_filled, stats = filler.fill_missing_values(
        df=df,
        target_column='capital_cost',
        grouping_columns=['build_year', 'type', 'carrier'],
        method='group_mean',
        non_negative=True
    )

    print(f"After filling: {df_filled['capital_cost'].isna().sum()} missing values")

    # Save if desired
    # df_filled.to_csv('output.csv', index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    # Run examples
    # Uncomment the example you want to run:

    example_1_basic_usage()
    # example_2_group_mean()
    # example_3_different_grouping()
    # example_4_programmatic()
