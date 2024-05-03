import streamlit as st
from audio_recorder_streamlit import audio_recorder

def main():
    st.header("Audio Recorder")
    
    # Record audio from the browser
    audio_bytes = audio_recorder()
    
    # If there is audio data, display an audio player
    if audio_bytes:
        print("In")
        st.audio(audio_bytes, format="audio/wav")
        st.write("Audio recording successful!")

    st.write("Click the record button above to start recording.")

if __name__ == "__main__":
    main()
