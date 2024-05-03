import streamlit as st
from utils import get_chat_response

def main():
    st.title("AI Chatbot")
    
    access_token = st.session_state.get('access_token', '')
    if not access_token:
        st.warning("You are not logged in.")
        return
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("What would you like to discuss?"):
        # Update chat history with user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get AI response
        chat_history = [[msg["content"], ""] if msg["role"] == "user" else ["", msg["content"]] for msg in st.session_state.messages]
        response = get_chat_response(prompt, chat_history, st.session_state['access_token'])

        # Update chat history with AI response
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Force a rerun of the app to update the chat immediately
        st.rerun()

if __name__ == "__main__":
    main()
