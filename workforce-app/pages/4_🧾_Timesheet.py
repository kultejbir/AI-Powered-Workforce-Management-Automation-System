from datetime import datetime

import pandas as pd
import streamlit as st
from utils.auth import require_login
from utils.db import get_db

user = require_login()
db = get_db()

st.title("🧾 Timesheet")

tab_log, tab_approve = st.tabs(
    ["Log Hours", "Approve Timesheets"] if user["role"] in ("Admin", "Manager") else ["Log Hours"]
)

with tab_log:
    emp_id = user.get("employee_id") or st.number_input("Employee ID", step=1)
    with st.form("log_hours"):
        c1, c2, c3 = st.columns(3)
        date = c1.date_input("Date", value=datetime.now())
        project = c2.selectbox("Project", ["Internal", "Client A", "Client B"])
        hours = c3.number_input("Hours worked", min_value=0.0, max_value=24.0, step=0.5, value=8.0)
        submitted = st.form_submit_button("Submit log")

    if submitted:
        db.timesheets.insert_one(
            {
                "employee_id": int(emp_id),
                "date": date.strftime("%Y-%m-%d"),
                "project": project,
                "hours": hours,
                "status": "Submitted",
            }
        )
        st.success("Timesheet entry logged.")

    st.divider()
    records = list(db.timesheets.find({"employee_id": int(emp_id)}, {"_id": 0}).sort("date", -1).limit(50))
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        by_project = df.groupby("project")["hours"].sum()
        st.bar_chart(by_project)
    else:
        st.info("No timesheet entries yet — this collection starts empty until people use it.")

if user["role"] in ("Admin", "Manager"):
    with tab_approve:
        pending = list(db.timesheets.find({"status": "Submitted"}, {"_id": 0}))
        if not pending:
            st.info("Nothing pending approval.")
        else:
            df = pd.DataFrame(pending)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if st.button("✅ Approve all shown"):
                db.timesheets.update_many({"status": "Submitted"}, {"$set": {"status": "Approved"}})
                st.rerun()
