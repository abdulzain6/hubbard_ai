import streamlit as st
from utils import get_files, delete_file, upload_file

def main():
    st.title('File Management')
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    # Initialize session state for messages
    if 'message' not in st.session_state:
        st.session_state['message'] = None

    # Show messages if any
    if st.session_state['message']:
        st.success(st.session_state['message'])
        # Clear the message after showing it
        st.session_state['message'] = None

    # File upload section with a heading
    st.header('Upload New File')
    with st.form("file_upload"):
        uploaded_file = st.file_uploader("Choose a file")
        file_description = st.text_input("Description")
        weight = int(st.number_input("Weight", step=1, format='%d'))
        submit_button = st.form_submit_button("Upload File")

        if submit_button and uploaded_file:
            file_data = uploaded_file.getvalue()
            if upload_file(uploaded_file.name, file_data, file_description, weight, access_token):
                st.session_state['message'] = f"Uploaded {uploaded_file.name}"
                st.rerun()
            else:
                st.error(f"Failed to upload {uploaded_file.name}")

    # Heading for file listing
    st.header('File List')
    files = get_files(access_token)
    if files:
        for file in files:
            col1, col2 = st.columns([4, 1], gap="small")
            with col1:
                st.text(file['file_name'])
            with col2:
                if st.button("Delete", key=file['file_name']):
                    if delete_file(file['file_name'], access_token):
                        st.session_state['message'] = f"Deleted {file['file_name']}"
                        st.rerun()
                    else:
                        st.error(f"Failed to delete {file['file_name']}")
    else:
        st.write("No files to display.")

if __name__ == "__main__":
    main()
