import streamlit as st
import sys, os
# Ensure the repository root is on the Python path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from login import show_login, logout
from dashboard import render_dashboard
from prediction import render_prediction_page
from history import render_history_page
from analytics import render_analytics_page
from utils import init_session_state

st.set_page_config(page_title="DiabetesCare AI", layout="wide")

# Initialise session state defaults
init_session_state()

if not st.session_state.get('authenticated'):
    # Show login page
    if show_login():
        st.session_state['authenticated'] = True
        st.experimental_rerun()
    else:
        st.stop()

# Sidebar navigation
st.sidebar.title(":hospital: DiabetesCare AI")
# Show localhost link and button after authentication
if st.session_state.get('authenticated'):
    st.sidebar.markdown(
        "**App URL:** "
        "[Diabetes‑Risk‑Assessment‑Agent](https://github.com/lalithsagar18/Diabetes-Risk-Assessment-Agent)"
    )
    if st.sidebar.button("Open App in New Tab"):
        import webbrowser
        webbrowser.open_new_tab("https://github.com/lalithsagar18/Diabetes-Risk-Assessment-Agent")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Register Patient", "History", "Analytics", "Logout"])

if menu == "Dashboard":
    render_dashboard()
elif menu == "Register Patient":
    render_prediction_page()
elif menu == "History":
    render_history_page()
elif menu == "Analytics":
    render_analytics_page()
elif menu == "Logout":
    logout()
    st.experimental_rerun()
