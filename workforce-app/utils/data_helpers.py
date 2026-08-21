"""
Small helpers to make dashboard code resilient to how your data was typed
when it was written into MongoDB (some import paths store CSV numbers/dates
as native BSON types, others store everything as strings). These coerce
either case into a usable pandas dtype without erroring out.
"""

import pandas as pd


def coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def coerce_date(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Handles native datetime values AND 'DD-MM-YYYY' strings."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    return df
