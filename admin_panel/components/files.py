import streamlit as st
from utils import get_files, delete_file, upload_file

def main():
    st.title('File Managementt')
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    # Initialize session state for messages
    if 'message' not in st.session_state:
        st.session_state['message'] = ''

    # File upload section with a heading
    st.header('Upload New File')
    with st.form("file_upload"):
        uploaded_file = st.file_uploader("Choose a file")
        file_description = st.text_input("Description", value=st.session_state.get('last_description', ''))
        weight = st.number_input("Weight", value=st.session_state.get('last_weight', 0), step=1, format='%d')
        submit_button = st.form_submit_button("Upload File")

        if submit_button and uploaded_file:
            file_data = uploaded_file.getvalue()
            if upload_file(uploaded_file.name, file_data, file_description, weight, access_token):
                st.session_state['message'] = f"Uploaded {uploaded_file.name}"
                st.session_state['last_description'] = file_description
                st.session_state['last_weight'] = weight
                st.rerun()
            else:
                st.error(f"Failed to upload {uploaded_file.name}")

    if st.session_state['message']:
        st.success(st.session_state['message'])
        st.session_state['message'] = ''  # Clear the message after showing it

    # Heading for file listing
    st.header('File List')
    sort_order = st.selectbox("Sort by", ['A to Z', 'Weight (Highest to Lowest)'])
    files = get_files(access_token)

    if files:
        if sort_order == 'A to Z':
            files.sort(key=lambda x: x['file_name'])
        else:
            files.sort(key=lambda x: x['weight'], reverse=True)

        selected_files = []
        for file in files:
            col1, col2 = st.columns([1, 9])
            with col1:
                selected = st.checkbox("Select", key=f"checkbox_{file['file_name']}", label_visibility="hidden")
                if selected:
                    selected_files.append(file['file_name'])
            with col2:
                st.text(file['file_name'])


        if selected_files and st.checkbox("Delete Selected"):
            if st.button(f"Confirm deletion of {len(selected_files)} selected files?", key="batch_delete_confirm"):
                print(selected_files)
                for file_name in selected_files:
                    if delete_file(file_name, access_token):
                        st.session_state['message'] += f"Deleted {file_name}\n"
                    else:
                        st.error(f"Failed to delete {file_name}")
                st.rerun()

    else:
        st.write("No files to display.")

if __name__ == "__main__":
    main()
