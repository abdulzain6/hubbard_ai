import streamlit as st
from utils import get_files, delete_file, update_file_metadata, upload_file, fetch_files_metadata, get_roles

def main():
    st.title('File Management')
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    # Initialize session state for messages
    if 'message' not in st.session_state:
        st.session_state['message'] = ''
    
    if 'roles' not in st.session_state or 'role_names' not in st.session_state:
        roles = get_roles(access_token)
        st.session_state['roles'] = roles
        st.session_state['role_names'] = [role["name"] for role in roles]
        
    roles = get_roles(access_token)
    role_names = [role["name"] for role in roles]
    

    # File upload section with a heading
    if st.session_state['roles']:
        st.header('Upload New File')
        with st.form("file_upload"):
            uploaded_file = st.file_uploader("Choose a file")
            file_description = st.text_input("Description", value=st.session_state.get('last_description', ''))
            weight = st.number_input("Weight", value=st.session_state.get('last_weight', 0), step=1, format='%d')
            selected_role = st.selectbox("Select Role", options=role_names)
            submit_button = st.form_submit_button("Upload File")
            
            if submit_button and uploaded_file:
                file_data = uploaded_file.getvalue()
                if upload_file(uploaded_file.name, file_data, file_description, weight, selected_role, access_token):
                    st.session_state['message'] = f"Uploaded {uploaded_file.name}"
                    st.session_state['last_description'] = file_description
                    st.session_state['last_weight'] = weight
                    st.session_state['refresh_files'] = True
                    st.rerun()
                else:
                    st.error(f"Failed to upload {uploaded_file.name}")
    else:
        st.error("No roles available to display. Please create one")    



    # Heading for file listing
    st.header('File List')
    sort_order = st.selectbox("Sort by", ['A to Z', 'Weight (Highest to Lowest)'])
    ref = st.session_state.get('refresh_files', True)
    if ref or 'files' not in st.session_state:
        st.session_state['files'] = get_files(access_token)
        st.session_state['metadata'], _ = fetch_files_metadata(access_token)
        st.session_state['refresh_files'] = False
        
    if st.session_state['files']:
        files = st.session_state['files']
        metadata = st.session_state['metadata']
        if sort_order == 'A to Z':
            files.sort(key=lambda x: x['file_name'])
        else:
            files.sort(key=lambda x: metadata.get(x['file_name']).get("weight"), reverse=True)

        for file in files:
            col1, col2, col3, col4 = st.columns([1, 7, 2, 3])
            with col1:
                st.checkbox("Select", key=f"checkbox_{file['file_name']}", label_visibility="hidden")
            with col2:
                st.text(file['file_name'])
            with col3:
                new_weight = st.number_input("Weight", value=metadata.get(file['file_name']).get("weight"), key=f"weight_{file['file_name']}")
                if new_weight != metadata.get(file['file_name']).get("weight"):
                    if st.button("Update", key=f"update_{file['file_name']}"):
                        status = update_file_metadata(file['file_name'], {"weight" : new_weight}, access_token)
                        if status == 200:
                            st.session_state['refresh_files'] = True
                            st.success(f"Weight updated for {file['file_name']}")
                            st.rerun()
                        else:
                            st.error(f"Failed to update weight for {file['file_name']}")
            with col4:
              #  role_names_update = role_names + ["No role"]
                new_role = st.selectbox(f"Current role: {metadata.get(file['file_name']).get('role', 'None')}", options=role_names, key=f"role_{file['file_name']}")
                if new_role != metadata.get(file['file_name']).get("role"):
                    if st.button("Update", key=f"update_role_{file['file_name']}"):
               #         if new_role == "No role":
                #            status = update_file_metadata(file['file_name'], {}, access_token)
                 #       else:
                        status = update_file_metadata(file['file_name'], {"role" : new_role}, access_token)
                        if status == 200:
                            st.success(f"Role updated for {file['file_name']}")
                            st.session_state['refresh_files'] = True
                            st.rerun()
                        else:
                            st.error(f"Failed to Role for {file['file_name']}")

        if st.checkbox("Delete Selected"):
            selected_files = [file['file_name'] for file in files if st.session_state.get(f"checkbox_{file['file_name']}")]
            if st.button(f"Are you sure you want to delete {len(selected_files)} files."):
                if selected_files:
                    for file_name in selected_files:
                        if delete_file(file_name, access_token):
                            st.session_state['message'] += f"Deleted {file_name}\n"
                        else:
                            st.error(f"Failed to delete {file_name}")
                    st.session_state['refresh_files'] = True
                    st.rerun()

    else:
        st.write("No files to display.")

if __name__ == "__main__":
    main()