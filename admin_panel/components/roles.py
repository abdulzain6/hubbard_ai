import streamlit as st
from utils import get_roles, add_role, update_role, delete_role

def main():
    st.title("Role Management")
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    roles = get_roles(access_token)

    # Display existing roles and allow updates
    for role in roles:
        with st.expander(f"Role: {role['name']}"):
            prompt_prefix = st.text_input(f"Prompt for {role['name']}", value=role['prompt'])
            if st.button(f"Update {role['name']}"):
                if update_role(role['name'], prompt_prefix, access_token):
                    st.success(f"Updated {role['name']} successfully!")
                else:
                    st.error("Failed to update role.")

            if st.button(f"Delete {role['name']}"):
                if delete_role(role['name'], access_token):
                    st.success(f"Deleted {role['name']} successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete role.")

    # Add new role
    with st.form("add_role"):
        new_name = st.text_input("Role Name")
        new_prompt_prefix = st.text_input("Prompt Prefix")
        submit_button = st.form_submit_button("Add Role")
        if submit_button:
            if add_role(new_name, new_prompt_prefix, access_token):
                st.success(f"Role {new_name} added successfully!")
                st.experimental_rerun()
            else:
                st.error("Failed to add role.")

if __name__ == "__main__":
    main()
