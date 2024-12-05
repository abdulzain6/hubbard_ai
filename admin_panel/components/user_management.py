import streamlit as st
from utils import register_admin, delete_user, update_user

def main():
    st.title("User Management")
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    # Section to register a new admin
    with st.form("register_admin"):
        st.subheader("Register New Admin")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        name = st.text_input("Name", key="reg_name")
        country = st.text_input("Country", key="reg_country")
        phone = st.text_input("Phone", key="reg_phone")
        company_role = st.text_input("Company Role", key="reg_company_role")
        company = st.text_input("Company", key="reg_company")
        department = st.text_input("Department", key="reg_department")
        submit_button = st.form_submit_button("Register")

        if submit_button:
            response, status_code = register_admin(email, password, name, country, phone, company_role, company, department, access_token)
            if status_code == 200:
                st.success("Admin registered successfully!")
            else:
                st.error(f"Failed to register admin: {response.get('detail', 'No specific error provided')}")

    # Section to update an existing user
    with st.form("update_user"):
        st.subheader("Update Existing User")
        upd_email = st.text_input("User Email to Update", key="upd_email")
        upd_data = {
            "password": st.text_input("New Password (leave blank to keep unchanged)", type="password", key="upd_password"),
            "name": st.text_input("Name", key="upd_name"),
            "country": st.text_input("Country", key="upd_country"),
            "phone": st.text_input("Phone", key="upd_phone"),
            "company_role": st.text_input("Company Role", key="upd_company_role"),
            "company": st.text_input("Company", key="upd_company"),
            "department": st.text_input("Department", key="upd_department"),
            "role": st.text_input("Role", key="upd_role")
        }
        update_button = st.form_submit_button("Update User")

        if update_button:
            # Filter out empty fields from updates
            filtered_updates = {k: v for k, v in upd_data.items() if v}
            response, status_code = update_user(upd_email, filtered_updates, access_token)
            if status_code == 200:
                st.success("User updated successfully!")
            else:
                st.error(f"Failed to update user: {response.get('detail', 'No specific error provided')}")

    # Section to delete a user
    with st.form("delete_user"):
        st.subheader("Delete User")
        del_email = st.text_input("User Email to Delete", key="del_email")
        delete_button = st.form_submit_button("Delete User")

        if delete_button:
            response, status_code = delete_user(del_email, access_token)
            if status_code == 200:
                st.success("User deleted successfully!")
            else:
                st.error(f"Failed to delete user: {response.get('message', 'No specific error provided')}")

if __name__ == "__main__":
    main()
