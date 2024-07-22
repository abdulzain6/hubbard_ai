import streamlit as st
from utils import create_response, get_roles, get_chat_response_stream, get_chat_response

def main() -> None:
    st.title("Response Management")
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    roles = get_roles(access_token)
    role_names = [role["name"] for role in roles if role["name"]]
    
    if roles:
        selected_role = st.selectbox("Select Role", options=role_names)
    else:
        st.text("No roles found! Please add a role")
        
    question = st.text_input("Enter your question for AI:")

    if st.button("Generate Response"):
        if selected_role:
            with st.spinner("Generating responses..."):
                response1 = get_chat_response(question, [], access_token, role=selected_role, get_highest_ranking_response=False)
                response2 = get_chat_response(question, [], access_token, role=selected_role, get_highest_ranking_response=False)
                
                st.session_state['response1'] = response1
                st.session_state['response2'] = response2

    if 'response1' in st.session_state and 'response2' in st.session_state:
        st.markdown("### Response 1")
        st.write(st.session_state['response1'])
        
        st.markdown("### Response 2")
        st.write(st.session_state['response2'])
        
        selected_response = st.radio("Select the best response", ["Response 1", "Response 2", "Custom Response"], key="selected_response")
        
        if selected_response == "Custom Response":
            custom_response = st.text_area("Write your custom response here:")
        
        if st.button("Submit Best Response"):
            if selected_response == "Response 1":
                best_response = st.session_state['response1']
            elif selected_response == "Response 2":
                best_response = st.session_state['response2']
            else:
                best_response = custom_response
            
            create_response(question, best_response, access_token)
            st.success("Response saved successfully")

if __name__ == "__main__":
    main()
