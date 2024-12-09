import streamlit as st
import streamlit.components.v1 as components
import os

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Load HTML file
    with open(os.path.join(current_dir, "index.html"), "r") as file:
        html_content = file.read()

    # Load JavaScript file
    with open(os.path.join(current_dir, "client.js"), "r") as file:
        js_content = file.read()

    # Combine HTML and JavaScript
    combined_content = f"{html_content}<script>{js_content}</script>"

    # Render the combined content
    components.html(combined_content, height=600)

if __name__ == "__main__":
    main()
