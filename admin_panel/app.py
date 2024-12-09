import streamlit as st
from components import login, files, ai_chat, roles, scenarios, voice_chat

# Define a dictionary of pages
PAGES = {
    "Login": login.main,
    "Files" : files.main,
    "AI Chat" : ai_chat.main,
    "Role Management" : roles.main,
    "Scenarios": scenarios.main,
    "Voice Chat" : voice_chat.main
}


def main():
    st.sidebar.title('Navigation')
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    page = PAGES[selection]
    page()  # Call the page function
    
if __name__ == "__main__":
    main()
