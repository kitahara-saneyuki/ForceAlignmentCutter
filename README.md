# ForceAlignmentCutter

A Python-based audio processing pipeline for Chinese (Mandarin) speech transcription and forced alignment. This tool converts video files to audio, segments them based on silence, transcribes using Whisper ASR, and performs forced alignment using Montreal Forced Aligner (MFA).

## Features

- **Video to Audio Conversion**: Convert MP4 videos to WAV audio format using FFmpeg
- **Smart Audio Segmentation**: Split audio files into chunks based on silence detection
- **Whisper ASR Transcription**: High-quality Chinese speech recognition using Faster-Whisper
- **Forced Alignment**: Precise word-level time alignment using Montreal Forced Aligner
- **Multiple Output Formats**: Generate SRT subtitles, JSON, or plain text transcriptions
- **GPU Acceleration**: CUDA support for faster transcription processing

## Prerequisites

- **Operating System**: Linux (Debian-based) or macOS
- **Hardware**: NVIDIA GPU (recommended for CUDA acceleration)
- **Software**:
  - [Conda](https://docs.conda.io/en/latest/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
  - FFmpeg
  - CUDA Toolkit (for GPU acceleration)

## Installation

### 1. Install Miniconda (if not already installed)

**For Debian/Ubuntu:**
```bash
make miniconda_debian
source ~/.bashrc
```

**For macOS:**
```bash
make miniconda_mac
source ~/.zprofile
```

### 2. Install System Dependencies

**For Debian/Ubuntu:**
```bash
make init_debian
```

**For macOS:**
```bash
make init_mac
```

### 3. Install CUDA Toolkit (Optional, for GPU acceleration)

```bash
make cuda
```

### 4. Create Conda Environment

This will install all Python dependencies and download required MFA models:

```bash
make conda_create
```

The environment includes:
- Python 3.11
- PyTorch with CUDA support
- `faster-whisper` for ASR
- Montreal Forced Aligner
- Audio processing libraries (pydub, sox, libsndfile)
- And other dependencies listed in `environment.yml`

### 5. Update Environment (when needed)

```bash
make conda_update
```

## Usage

### Basic Workflow

1. **Open the Jupyter Notebook:**
   ```bash
   conda activate ForceAlignmentCutter
   jupyter notebook src/asr.ipynb
   ```

2. **Configure Parameters:**
   
   Edit the configuration cell in the notebook:
   ```python
   ASR_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"
   MIN_SILENCE_LEN = 500  # Minimum silence length in ms
   SILENCE_THRESH = -60   # Silence threshold in dBFS
   ```

3. **Process Your Audio/Video:**
   
   Update the audio file path in the notebook:
   ```python
   audio_file = "../youtube/guardiola/your-video-file"
   mp42wav(audio_file)
   chunks = cut_blanks(audio_file, MIN_SILENCE_LEN, SILENCE_THRESH)
   audio_file_dir, audio_file_name = audio_paths(audio_file)
   
   for i in range(chunks):
       chunk_audio_file = f"{audio_file_dir}/chunks/{audio_file_name}_chunk{i}"
       transcribe_audio(chunk_audio_file, subtitle_format="txt")
   
   mfa(audio_file_dir)
   ```

### Output Files

The pipeline generates:
- `.wav` - Converted audio file
- `.srt` - SubRip subtitle file with timestamps
- `.json` - JSON format with structured subtitle data
- `.txt` - Plain text transcription
- `chunks/` - Directory containing segmented audio chunks and alignment results

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
│       ├── *.srt           # Generated subtitle files
│       └── chunks/         # Audio chunks and alignment results
├── environment.yml         # Conda environment specification
├── Makefile               # Build and setup commands
└── README.md              # This file
```

## Key Functions

### `mp42wav(audio_file)`
Converts MP4 video to WAV audio format.

### `cut_blanks(audio_file, min_silence_len, silence_thresh)`
Splits audio into chunks based on silence detection.
- `min_silence_len`: Minimum silence duration in milliseconds
- `silence_thresh`: Silence threshold in dBFS

### `transcribe_audio(audio_file, subtitle_format)`
Transcribes audio using Whisper ASR model.
- Supports formats: `"srt"`, `"json"`, `"txt"`
- Includes word-level timestamps
- Optimized for Mandarin Chinese

### `mfa(audio_file_dir)`
Performs forced alignment using Montreal Forced Aligner with Mandarin models.

## Configuration

### Whisper Model Options

You can change the ASR model in the notebook:
- `"deepdml/faster-whisper-large-v3-turbo-ct2"` (default, faster)
- `"XA9/Belle-faster-whisper-large-v3-zh-punct"` (with punctuation)

### Silence Detection Parameters

Adjust for different audio conditions:
- **MIN_SILENCE_LEN**: Increase for longer pauses, decrease for continuous speech
- **SILENCE_THRESH**: Lower values (e.g., -70) for noisy audio, higher (e.g., -50) for clean audio

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


