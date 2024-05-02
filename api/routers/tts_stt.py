import tempfile
import os
import tempfile
from typing import Any
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Depends, Form
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
from fastapi.responses import FileResponse
from api.auth import has_role
from ..globals import oauth2_scheme

router = APIRouter()

@router.post("/transcribe_audio")
@has_role(allowed_roles=["admin", "user"])
def transcribe_audio(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
) -> Any:

    try:
        deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
        options = PrerecordedOptions(model="nova", language="en", smart_format=True)
        audio_content = file.file.read()
        payload = {"buffer": audio_content}
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        resp = response.to_dict()
        transcript = resp.get("results", {}).get("channels", [])[0]["alternatives"][0]["transcript"]
        return {"transcript": transcript}
    except Exception as e:
        print(f"Error processing transcription request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the transcription request. Please try again later.")

@router.post("/generate_speech")
@has_role(allowed_roles=["admin", "user"])
def generate_speech(background_tasks: BackgroundTasks, text: str = Form(...), model: str = Form(default="aura-asteria-en") , token: str = Depends(oauth2_scheme)):
    try:
        # Create a Deepgram client using the API key from environment variables
        deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

        # Configure the options (such as model choice, audio configuration, etc.)
        options = SpeakOptions(
            model=model,
            encoding="linear16",
            container="wav"
        )

        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            # Save the generated speech to the temporary file
            deepgram.speak.v("1").save(tmp_file.name, {"text": text}, options)
            
            # Prepare to send the file back as a response
            tmp_file_path = tmp_file.name
        
        response = FileResponse(tmp_file_path, media_type='audio/wav', filename=os.path.basename(tmp_file_path))

        background_tasks.add_task(os.unlink, tmp_file_path)
        
        return response

    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating speech. Please try again later.")
