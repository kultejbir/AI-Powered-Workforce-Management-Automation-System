"""
Attendance anomaly detection.

Approach: unsupervised IsolationForest over two engineered features per
attendance record — check-in minute-of-day, and hours worked. This needs
no labeled data (you don't have historical "this was anomalous" tags),
which makes it realistic for a student project with limited data.

Flags things like: unusually early/late check-ins, unusually short/long
shifts. Each row gets an anomaly_score (lower = more anomalous) and an
is_anomaly flag.
"""

import pandas as pd
from sklearn.ensemble import IsolationForest


def _to_minutes(t) -> float:
    """Accepts a datetime.time, datetime, or 'HH:MM' string."""
    if pd.isna(t):
        return None
    if isinstance(t, str):
        h, m = t.split(":")[:2]
        return int(h) * 60 + int(m)
    return t.hour * 60 + t.minute


def detect_attendance_anomalies(df: pd.DataFrame, contamination: float = 0.08) -> pd.DataFrame:
    """
    df must have columns: employee_id, date, check_in, check_out
    (check_in/check_out as 'HH:MM' strings or datetime.time).
    Returns df with added columns: hours_worked, checkin_minute,
    anomaly_score, is_anomaly.
    """
    work = df.copy()
    work["checkin_minute"] = work["check_in"].apply(_to_minutes)
    checkout_minute = work["check_out"].apply(_to_minutes)

    # handle overnight shifts (checkout minute < checkin minute)
    hours = (checkout_minute - work["checkin_minute"]) / 60.0
    hours = hours.where(hours >= 0, hours + 24)
    work["hours_worked"] = hours

    features = work[["checkin_minute", "hours_worked"]].dropna()
    if len(features) < 10:
        # Not enough data for a meaningful model yet
        work["anomaly_score"] = 0.0
        work["is_anomaly"] = False
        return work

    model = IsolationForest(
        contamination=contamination, random_state=42, n_estimators=200
    )
    model.fit(features)

    work.loc[features.index, "anomaly_score"] = model.decision_function(features)
    work.loc[features.index, "is_anomaly"] = model.predict(features) == -1
    work["is_anomaly"] = work["is_anomaly"].fillna(False)

    return work
