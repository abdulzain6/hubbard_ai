import streamlit as st
from components import login, dashboard_page

# Define a dictionary of pages
PAGES = {
    "Login": login.main,
    "Dashboard": dashboard_page.main
}

def main():
    st.sidebar.title('Navigation')
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    page = PAGES[selection]
    page()  # Call the page function
    
if __name__ == "__main__":
    main()
