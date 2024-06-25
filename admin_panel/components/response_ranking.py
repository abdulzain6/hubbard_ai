import streamlit as st

from utils import create_response, get_roles, update_response, delete_response, list_responses, generate_response

def main() -> None:
    st.title("Response Management")
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    roles = get_roles(access_token)
    role_names = [role["name"] for role in roles]
    if roles:
        selected_role = st.selectbox("Select Role", options=role_names)
    else:
        st.text("No roles found! Please add a role")
        
    question = st.text_input("Enter your question for AI:")
    if st.button("Generate Response"):
            if selected_role:
                result, status_code = generate_response(question, access_token, role=selected_role)
                if status_code == 200:
                    st.success(f"AI Response: {result['ai_response']}")
                else:
                    st.error(f"Failed to generate response: {result.get('message', 'API Error')}")
    tab1, tab4 = st.tabs(["Create", "List"])

    with tab1:
        with st.form("create_response"):
            new_prompt = st.text_area("Prompt")
            new_response = st.text_area("Response")
            new_rank = st.number_input("Rank", min_value=1, value=1, step=1, format="%d")
            create_button = st.form_submit_button("Create")
            if create_button:
                result, status_code = create_response(new_prompt, new_response, new_rank, access_token)
                if status_code == 200:
                    st.success("Response created successfully.")
                else:
                    st.error(f"Failed to create response: {result.get('message', 'API Error')}")

    with tab4:
        st.subheader("List and Manage Responses")
        prompt = st.text_area("Prompt")
        if prompt:
            responses, status_code = list_responses(access_token, prompt)
            if status_code == 200:
                for response in responses:
                    with st.expander(f"Prompt: {response['prompt']} - Rank: {response['rank']}"):
                        updated_response = st.text_area("Response", value=response['response'], key=f"resp_{response['id']}")
                        updated_rank = st.number_input("Rank", value=response['rank'], key=f"rank_{response['id']}", step=1, format="%d")
                        update_button = st.button("Update", key=f"update_{response['id']}")
                        delete_button = st.button("Delete", key=f"delete_{response['id']}")

                        if update_button:
                            update_result, update_status_code = update_response(response['prompt'], response['rank'], updated_response, updated_rank, access_token)
                            if update_status_code == 200:
                                st.success("Response updated successfully.")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to update response: {update_result.get('message', 'API Error')}")

                        if delete_button:
                            delete_result, delete_status_code = delete_response(response['prompt'], response['rank'], access_token)
                            if delete_status_code == 204:
                                st.success("Response deleted successfully.")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to delete response: {delete_result.get('message', 'API Error')}")

if __name__ == "__main__":
    main()
