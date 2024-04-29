import streamlit as st
from components import login, dashboard_page, files, ai_chat, prompts, roles

# Define a dictionary of pages
PAGES = {
    "Login": login.main,
    "Dashboard": dashboard_page.main,
    "Files" : files.main,
    "AI Chat" : ai_chat.main,
    "Prompt Templates" : prompts.main,
    "Role Prompt Management" : roles.main
}

def main():
    st.sidebar.title('Navigation')
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    page = PAGES[selection]
    page()  # Call the page function
    
if __name__ == "__main__":
    main()
