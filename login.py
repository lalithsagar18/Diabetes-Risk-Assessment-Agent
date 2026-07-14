import streamlit as st
from database import get_user_by_username, create_user
from utils import hash_password, check_password, init_session_state


def show_login() -> bool:
    """Render the login form. Returns True if login succeeded.
    If the user does not exist, a simple admin creation flow is provided on first run.
    """
    # Initialise session defaults if not already done
    init_session_state()

    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
            return False
        user = get_user_by_username(username)
        if user:
            user_id, stored_hash = user
            if check_password(password, stored_hash):
                st.session_state["user_id"] = user_id
                st.session_state["authenticated"] = True
                st.success("Logged in successfully!")
                return True
            else:
                st.error("Incorrect password.")
                return False
        else:
            # No user found – offer to create an admin account
            st.info("User not found. Create a new admin account?")
            if st.button("Create Admin"):
                hashed = hash_password(password)
                uid = create_user(username, hashed)
                st.session_state["user_id"] = uid
                st.session_state["authenticated"] = True
                st.success("Admin account created and logged in.")
                return True
    return False


def logout():
    """Clear authentication state."""
    for key in ["authenticated", "user_id", "login_error"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Logged out.")
