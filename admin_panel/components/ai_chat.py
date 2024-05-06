import streamlit as st
from utils import get_chat_response


def main() -> None:
    st.title("AI Chatbot")
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
    
    access_token = st.session_state.get('access_token', '')
    if not access_token:
        st.warning("You are not logged in.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for user_msg, ai_msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(user_msg)
        with st.chat_message("assistant"):
            st.markdown(ai_msg)

    user_input = st.chat_input("What would you like to discuss?")
    if user_input:
        response = get_chat_response(user_input, st.session_state.chat_history, access_token)
        st.session_state.chat_history.append((user_input, response))
        st.rerun()


if __name__ == "__main__":
    main()