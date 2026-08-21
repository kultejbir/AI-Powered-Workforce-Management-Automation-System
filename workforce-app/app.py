import streamlit as st
from utils.db import check_connection
from utils.auth import login, logout, current_user

st.set_page_config(page_title="Workforce Management", page_icon="🧑‍💼", layout="wide")

st.title("🧑‍💼 AI-Powered Workforce Management")

ok, msg = check_connection()
if not ok:
    st.error(
        f"⚠️ {msg}\n\nSet MONGODB_URI in `.streamlit/secrets.toml` "
        "(locally) or in your app's Secrets (Streamlit Cloud), then rerun "
        "`python seed.py` to load demo data."
    )
    st.stop()

user = current_user()

if user is None:
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        if login(username, password):
            st.success("Logged in — use the sidebar to navigate.")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    with st.expander("Demo accounts (from seed.py)"):
        st.code(
            "admin / admin123      → Admin\n"
            "manager1 / manager123 → Manager\n"
            "emp1 / emp123         → Employee",
            language="text",
        )
else:
    st.success(f"Logged in as **{user['name']}** ({user['role']})")
    st.write("Use the sidebar to open a module. Available pages depend on your role.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Role", user["role"])
    col2.metric("Username", user["username"])
    col3.metric("Employee ID", user.get("employee_id") or "—")

    if st.button("Log out"):
        logout()
        st.rerun()

    st.divider()
    st.markdown(
        """
        **Modules in the sidebar:**
        - 👥 Employee Management *(Admin)*
        - 🕒 Attendance *(All — QR check-in)*
        - 🌴 Leave Management *(All)*
        - 🧾 Timesheet *(All)*
        - 📊 HR Dashboard *(Admin / Manager)*
        - 📈 Manager Dashboard *(Manager)*
        - 🤖 AI Anomaly Detection *(Admin / Manager)*
        - 🧩 Skill Gap Analysis *(Admin / Manager)*
        """
    )
