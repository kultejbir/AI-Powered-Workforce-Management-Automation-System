from datetime import datetime

import pandas as pd
import streamlit as st
from utils.auth import require_login
from utils.db import get_db

user = require_login()
db = get_db()

st.title("🌴 Leave Management")

tab_apply, tab_status, tab_approve = st.tabs(
    ["Apply for Leave", "My Leave Status", "Approvals"] if user["role"] in ("Admin", "Manager")
    else ["Apply for Leave", "My Leave Status"]
)

with tab_apply:
    emp_id = user.get("employee_id") or st.number_input("Employee ID", step=1)
    with st.form("apply_leave"):
        leave_type = st.selectbox("Leave type", ["Sick", "Casual", "Earned"])
        c1, c2 = st.columns(2)
        start = c1.date_input("Start date")
        end = c2.date_input("End date")
        reason = st.text_area("Reason")
        submitted = st.form_submit_button("Submit request")

    if submitted:
        if end < start:
            st.error("End date must be after start date.")
        else:
            db.leaves.insert_one(
                {
                    "employee_id": int(emp_id),
                    "leave_type": leave_type,
                    "start_date": start.strftime("%Y-%m-%d"),
                    "end_date": end.strftime("%Y-%m-%d"),
                    "status": "Pending",
                    "reason": reason,
                    "applied_on": datetime.now().strftime("%Y-%m-%d"),
                }
            )
            st.success("Leave request submitted for approval.")

with tab_status:
    emp_id = user.get("employee_id")
    records = list(db.leaves.find({"employee_id": emp_id}, {"_id": 0}).sort("applied_on", -1))
    if records:
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        balance = 18 - sum(
            1 for r in records if r["status"] == "Approved"
        )  # simple placeholder policy: 18 days/year
        st.metric("Approx. leave balance remaining", balance)
    else:
        st.info("No leave requests yet — this collection starts empty until people use it.")

if user["role"] in ("Admin", "Manager"):
    with tab_approve:
        pending = list(db.leaves.find({"status": "Pending"}, {"_id": 0}))
        if not pending:
            st.info("No pending requests.")
        for req in pending:
            with st.container(border=True):
                st.write(
                    f"**Employee {req['employee_id']}** — {req['leave_type']} leave, "
                    f"{req['start_date']} to {req['end_date']}"
                )
                st.caption(f"Reason: {req.get('reason', '—')}")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"appr_{req['employee_id']}_{req['start_date']}"):
                    db.leaves.update_one(
                        {"employee_id": req["employee_id"], "start_date": req["start_date"]},
                        {"$set": {"status": "Approved"}},
                    )
                    st.rerun()
                if c2.button("❌ Reject", key=f"rej_{req['employee_id']}_{req['start_date']}"):
                    db.leaves.update_one(
                        {"employee_id": req["employee_id"], "start_date": req["start_date"]},
                        {"$set": {"status": "Rejected"}},
                    )
                    st.rerun()
