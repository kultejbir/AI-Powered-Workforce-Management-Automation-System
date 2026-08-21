import pandas as pd
import plotly.express as px
import streamlit as st
from utils.auth import require_role
from utils.data_helpers import coerce_numeric
from utils.db import get_db

user = require_role("Admin")
db = get_db()

st.title("👥 Employee Management")

tab_list, tab_add, tab_dept = st.tabs(["All Employees", "Add / Onboard", "Departments"])

with tab_list:
    employees = list(db.employee_info.find({}, {"_id": 0}))
    if not employees:
        st.info("No documents found in `employee_info`. Check DB_NAME in your secrets.")
    else:
        df = pd.DataFrame(employees)
        df = coerce_numeric(df, ["Salary", "Absences", "DaysLateLast30"])

        c1, c2, c3 = st.columns(3)
        dept_filter = c1.multiselect("Department", sorted(df["Department"].dropna().unique()))
        status_filter = c2.multiselect("Employment status", sorted(df["EmploymentStatus"].dropna().unique()))
        search = c3.text_input("Search by name")

        view = df.copy()
        if dept_filter:
            view = view[view["Department"].isin(dept_filter)]
        if status_filter:
            view = view[view["EmploymentStatus"].isin(status_filter)]
        if search:
            view = view[view["EmployeeName"].str.contains(search, case=False, na=False)]

        show_cols = [
            "EmpID", "EmployeeName", "Department", "Position", "ManagerName",
            "EmploymentStatus", "PerformanceScore", "Salary", "DateofHire",
            "DaysLateLast30", "Absences",
        ]
        show_cols = [c for c in show_cols if c in view.columns]
        st.dataframe(view[show_cols], use_container_width=True, hide_index=True)
        st.caption(f"{len(view)} of {len(df)} employees shown")

with tab_add:
    st.subheader("Onboard a new employee")
    st.caption(
        "Adds a new document to your existing `employee_info` collection "
        "using the same field names as your source data."
    )
    existing_ids = [e["EmpID"] for e in db.employee_info.find({}, {"_id": 0, "EmpID": 1})]
    next_id = max((int(i) for i in existing_ids), default=10000) + 1

    with st.form("add_employee"):
        c1, c2 = st.columns(2)
        emp_id = c1.number_input("EmpID", value=next_id, step=1)
        employee_name = c2.text_input("EmployeeName")
        department = c1.text_input("Department")
        position = c2.text_input("Position")
        manager_name = c1.text_input("ManagerName")
        salary = c2.number_input("Salary", min_value=0, step=1000, value=55000)
        submitted = st.form_submit_button("Add employee")

    if submitted:
        if not employee_name:
            st.warning("EmployeeName is required.")
        elif db.employee_info.find_one({"EmpID": int(emp_id)}):
            st.error(f"EmpID {emp_id} already exists.")
        else:
            from datetime import datetime
            db.employee_info.insert_one(
                {
                    "EmpID": int(emp_id),
                    "EmployeeName": employee_name,
                    "Department": department,
                    "Position": position,
                    "ManagerName": manager_name,
                    "Salary": salary,
                    "EmploymentStatus": "Active",
                    "Termd": 0,
                    "PerformanceScore": "Fully Meets",
                    "DateofHire": datetime.now(),
                    "DaysLateLast30": 0,
                    "Absences": 0,
                }
            )
            st.success(f"{employee_name} onboarded successfully.")
            st.rerun()

with tab_dept:
    employees = list(db.employee_info.find({}, {"_id": 0}))
    if employees:
        df = pd.DataFrame(employees)
        c1, c2 = st.columns(2)
        with c1:
            counts = df.groupby("Department").size().reset_index(name="headcount")
            fig = px.bar(counts, x="Department", y="headcount", title="Headcount by Department")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = px.pie(df, names="EmploymentStatus", title="Employment Status Mix")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data yet.")
