import pandas as pd
import plotly.express as px
import streamlit as st
from utils.auth import require_role
from utils.data_helpers import coerce_date, coerce_numeric
from utils.db import get_db

user = require_role("Admin", "Manager")
db = get_db()

st.title("📊 HR Dashboard")
st.caption("All charts below are generated live from your MongoDB collections.")

employees = pd.DataFrame(list(db.employee_info.find({}, {"_id": 0})))
attendance = pd.DataFrame(list(db.attendance.find({}, {"_id": 0})))
leaves = pd.DataFrame(list(db.leaves.find({}, {"_id": 0})))

if employees.empty:
    st.info("No documents found in `employee_info`. Check DB_NAME in your secrets.")
    st.stop()

employees = coerce_numeric(
    employees, ["Salary", "Termd", "EngagementSurvey", "EmpSatisfaction", "Absences", "DaysLateLast30"]
)

# ----------------------------------------------------------------- KPIs
active = employees[employees["EmploymentStatus"] == "Active"]
terminated = employees[employees["Termd"] == 1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Employees", len(employees))
c2.metric("Active", len(active))
c3.metric("Attrition rate", f"{len(terminated) / len(employees) * 100:.1f}%")
c4.metric("Avg. Engagement Survey", f"{employees['EngagementSurvey'].mean():.2f} / 5")

st.divider()

# ----------------------------------------------------------------- Headcount
col1, col2 = st.columns(2)
with col1:
    counts = employees.groupby("Department").size().reset_index(name="headcount")
    fig = px.bar(counts, x="Department", y="headcount", title="Headcount by Department")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.pie(employees, names="PerformanceScore", title="Performance Score Distribution")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------------ Attrition
st.subheader("Attrition")
col3, col4 = st.columns(2)
with col3:
    status_by_dept = employees.groupby(["Department", "EmploymentStatus"]).size().reset_index(name="count")
    fig3 = px.bar(
        status_by_dept, x="Department", y="count", color="EmploymentStatus",
        barmode="stack", title="Employment Status by Department",
    )
    st.plotly_chart(fig3, use_container_width=True)
with col4:
    termed = employees[employees["TermReason"].notna() & (employees["TermReason"] != "N/A-StillEmployed")]
    if not termed.empty:
        reasons = termed["TermReason"].value_counts().reset_index()
        reasons.columns = ["reason", "count"]
        fig4 = px.bar(reasons.head(10), x="count", y="reason", orientation="h", title="Top Termination Reasons")
        st.plotly_chart(fig4, use_container_width=True)

# --------------------------------------------------------------- Compensation
st.subheader("Compensation & Performance")
col5, col6 = st.columns(2)
with col5:
    fig5 = px.box(employees, x="Department", y="Salary", title="Salary Distribution by Department")
    st.plotly_chart(fig5, use_container_width=True)
with col6:
    fig6 = px.scatter(
        employees, x="EngagementSurvey", y="EmpSatisfaction", color="PerformanceScore",
        hover_data=["EmployeeName", "Department"],
        title="Engagement vs. Satisfaction (colored by performance)",
    )
    st.plotly_chart(fig6, use_container_width=True)

# ----------------------------------------------------------------- Attendance
if not attendance.empty:
    st.subheader("Attendance")
    att = attendance.copy()
    att = coerce_date(att, ["date"])

    col7, col8 = st.columns(2)
    with col7:
        status_counts = att["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig7 = px.pie(status_counts, names="status", values="count", title="Attendance Status (all time)")
        st.plotly_chart(fig7, use_container_width=True)
    with col8:
        monthly = (
            att.dropna(subset=["date"])
            .assign(month=lambda d: d["date"].dt.to_period("M").astype(str))
            .groupby(["month", "status"]).size().reset_index(name="count")
        )
        fig8 = px.line(monthly, x="month", y="count", color="status", title="Monthly Attendance Trend")
        st.plotly_chart(fig8, use_container_width=True)

# --------------------------------------------------------------- Absenteeism
st.subheader("Absenteeism & Lateness (from employee_info)")
col9, col10 = st.columns(2)
with col9:
    top_absent = employees.nlargest(10, "Absences")[["EmployeeName", "Department", "Absences"]]
    fig9 = px.bar(top_absent, x="Absences", y="EmployeeName", orientation="h", title="Top 10 by Absences")
    st.plotly_chart(fig9, use_container_width=True)
with col10:
    fig10 = px.histogram(employees, x="DaysLateLast30", nbins=15, title="Distribution: Days Late (last 30)")
    st.plotly_chart(fig10, use_container_width=True)

if not leaves.empty:
    st.subheader("Leave requests by type & status")
    pivot = leaves.groupby(["leave_type", "status"]).size().reset_index(name="count")
    fig11 = px.bar(pivot, x="leave_type", y="count", color="status", barmode="group")
    st.plotly_chart(fig11, use_container_width=True)
