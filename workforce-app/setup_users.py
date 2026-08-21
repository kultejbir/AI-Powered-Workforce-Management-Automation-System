"""
Your data (employee_info, attendance, employee_skills,
position_skill_requirements, skills) already lives in MongoDB — this
script does NOT touch or re-import any of that.

It only creates a `users` collection for app login/RBAC, since your
dataset doesn't include login credentials. It picks 2 REAL people from
your employee_info collection to back the demo Manager/Employee accounts
(a manager with the most direct reports, and one of their reports), so
the Manager Dashboard shows a real team.

Usage:
    export MONGODB_URI="mongodb+srv://..."   (or paste in secrets.toml)
    python setup_users.py
"""

import os

import bcrypt
from pymongo import MongoClient

URI = os.environ.get("MONGODB_URI") or input("Paste your MONGODB_URI: ").strip()
DB_NAME = os.environ.get("DB_NAME") or input(
    "Database name (the one your 5 collections live in): "
).strip()

client = MongoClient(URI)
db = client[DB_NAME]


def hash_pw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


# Find whichever manager (by ManagerName) has the most direct reports
# who ALSO exists as an employee row themselves (so they can log in as
# that person).
pipeline = [
    {"$group": {"_id": "$ManagerName", "report_count": {"$sum": 1}}},
    {"$sort": {"report_count": -1}},
]
manager_candidates = list(db.employee_info.aggregate(pipeline))

chosen_manager = None
for cand in manager_candidates:
    mgr_name = cand["_id"]
    mgr_row = db.employee_info.find_one({"EmployeeName": mgr_name})
    if mgr_row:
        chosen_manager = mgr_row
        report_count = cand["report_count"]
        break

if not chosen_manager:
    raise SystemExit(
        "Couldn't find a manager who is also an employee row in "
        "employee_info. Check your ManagerName / EmployeeName fields."
    )

sample_report = db.employee_info.find_one({"ManagerName": chosen_manager["EmployeeName"]})

users = [
    {
        "username": "admin",
        "password_hash": hash_pw("admin123"),
        "role": "Admin",
        "name": "Admin User",
        "employee_id": None,
    },
    {
        "username": "manager1",
        "password_hash": hash_pw("manager123"),
        "role": "Manager",
        "name": chosen_manager["EmployeeName"],
        "employee_id": chosen_manager["EmpID"],
    },
    {
        "username": "emp1",
        "password_hash": hash_pw("emp123"),
        "role": "Employee",
        "name": sample_report["EmployeeName"],
        "employee_id": sample_report["EmpID"],
    },
]

db.users.delete_many({})
db.users.insert_many(users)

print(f"\nManager account -> {chosen_manager['EmployeeName']} (EmpID {chosen_manager['EmpID']}), "
      f"{report_count} direct reports")
print(f"Employee account -> {sample_report['EmployeeName']} (EmpID {sample_report['EmpID']})")
print("\nDemo logins (change passwords before real deployment):")
print("  admin / admin123      -> Admin")
print("  manager1 / manager123 -> Manager")
print("  emp1 / emp123         -> Employee")
