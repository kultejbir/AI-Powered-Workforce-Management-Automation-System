import pandas as pd
import plotly.express as px
import streamlit as st
from utils.auth import require_role
from utils.db import get_db

user = require_role("Admin", "Manager")
db = get_db()

st.title("🧩 Skill Gap Analysis")
st.caption(
    "Compares required skills per position against what your employees "
    "actually have on record, using your `skills`, `employee_skills`, and "
    "`position_skill_requirements` collections."
)

skills = pd.DataFrame(list(db.skills.find({}, {"_id": 0})))
emp_skills = pd.DataFrame(list(db.employee_skills.find({}, {"_id": 0})))
pos_req = pd.DataFrame(list(db.position_skill_requirements.find({}, {"_id": 0})))
employees = pd.DataFrame(
    list(db.employee_info.find({}, {"_id": 0, "EmpID": 1, "EmployeeName": 1, "Position": 1, "Department": 1}))
)

if skills.empty or emp_skills.empty or pos_req.empty:
    st.info("One of `skills` / `employee_skills` / `position_skill_requirements` is empty. Check DB_NAME.")
    st.stop()

# ------------------------------------------------------------------ #
# Position-level gap: for a chosen position, compare the average
# proficiency of employees CURRENTLY in that position against what the
# position requires.
# ------------------------------------------------------------------ #
st.subheader("Position skill gaps")

positions = sorted(pos_req["Position"].unique())
chosen_position = st.selectbox("Choose a position", positions)

reqs = pos_req[pos_req["Position"] == chosen_position].merge(skills, on="SkillID", how="left")

people_in_role = employees[employees["Position"] == chosen_position]
if people_in_role.empty:
    st.warning(f"No current employees hold the position '{chosen_position}' — showing requirements only.")
    gap_df = reqs[["SkillName", "Category", "RequiredProficiency", "Importance"]].copy()
    gap_df["avg_current_proficiency"] = 0
    gap_df["gap"] = gap_df["RequiredProficiency"]
else:
    role_emp_skills = emp_skills[emp_skills["EmpID"].isin(people_in_role["EmpID"])]
    avg_prof = role_emp_skills.groupby("SkillID")["ProficiencyLevel"].mean().reset_index()
    avg_prof.columns = ["SkillID", "avg_current_proficiency"]

    gap_df = reqs.merge(avg_prof, on="SkillID", how="left")
    gap_df["avg_current_proficiency"] = gap_df["avg_current_proficiency"].fillna(0)
    gap_df["gap"] = (gap_df["RequiredProficiency"] - gap_df["avg_current_proficiency"]).clip(lower=0)

gap_df = gap_df.sort_values("gap", ascending=False)

fig = px.bar(
    gap_df,
    x="SkillName",
    y=["avg_current_proficiency", "RequiredProficiency"],
    barmode="group",
    title=f"Required vs. current proficiency — {chosen_position}",
    labels={"value": "Proficiency (1-5)", "variable": ""},
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    gap_df[["SkillName", "Category", "Importance", "RequiredProficiency", "avg_current_proficiency", "gap"]],
    use_container_width=True, hide_index=True,
)

critical_gaps = gap_df[(gap_df["gap"] > 0) & (gap_df["Importance"] == "Critical")]
if not critical_gaps.empty:
    st.error(
        f"⚠️ {len(critical_gaps)} CRITICAL skill gap(s) for {chosen_position}: "
        + ", ".join(critical_gaps["SkillName"].tolist())
    )

st.divider()

# ------------------------------------------------------------------ #
# Individual employee skill profile
# ------------------------------------------------------------------ #
st.subheader("Individual employee skill profile")

emp_options = employees.sort_values("EmployeeName")
emp_label = st.selectbox(
    "Choose an employee",
    emp_options.apply(lambda r: f"{r['EmployeeName']} ({r['EmpID']}) — {r['Position']}", axis=1),
)
chosen_emp_id = int(emp_label.split("(")[1].split(")")[0])

person_skills = emp_skills[emp_skills["EmpID"] == chosen_emp_id].merge(skills, on="SkillID", how="left")
if person_skills.empty:
    st.info("No skills on record for this employee.")
else:
    fig2 = px.bar(
        person_skills.sort_values("ProficiencyLevel", ascending=True),
        x="ProficiencyLevel", y="SkillName", orientation="h", color="Category",
        title="Recorded skills & proficiency (1-5)",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ------------------------------------------------------------------ #
# Org-wide skill coverage by category
# ------------------------------------------------------------------ #
st.subheader("Org-wide skill coverage by category")
coverage = emp_skills.merge(skills, on="SkillID", how="left")
cat_summary = coverage.groupby("Category").agg(
    employees_with_skill=("EmpID", "nunique"),
    avg_proficiency=("ProficiencyLevel", "mean"),
).reset_index()
fig3 = px.bar(
    cat_summary.sort_values("employees_with_skill", ascending=False),
    x="Category", y="employees_with_skill", title="How many employees have at least one skill in each category",
)
st.plotly_chart(fig3, use_container_width=True)
