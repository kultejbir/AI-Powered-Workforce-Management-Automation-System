import pandas as pd
import plotly.express as px
import streamlit as st
from utils.auth import require_role
from utils.data_helpers import coerce_date, coerce_numeric
from utils.db import get_db

user = require_role("Admin", "Manager")
db = get_db()

st.title("📈 Manager Dashboard")

# ManagerID in this dataset uses its own numbering that doesn't overlap
# with EmpID, and not every manager has their own employee_info row
# (e.g. "Board of Directors"). So team lookup matches the logged-in
# manager's name against employee_info.ManagerName.
if user["role"] == "Admin":
    team = pd.DataFrame(list(db.employee_info.find({}, {"_id": 0})))
else:
    team = pd.DataFrame(list(db.employee_info.find({"ManagerName": user["name"]}, {"_id": 0})))

if team.empty:
    st.info(f"No direct reports found for ManagerName = '{user['name']}'.")
    st.stop()

team = coerce_numeric(team, ["Absences", "DaysLateLast30"])
team_ids = team["EmpID"].tolist()

st.subheader(f"Team ({len(team)} people)")
cols = ["EmpID", "EmployeeName", "Department", "Position", "PerformanceScore",
        "EmploymentStatus", "Absences", "DaysLateLast30"]
st.dataframe(team[[c for c in cols if c in team.columns]], use_container_width=True, hide_index=True)

attendance = pd.DataFrame(list(db.attendance.find({"employee_id": {"$in": team_ids}}, {"_id": 0})))
leaves = pd.DataFrame(list(db.leaves.find({"employee_id": {"$in": team_ids}}, {"_id": 0})))
timesheets = pd.DataFrame(list(db.timesheets.find({"employee_id": {"$in": team_ids}}, {"_id": 0})))

c1, c2, c3 = st.columns(3)
c1.metric("Team size", len(team))
c2.metric(
    "Late arrivals (attendance log)",
    int((attendance["status"] == "Late").sum()) if not attendance.empty else 0,
)
c3.metric(
    "Pending leave approvals",
    int((leaves["status"] == "Pending").sum()) if not leaves.empty else 0,
)

col1, col2 = st.columns(2)
with col1:
    fig = px.pie(team, names="PerformanceScore", title="Team Performance Distribution")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.bar(
        team.sort_values("Absences", ascending=False).head(15),
        x="Absences", y="EmployeeName", orientation="h", title="Absences by Team Member",
    )
    st.plotly_chart(fig2, use_container_width=True)

if not attendance.empty:
    st.subheader("Team attendance over time")
    att = coerce_date(attendance.copy(), ["date"])
    daily = att.dropna(subset=["date"]).groupby(att["date"].dt.date).size().reset_index(name="check_ins")
    fig3 = px.line(daily, x="date", y="check_ins")
    st.plotly_chart(fig3, use_container_width=True)

if not timesheets.empty:
    st.subheader("Hours logged per team member")
    by_emp = timesheets.groupby("employee_id")["hours"].sum().reset_index()
    fig4 = px.bar(by_emp, x="employee_id", y="hours")
    st.plotly_chart(fig4, use_container_width=True)
