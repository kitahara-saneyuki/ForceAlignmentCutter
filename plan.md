# Plan

## Backend Implementation

1.  [x] Using `faster-whisper` to transcribe the audio file into text and Montreal Forced Aligner (MFA) to generate a JSON file with word-level timestamps.
1.  [x] Concatenate audio files and the words with timestamps into a single file for MFA input(put in `chunks/{audio_file_name}_chunk{i}.wav`) and output JSONs(put in `chunks/{audio_file_name}_chunk{i}.json`, please read this json to understand MFA results), with specified interval of silence. For each word entries, we preserve a dictionary of the following format:
```json
{
    sequence[int]: {
        "word": "word_text",
        "start_time": 0.0,
        "end_time": 1.0
    }
}
```
1.  [x] Implement a function to compare two of the above-formatted JSON files: one from the ASR and MFA output, another one is manually edited with unused characters removed. The goal of this function is to remove the unused characters in the audio file and generate a new audio file that is aligned with the manually edited JSON file.
1.  [x] Refactor the backend from Jupyter Notebook to Python FastAPI project. Using FastAPI to create a web interface for users to upload audio files and manually edit the ASR output JSON file, and then download the updated audio file. 
    1.  [x] The web interface should also support Server-Sent Events (SSE) to show the progress of the different processes in real-time.
    1.  [x] Deploy the FastAPI application using Docker and Docker Compose for containerized deployment.
    1.  [x] Implement chunked upload (500KB chunks) with automatic retry logic for unreliable network connections
    1.  [x] Stream subprocess output (FFmpeg, MFA) to UI via SSE for real-time progress tracking
    1.  [ ] Deploy the FastAPI application on a production server and make it accessible to users.
1.  [~] ~~Using RabbitMQ / Celery to make the backend processes asynchronous and scalable~~ **CANCELLED** - Current FastAPI async implementation is sufficient for single-user workflow

## Frontend Implementation

1.  [ ] Create a Flutter application that allows users to upload audio files, view the ASR output JSON file, and manually edit it.
    - Flutter supports iOS (iPad), Android, Web, and Desktop (Windows, macOS, Linux)
    - **iPad full-stack deployment**: Use Briefcase to package FastAPI backend
      - **Architecture**: Embedded HTTP server approach
        1. Use `briefcase` to package FastAPI + uvicorn as native iOS app
        2. FastAPI runs on localhost (127.0.0.1:8000) within the app sandbox
        3. Flutter frontend connects to http://localhost:8000
        4. All processing happens on-device with Metal GPU acceleration
      - **Dependencies bundled**:
        - Python runtime via `python-apple-support`
        - FastAPI + uvicorn (HTTP server)
        - faster-whisper with Metal backend
        - FFmpeg compiled for iOS
        - Montreal Forced Aligner
        - pydub, torch, etc.
      - **Hardware**: 16GB iPad RAM sufficient for Whisper large models
      - **Distribution**: Can package as .ipa for App Store or TestFlight
      - **Internet requirements**:
        - First launch: Download Whisper model files (~2-3GB for large-v3)
        - Subsequent use: Fully offline after models cached locally
    - Can use same Flutter codebase for multiple platforms (API endpoint configurable)
    - **Development workflow**: Test on desktop first, then package for iOS

## Future Improvements

1.  [ ] 
