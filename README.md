# ForceAlignmentCutter

A Python-based audio processing pipeline for Chinese (Mandarin) speech transcription, forced alignment, and audio editing. This tool converts video files to audio, segments them based on silence, transcribes using Whisper ASR, performs forced alignment using Montreal Forced Aligner (MFA), and enables manual editing of transcriptions to generate precisely aligned audio files.

## Deployment Options

### 🐳 Docker (Recommended for Production)
**NEW**: Containerized deployment with Docker and Docker Compose.

**Quick Start:**
```bash
# Development
make docker-up

# Production (with Nginx)
make docker-prod-up
```

**Benefits:**
- ✅ Consistent environment across systems
- ✅ GPU support with NVIDIA Container Toolkit
- ✅ Production-ready with Nginx reverse proxy
- ✅ Easy scaling and deployment

See [DOCKER.md](DOCKER.md) for complete Docker deployment guide.

### 🐍 Conda (Development)
Traditional Conda environment for local development.

```bash
make conda_create
make run_api
```

## Available Interfaces

### 🌐 Web API (FastAPI)
Process audio files through a RESTful API with real-time progress updates via Server-Sent Events (SSE).

- **Web Interface**: Simple HTML/JS client at `http://localhost:8000/static/index.html`
- **REST API**: RESTful endpoints for file upload, processing, and download
- **Real-time Progress**: SSE streaming for live processing updates
- **Interactive Docs**: Auto-generated API documentation at `http://localhost:8000/docs`

**With Docker:**
```bash
make docker-up
# Open http://localhost:8000/static/index.html
```

**With Conda:**
```bash
make run_api
# Open http://localhost:8000/static/index.html
```

See [API_README.md](API_README.md) for detailed API documentation.

### 📓 Jupyter Notebook
Traditional notebook interface for step-by-step audio processing.

```bash
conda activate ForceAlignmentCutter
jupyter notebook src/asr.ipynb
```

## Audio Processing Pipeline

1.  Preprocessing:
    1.  Smart Silence Removal
    1.  Whisper ASR Transcription: High-quality Chinese speech recognition using Faster-Whisper
    1.  Forced Alignment: Precise word-level time alignment using Montreal Forced Aligner
2.  Manual Editing:
    1.  Edit transcriptions and generate aligned audio with unwanted segments removed
3.  Generate SRT subtitles

## Environment

- **Operating System**: Linux (Debian-based) or macOS
- **Hardware**: NVIDIA GPU (recommended for CUDA acceleration)
- **Software**:
  - [Conda](https://docs.conda.io/en/latest/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
  - FFmpeg
  - CUDA Toolkit (for GPU acceleration)

## Installation for Debian/Ubuntu:**

```bash
make miniconda
source ~/.bashrc
make init
make cuda
make conda_create
```

The environment includes:
- Python 3.11
- PyTorch with CUDA support
- `faster-whisper` for ASR
- Montreal Forced Aligner
- Audio processing libraries (pydub, sox, libsndfile)
- And other dependencies listed in `environment.yml`

### Update Environment (when needed)

```bash
make conda_update
```

## Usage

### Complete Workflow

The pipeline follows these steps:

1. **Open the Jupyter Notebook:**
   ```bash
   conda activate ForceAlignmentCutter
   jupyter notebook src/asr.ipynb
   ```

2. **Configure Parameters:**
   
   Edit the configuration cell in the notebook:
   ```python
   ASR_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"
   MIN_SILENCE_LEN = 800        # Minimum silence length in ms for chunking
   MANUAL_SILENCE_LEN = 300     # Silence interval between combined chunks in ms
   SILENCE_THRESH = -60         # Silence threshold in dBFS
   ```

3. **Process Your Audio/Video:**
   
   Run the main workflow in the notebook:
   ```python
   audio_file = "../youtube/guardiola/your-video-file"
   audio_file_dir, audio_file_name = audio_paths(audio_file)
   
   # Step 1: Convert video to audio
   mp42m4a(audio_file)
   
   # Step 2: Split audio into chunks based on silence
   chunks = cut_blanks(audio_file, MIN_SILENCE_LEN, SILENCE_THRESH)
   
   # Step 3: Transcribe each chunk
   for i in range(chunks):
       chunk_audio_file = f"{audio_file_dir}/chunks/{audio_file_name}_chunk{i}"
       transcribe_audio(chunk_audio_file, subtitle_format="txt")
   
   # Step 4: Perform forced alignment on all chunks
   mfa(audio_file_dir)
   
   # Step 5: Concatenate chunks with word-level timestamps
   concatenate_audio_and_adjust_timestamps(audio_file, chunks)
   ```

4. **Manual Editing (Optional):**
   
   After the pipeline generates `{filename}_combined.json`, you can manually edit it to remove unwanted segments:
   - Open `{filename}_combined.json` in a text editor
   - Remove entries for words/segments you want to exclude from the final audio
   - Save the edited version as `{filename}_edited.json`
   
5. **Generate Aligned Audio:**
   
   Create the final audio file with unwanted segments removed:
   ```python
   align_audio_with_edited_json(
       f"{audio_file_dir}/{audio_file_name}_combined.json",
       f"{audio_file_dir}/{audio_file_name}_edited.json",
       f"{audio_file_dir}/{audio_file_name}_combined.m4a",
       f"{audio_file_dir}/{audio_file_name}_edited.m4a",
   )
   ```

### Output Files

The pipeline generates multiple files at different stages:

**Initial Processing:**
- `{filename}.m4a` - Converted audio file from video
- `chunks/{filename}_chunk{i}.wav` - Segmented audio chunks
- `chunks/{filename}_chunk{i}.txt` - Transcription for each chunk
- `chunks/{filename}_chunk{i}.json` - MFA alignment data for each chunk

**Combined Output:**
- `{filename}_combined.m4a` - Concatenated audio with silence intervals
- `{filename}_combined.json` - Word-level timestamps for all chunks in format:
  ```json
  {
    "0": {
      "word": "word_text",
      "start_time": 0.0,
      "end_time": 1.0
    },
    ...
  }
  ```

**Manual Editing:**
- `{filename}_edited.json` - Manually edited JSON (created by user)
- `{filename}_edited.m4a` - Final aligned audio with unwanted segments removed

### Manual Editing Workflow

The manual editing feature allows you to remove unwanted segments from your audio by editing the JSON file:

1. **Review the Combined JSON**: Open `{filename}_combined.json` to see all transcribed words with their timestamps

2. **Edit the JSON**: Create a copy as `{filename}_edited.json` and remove entries for:
   - Filler words (um, uh, etc.)
   - Mistakes or repeated phrases
   - Unwanted content or pauses
   - Any segments you want to exclude from the final audio

3. **Example Editing**:
   ```json
   // Original combined.json
   {
     "0": {"word": "今天", "start_time": 0.0, "end_time": 0.5},
     "1": {"word": "呃", "start_time": 0.5, "end_time": 0.8},  // Remove this
     "2": {"word": "天气", "start_time": 0.8, "end_time": 1.2},
     "3": {"word": "很好", "start_time": 1.2, "end_time": 1.7}
   }
   
   // Edited version (removed entry "1")
   {
     "0": {"word": "今天", "start_time": 0.0, "end_time": 0.5},
     "2": {"word": "天气", "start_time": 0.8, "end_time": 1.2},
     "3": {"word": "很好", "start_time": 1.2, "end_time": 1.7}
   }
   ```

4. **Generate Aligned Audio**: Run `align_audio_with_edited_json()` to create the final audio file with the unwanted segments removed

**Note**: The sequence numbers don't need to be renumbered - just remove the entries you don't want and keep the original sequence IDs for the remaining entries.

## Project Structure

```
ForceAlignmentCutter/
├── src/
│   ├── asr.ipynb           # Main notebook for ASR processing
│   └── utils/
│       ├── utils.py        # Utility functions (audio conversion, chunking)
│       └── __init__.py
├── youtube/
│   └── guardiola/          # Example video processing directory
│       ├── *.mp4           # Input video files
│       ├── *.m4a           # Converted audio files
│       ├── *_combined.m4a  # Concatenated audio output
│       ├── *_combined.json # Word-level timestamps
│       ├── *_edited.json   # Manually edited timestamps (user-created)
│       ├── *_edited.m4a    # Final aligned audio output
│       └── chunks/         # Audio chunks and MFA alignment results
│           ├── *_chunk0.wav
│           ├── *_chunk0.txt
│           ├── *_chunk0.json
│           └── ...
├── environment.yml         # Conda environment specification
├── Makefile               # Build and setup commands
├── plan.md                # Development roadmap
└── README.md              # This file
```

## Key Functions

### `mp42m4a(audio_file)`
Converts MP4 video to M4A audio format using FFmpeg.

### `cut_blanks(audio_file, min_silence_len, silence_thresh)`
Splits audio into chunks based on silence detection.
- `min_silence_len`: Minimum silence duration in milliseconds
- `silence_thresh`: Silence threshold in dBFS
- Returns: Number of chunks created

### `transcribe_audio(audio_file, subtitle_format)`
Transcribes audio using Whisper ASR model.
- Supports formats: `"srt"`, `"json"`, `"txt"`
- Includes word-level timestamps
- Optimized for Mandarin Chinese

### `mfa(audio_file_dir)`
Performs forced alignment using Montreal Forced Aligner with Mandarin models on all chunks in the directory.

### `concatenate_audio_and_adjust_timestamps(audio_file, chunks)`
Concatenates audio chunks with silence intervals and combines word-level timestamps.
- Adds `MANUAL_SILENCE_LEN` milliseconds of silence between chunks
- Adjusts timestamps to account for cumulative time
- Generates `{filename}_combined.m4a` and `{filename}_combined.json`

### `align_audio_with_edited_json(original_json, edited_json, original_audio, output_audio)`
Compares original and manually edited JSON files to generate aligned audio.
- Removes audio segments not present in the edited JSON
- Preserves timing of kept segments
- Useful for removing filler words, mistakes, or unwanted content

## Configuration

### Whisper Model Options

You can change the ASR model in the notebook:
- `"deepdml/faster-whisper-large-v3-turbo-ct2"` (default, faster)
- `"XA9/Belle-faster-whisper-large-v3-zh-punct"` (with punctuation)

### Silence Detection Parameters

Adjust for different audio conditions:
- **MIN_SILENCE_LEN** (default: 800ms): Controls how audio is chunked. Increase for longer pauses, decrease for continuous speech
- **MANUAL_SILENCE_LEN** (default: 300ms): Silence interval inserted between concatenated chunks
- **SILENCE_THRESH** (default: -60 dBFS): Lower values (e.g., -70) for noisy audio, higher (e.g., -50) for clean audio

## Current Status & Roadmap

### Completed Features ✓

The following backend features have been successfully implemented:

1. **ASR & Forced Alignment**: Using `faster-whisper` for transcription and Montreal Forced Aligner (MFA) to generate word-level timestamps
2. **Audio Concatenation**: Concatenate audio chunks with silence intervals and combine word-level timestamps into a single JSON file
3. **Manual Editing & Audio Alignment**: Compare original and manually edited JSON files to generate aligned audio with unwanted segments removed

### Planned Features

1. **Web Interface**: Refactor from Jupyter Notebook to FastAPI with web UI
   - Real-time progress updates using Server-Sent Events (SSE)
   - Upload audio files and edit transcriptions in browser
   - Download aligned audio files
2. **Scalable Backend**: RabbitMQ/Celery for asynchronous processing
3. **Flutter Frontend**: Cross-platform web interface for audio editing
4. **Deployment**: Production server deployment

## Troubleshooting

### CUDA Out of Memory
Reduce batch size or use CPU mode by changing:
```python
WHISPER_MODEL = WhisperModel(ASR_MODEL, device="cpu", compute_type="int8")
```

### MFA Alignment Errors
Ensure the audio quality is good and text transcription is accurate. Check the chunks directory for problematic segments.

### Environment Issues
Remove and recreate the conda environment:
```bash
make conda_remove
make conda_create
```

## Dependencies

Key Python packages:
- `faster-whisper`: Fast Whisper ASR implementation
- `montreal-forced-aligner`: Phonetic alignment tool
- `pydub`: Audio manipulation
- `transformers`: For model loading
- `torch`: PyTorch deep learning framework
- `yt-dlp`: YouTube video downloading (optional)

See `environment.yml` for the complete dependency list.

## License

This project uses various open-source models and libraries. Please ensure compliance with their respective licenses.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Montreal Forced Aligner](https://montreal-forced-aligner.readthedocs.io/) for alignment
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) for efficient inference


