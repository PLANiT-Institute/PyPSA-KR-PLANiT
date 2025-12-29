"""
Leap Year Handler for PyPSA Alternative

Handles temporal data conversion between years with different leap year status.
Adjusts dates when base_year and target_year differ, accounting for Feb 29th.
"""

import pandas as pd
from calendar import isleap


def is_leap_year(year):
    """Check if a year is a leap year."""
    return isleap(year)


def has_feb_29(df, datetime_col=None):
    """
    Check if a DataFrame with datetime index or column contains Feb 29th.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with datetime index or column
    datetime_col : str, optional
        Name of datetime column if not using index

    Returns:
    --------
    bool
        True if Feb 29th exists in the data
    """
    if datetime_col:
        dates = pd.to_datetime(df[datetime_col])
        return ((dates.dt.month == 2) & (dates.dt.day == 29)).any()
    else:
        dates = df.index
        return ((dates.month == 2) & (dates.day == 29)).any()


def adjust_year_with_leap_handling(df, base_year, target_year, datetime_col=None):
    """
    Adjust year in temporal data, handling leap year differences.

    Cases:
    ------
    1. Both leap years OR both non-leap: Simply change the year
    2. Base is leap, target is not: Drop Feb 29th
    3. Base is not leap, target is leap: Duplicate Feb 28th to create Feb 29th

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with datetime index or column
    base_year : int or None
        Year of the base data
    target_year : int or None
        Target year to convert to
    datetime_col : str, optional
        Name of datetime column if not using index. If None, uses index.

    Returns:
    --------
    pd.DataFrame
        DataFrame with adjusted dates (or unchanged if base_year/target_year not provided or same)
    """
    # Return unchanged if years not specified or are the same
    if not base_year or not target_year or base_year == target_year:
        return df.copy()

    df = df.copy()

    # Determine if working with index or column
    use_index = datetime_col is None
    if use_index:
        dates = df.index
    else:
        dates = pd.to_datetime(df[datetime_col])

    base_is_leap = is_leap_year(base_year)
    target_is_leap = is_leap_year(target_year)

    # Helper to get month/day that works for both Index and Series
    def get_month(dt):
        return dt.month if isinstance(dt, pd.DatetimeIndex) else dt.dt.month

    def get_day(dt):
        return dt.day if isinstance(dt, pd.DatetimeIndex) else dt.dt.day

    # Case 1: Both same leap status - just change year
    if base_is_leap == target_is_leap:
        new_dates = dates.map(lambda x: x.replace(year=target_year))
        if use_index:
            df.index = new_dates
        else:
            df[datetime_col] = new_dates
        return df

    # Case 2: Base is leap, target is not - drop Feb 29th
    if base_is_leap and not target_is_leap:
        # Filter out Feb 29th
        mask = ~((get_month(dates) == 2) & (get_day(dates) == 29))
        df = df[mask].copy()

        # Update dates reference after filtering
        if use_index:
            dates = df.index
        else:
            dates = pd.to_datetime(df[datetime_col])

        # Change year
        new_dates = dates.map(lambda x: x.replace(year=target_year))
        if use_index:
            df.index = new_dates
        else:
            df[datetime_col] = new_dates
        return df

    # Case 3: Base is not leap, target is leap - duplicate Feb 28th
    if not base_is_leap and target_is_leap:
        # Find Feb 28th rows
        feb_28_mask = (get_month(dates) == 2) & (get_day(dates) == 28)
        feb_28_rows = df[feb_28_mask].copy()

        if len(feb_28_rows) > 0:
            # Change year first for all data
            new_dates = dates.map(lambda x: x.replace(year=target_year))
            if use_index:
                df.index = new_dates
            else:
                df[datetime_col] = new_dates

            # Create Feb 29th rows from Feb 28th
            if use_index:
                feb_29_dates = feb_28_rows.index.map(lambda x: x.replace(day=29))
                feb_28_rows.index = feb_29_dates
            else:
                feb_29_dates = pd.to_datetime(feb_28_rows[datetime_col]).map(lambda x: x.replace(day=29))
                feb_28_rows[datetime_col] = feb_29_dates

            # Concatenate and sort
            df = pd.concat([df, feb_28_rows])
            if use_index:
                df = df.sort_index()
            else:
                df = df.sort_values(datetime_col).reset_index(drop=True)
        else:
            # No Feb 28th found, just change year
            new_dates = dates.map(lambda x: x.replace(year=target_year))
            if use_index:
                df.index = new_dates
            else:
                df[datetime_col] = new_dates

        return df

    return df


def adjust_snapshot_data(snapshot_df, base_year, target_year):
    """
    Adjust snapshot data with datetime index.

    Parameters:
    -----------
    snapshot_df : pd.DataFrame
        DataFrame with datetime index
    base_year : int
        Year of the base data
    target_year : int
        Target year to convert to

    Returns:
    --------
    pd.DataFrame
        DataFrame with adjusted dates
    """
    return adjust_year_with_leap_handling(snapshot_df, base_year, target_year, datetime_col=None)


def adjust_load_data(load_df, base_year, target_year, datetime_col='datetime'):
    """
    Adjust load data that may have a datetime column.

    Parameters:
    -----------
    load_df : pd.DataFrame
        DataFrame with datetime column or index
    base_year : int
        Year of the base data
    target_year : int
        Target year to convert to
    datetime_col : str, optional
        Name of datetime column. If None, uses index.

    Returns:
    --------
    pd.DataFrame
        DataFrame with adjusted dates
    """
    # Check if datetime_col exists in dataframe
    if datetime_col and datetime_col in load_df.columns:
        return adjust_year_with_leap_handling(load_df, base_year, target_year, datetime_col=datetime_col)
    else:
        # Use index
        return adjust_year_with_leap_handling(load_df, base_year, target_year, datetime_col=None)
