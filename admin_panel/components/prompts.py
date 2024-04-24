import streamlit as st
from utils import list_prompts, delete_prompt, choose_main_prompt, update_prompt, create_prompt

def main():
    st.title("Prompt Template Management")
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    # Display prompts
    prompts = list_prompts(access_token)
    for idx, prompt in enumerate(prompts):
        prompt_key = f"{prompt['name']}_{idx}"  # Ensure unique key by appending index
        st.subheader(prompt['name'])
        st.text(f"Last updated: {prompt['last_updated']}")
        st.text_area("Content", value=prompt['content'], key=f"content_{prompt_key}")
        st.checkbox("Main prompt Template", value=prompt['is_main'], key=f"main_{prompt_key}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Update", key=f"update_{prompt_key}"):
                updated_content = st.session_state[f"content_{prompt_key}"]
                if update_prompt(prompt['name'], updated_content, access_token):
                    st.success("Updated successfully!")
                else:
                    st.error("Failed to update.")
        with col2:
            if st.button("Delete", key=f"delete_{prompt_key}"):
                if delete_prompt(prompt['name'], access_token):
                    st.rerun()
                else:
                    st.error("Failed to delete.")
        with col3:
            if st.button("Set as Main", key=f"set_main_{prompt_key}"):
                if choose_main_prompt(prompt['name'], access_token):
                    st.success("Main prompt Template chosen successfully!")
                    st.rerun()
                else:
                    st.error("Failed to set as main.")

    # Add new prompt
    with st.form("new_prompt"):
        new_name = st.text_input("New Prompt Name", key="new_prompt_name")
        new_content = st.text_area("Content", key="new_prompt_content")
        submit_new_prompt = st.form_submit_button("Create New Prompt Template")
        new_is_main = st.checkbox("Set as Main Prompt Template")

        if submit_new_prompt:
            success, msg = create_prompt(new_name, new_content, new_is_main, access_token)
            if success:
                st.success("Prompt Template created successfully!")
                st.rerun()
            else:
                st.error(f"Failed to create prompt Template. {msg}")

if __name__ == "__main__":
    main()
