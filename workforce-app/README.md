# AI-Powered Workforce Management (Streamlit)

Connects directly to your existing MongoDB — the app does NOT import or
duplicate any data. It reads your 5 collections as-is:

| Collection | Key fields used |
|---|---|
| `employee_info` | EmpID, EmployeeName, Department, Position, ManagerName, Salary, EmploymentStatus, Termd, PerformanceScore, EngagementSurvey, EmpSatisfaction, Absences, DaysLateLast30, TermReason, DateofHire |
| `attendance` | employee_id, date, check_in, check_out, method, status |
| `skills` | SkillID, SkillName, Category |
| `employee_skills` | EmpID, SkillID, ProficiencyLevel |
| `position_skill_requirements` | Position, SkillID, RequiredProficiency, Importance |

Dashboards are built natively in the app with Plotly (no Power BI embed —
dropped since "Publish to web" isn't available to you administratively).

## What's included
- **Employee Management** — search/filter your real `employee_info`, onboard new employees
- **Attendance** — your real `attendance` collection + live QR check-in/out simulation
- **Leave Management** — apply, view status, approve/reject (grows from real usage — you have no source collection for this yet)
- **Timesheet** — daily hours logging, approval (same — grows from real usage)
- **HR Dashboard** — 10+ native Plotly charts: headcount, attrition %, termination reasons, salary distribution, engagement vs. satisfaction, attendance trends, absenteeism, lateness
- **Manager Dashboard** — real team view (via `ManagerName` matching — see note below)
- **AI: Attendance Anomaly Detection** — IsolationForest on real check-in times / shift lengths
- **Skill Gap Analysis** — required vs. actual proficiency per position, individual skill profiles, org-wide skill coverage, using your 3 skills collections
- **RBAC** — Admin / Manager / Employee, enforced per page

## Not included (documented as future scope — normal for a project report)
Biometric/face recognition/GPS attendance, payroll processing, SAP/Oracle/ERP
integrations, chatbot, sentiment analysis, voice assistant, mobile app,
multi-location support.

## 1. Local setup

```bash
cd workforce-app
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml:
#   MONGODB_URI = your real connection string
#   DB_NAME     = the database your 5 collections live in
```

## 2. Set up login accounts (one-time, doesn't touch your real data)

Your dataset has no login/credentials collection, so this creates a
`users` collection only — it never modifies `employee_info`, `attendance`,
or the skills collections.

```bash
export MONGODB_URI="mongodb+srv://..."
export DB_NAME="your_db_name"
python setup_users.py
```

It automatically finds the manager with the most direct reports (who is
also present as an employee row) and their first report, so the Manager
Dashboard shows a real team out of the box:

| username | password | role |
|---|---|---|
| admin | admin123 | Admin |
| manager1 | manager123 | Manager (real manager from your data) |
| emp1 | emp123 | Employee (real report of that manager) |

**Change/remove these before any real deployment.** Add more accounts
directly in the `users` collection for other employees as needed.

## 3. Run locally

```bash
streamlit run app.py
```

## 4. Deploy (free & simplest option)
**Streamlit Community Cloud:**
1. Push this folder to GitHub (don't commit `secrets.toml` — only the
   `.example` file goes in git).
2. share.streamlit.io → New app → point at your repo → main file `app.py`.
3. In Settings → Secrets, paste your real MONGODB_URI and DB_NAME.
4. Deploy — you get a public URL.

Alternative: Azure App Service / Azure Container Apps if you want it in
the same ecosystem as Fabric for your report.

## Note on manager/employee relationships
`ManagerID` in your data uses its own numbering (separate from `EmpID`),
and some managers (e.g. "Board of Directors") have no `employee_info` row
of their own. The app links reports to managers via **`ManagerName`**
matching a real employee's `EmployeeName`, which is reliable for this
dataset. If you'd rather use a proper foreign key, add a `ManagerEmpID`
column mapping each manager name to their `EmpID` and I can switch the
lookup over.

## Note on field types
The app coerces numeric and date fields defensively (`utils/data_helpers.py`)
so it works whether your import path stored dates/numbers as native BSON
types or as plain strings. If a chart looks empty, check that the
collection/field names above match yours exactly (case-sensitive).

## Suggested "Phase 2" additions if you have time left
- Email notifications (leave approved/rejected, late arrival) via SMTP
- A second AI feature: absenteeism prediction or attrition prediction
  (you already have real `Absences` / `Termd` columns to train on)
- Holiday calendar + leave balance policy engine
- CSV export for reports (attendance, payroll input summary)
