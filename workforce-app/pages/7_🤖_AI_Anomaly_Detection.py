import pandas as pd
import plotly.express as px
import streamlit as st
from utils.auth import require_role
from utils.db import get_db
from utils.ai_models import detect_attendance_anomalies

user = require_role("Admin", "Manager")
db = get_db()

st.title("🤖 AI: Attendance Anomaly Detection")
st.caption(
    "Uses an unsupervised IsolationForest model over check-in time and "
    "hours worked to flag attendance records that look unusual — "
    "no manually labeled 'anomaly' data required. Runs on your real "
    "`attendance` collection."
)

records = list(db.attendance.find({}, {"_id": 0}))
if not records:
    st.info("No documents found in `attendance`. Check DB_NAME in your secrets.")
    st.stop()

df = pd.DataFrame(records)
df = df.dropna(subset=["check_in", "check_out"])

# join employee names for readability
employees = pd.DataFrame(
    list(db.employee_info.find({}, {"_id": 0, "EmpID": 1, "EmployeeName": 1, "Department": 1}))
)
df = df.merge(employees, left_on="employee_id", right_on="EmpID", how="left")

contamination = st.slider(
    "Sensitivity (expected % of records that are anomalous)",
    min_value=0.02, max_value=0.25, value=0.08, step=0.01,
)

with st.spinner("Running model on attendance records..."):
    result = detect_attendance_anomalies(df, contamination=contamination)

anomalies = result[result["is_anomaly"]]
c1, c2 = st.columns(2)
c1.metric("Records analyzed", len(result))
c2.metric("Anomalies flagged", len(anomalies))

fig = px.scatter(
    result,
    x="checkin_minute",
    y="hours_worked",
    color="is_anomaly",
    hover_data=["EmployeeName", "Department", "date", "check_in", "check_out"],
    title="Check-in time vs. hours worked (flagged points = potential anomalies)",
    labels={"checkin_minute": "Check-in time (minutes after midnight)"},
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Flagged records")
if anomalies.empty:
    st.success("No anomalies at this sensitivity level.")
else:
    cols = ["employee_id", "EmployeeName", "Department", "date", "check_in", "check_out", "hours_worked", "status"]
    st.dataframe(
        anomalies[cols].sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Typical causes: unusually early/late check-ins, very short or very "
        "long shifts, or a missed check-out. Worth a manager follow-up."
    )

    st.subheader("Which employees have the most flagged records?")
    by_emp = anomalies.groupby(["employee_id", "EmployeeName"]).size().reset_index(name="anomaly_count")
    by_emp = by_emp.sort_values("anomaly_count", ascending=False).head(15)
    fig2 = px.bar(by_emp, x="anomaly_count", y="EmployeeName", orientation="h")
    st.plotly_chart(fig2, use_container_width=True)
