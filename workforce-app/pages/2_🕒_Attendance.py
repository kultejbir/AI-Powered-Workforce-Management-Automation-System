from datetime import datetime, time

import pandas as pd
import plotly.express as px
import streamlit as st
from utils.auth import require_login
from utils.data_helpers import coerce_date
from utils.db import get_db

user = require_login()
db = get_db()

st.title("🕒 Attendance")

st.subheader("Check in / out")
st.caption(
    "In production this is triggered by scanning a QR code posted at the "
    "office entrance; here we simulate that scan with a button. This adds "
    "a NEW record on top of your existing `attendance` collection."
)

today = datetime.now().strftime("%d-%m-%Y")
emp_id = user.get("employee_id") or st.number_input("Employee ID for this check-in", step=1)

col1, col2 = st.columns(2)
with col1:
    if st.button("📷 Simulate QR Check-In", use_container_width=True):
        existing = db.attendance.find_one({"employee_id": int(emp_id), "date": today})
        now_str = datetime.now().strftime("%H:%M")
        if existing:
            st.warning("Already checked in today.")
        else:
            is_late = datetime.now().time() > time(9, 15)
            db.attendance.insert_one(
                {
                    "employee_id": int(emp_id),
                    "date": today,
                    "check_in": now_str,
                    "check_out": None,
                    "method": "QR",
                    "status": "Late" if is_late else "On Time",
                }
            )
            st.success(f"Checked in at {now_str} ({'Late' if is_late else 'On Time'})")

with col2:
    if st.button("🚪 Simulate QR Check-Out", use_container_width=True):
        now_str = datetime.now().strftime("%H:%M")
        result = db.attendance.update_one(
            {"employee_id": int(emp_id), "date": today},
            {"$set": {"check_out": now_str}},
        )
        if result.matched_count:
            st.success(f"Checked out at {now_str}")
        else:
            st.warning("No check-in found for today yet.")

st.divider()
st.subheader("Attendance history")

query = {} if user["role"] in ("Admin", "Manager") else {"employee_id": int(emp_id)}
records = list(db.attendance.find(query, {"_id": 0}).limit(5000))

if records:
    df = pd.DataFrame(records)
    df = coerce_date(df, ["date"])  # handles 'DD-MM-YYYY' strings or native dates
    df = df.sort_values("date", ascending=False)

    late_count = (df["status"] == "Late").sum()
    c1, c2 = st.columns(2)
    c1.metric("Records shown", len(df))
    c2.metric("Late arrivals in view", int(late_count))

    st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    if user["role"] in ("Admin", "Manager"):
        st.subheader("Attendance status trend (daily)")
        trend = (
            df.dropna(subset=["date"])
            .groupby([df["date"].dt.date, "status"])
            .size()
            .reset_index(name="count")
        )
        fig = px.line(trend, x="date", y="count", color="status")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No attendance records found for this query.")
