import streamlit as st
from utils import get_access_token

def main():
    st.title('Login Page')

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            try:
                access_token = get_access_token(username, password)
                st.success("Login successful!")
                st.session_state['access_token'] = access_token  # Store access token
                # Redirect or further actions
            except Exception as e:
                st.error(f"Login failed. Invalid username/Password")
