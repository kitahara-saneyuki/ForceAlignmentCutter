# ForceAlignmentCutter API

FastAPI-based web service for audio processing, ASR transcription, and forced alignment with real-time progress updates via Server-Sent Events (SSE).

## Features

- **RESTful API**: Upload, process, and download audio files
- **Real-time Progress**: Server-Sent Events (SSE) for live processing updates
- **Background Processing**: Non-blocking audio processing pipeline
- **Web Interface**: Simple HTML/JS client for testing
- **Async Architecture**: Built on FastAPI with async/await support

## API Endpoints

### Audio Processing

- `POST /api/audio/upload` - Upload M4A audio file
- `POST /api/audio/process` - Start audio processing pipeline
- `GET /api/audio/transcription/{filename}` - Get transcription JSON
- `POST /api/audio/align` - Align audio with edited JSON
- `GET /api/audio/download/{filename}` - Download processed audio
- `GET /api/audio/task/{task_id}` - Get task status

### Server-Sent Events

- `GET /api/sse/stream/{task_id}` - Stream real-time progress updates
- `GET /api/sse/tasks` - List all tasks

### General

- `GET /` - API information
- `GET /health` - Health check

## Installation

### Option 1: Docker (Recommended)

**Quick Start:**
```bash
# Development mode
make docker-up
# Open http://localhost:8000/static/index.html

# Production mode (with Nginx)
make docker-prod-up
# Open http://localhost/static/index.html
```

See [DOCKER.md](DOCKER.md) for complete Docker deployment guide.

### Option 2: Conda Environment

#### 1. Install FastAPI Dependencies

```bash
conda activate ForceAlignmentCutter
pip install -r requirements-api.txt
```

Or update the conda environment:

```bash
conda env update -f environment.yml
```

#### 2. Create Upload Directory

```bash
mkdir -p uploads
```

## Running the Server

### Development Mode

```bash
conda activate ForceAlignmentCutter
python -m api.main
```

Or with uvicorn directly:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Using the Web Interface

1. Start the server
2. Open browser to: `http://localhost:8000/static/index.html`
3. Upload an M4A audio file
4. Configure processing parameters
5. Click "Start Processing" and watch real-time progress
6. Edit the JSON transcription
7. Generate aligned audio
8. Download the results

## API Usage Examples

### Upload File

```bash
curl -X POST "http://localhost:8000/api/audio/upload" \
  -F "file=@audio.m4a"
```

### Start Processing

```bash
curl -X POST "http://localhost:8000/api/audio/process" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.m4a",
    "min_silence_len": 800,
    "manual_silence_len": 300,
    "silence_thresh": -60,
    "asr_model": "deepdml/faster-whisper-large-v3-turbo-ct2"
  }'
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Processing started"
}
```

### Stream Progress (SSE)

```bash
curl -N "http://localhost:8000/api/sse/stream/550e8400-e29b-41d4-a716-446655440000"
```

Or in JavaScript:

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/sse/stream/550e8400-e29b-41d4-a716-446655440000'
);

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log('Progress:', data.message);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('Complete:', data);
  eventSource.close();
});
```

### Align Audio

```bash
curl -X POST "http://localhost:8000/api/audio/align" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.m4a",
    "edited_json": {
      "0": {"word": "今天", "start_time": 0.0, "end_time": 0.5},
      "2": {"word": "天气", "start_time": 0.8, "end_time": 1.2}
    }
  }'
```

### Download File

```bash
curl -O "http://localhost:8000/api/audio/download/audio_edited.m4a"
```

## Project Structure

```
api/
├── __init__.py
├── main.py              # FastAPI application
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic models
├── routes/
│   ├── __init__.py
│   ├── audio.py         # Audio processing endpoints
│   └── sse.py           # SSE streaming endpoints
└── services/
    ├── __init__.py
    ├── asr_service.py   # ASR and MFA processing
    ├── audio_service.py # Audio manipulation
    └── task_manager.py  # Background task management
```

## Configuration

### Processing Parameters

- **min_silence_len** (default: 800ms): Minimum silence duration for chunking
- **manual_silence_len** (default: 300ms): Silence interval between concatenated chunks
- **silence_thresh** (default: -60 dBFS): Silence detection threshold
- **asr_model**: Whisper model to use
  - `deepdml/faster-whisper-large-v3-turbo-ct2` (faster, default)
  - `XA9/Belle-faster-whisper-large-v3-zh-punct` (with punctuation)

## SSE Event Types

- `status` - Task status update
- `progress` - Processing progress message
- `complete` - Processing completed with results
- `error` - Error occurred

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad request (e.g., invalid file type)
- `404` - Resource not found (file or task)
- `500` - Internal server error

Error response format:

```json
{
  "error": "Error message",
  "detail": "Additional details (optional)"
}
```

## CORS Configuration

By default, CORS is enabled for all origins in development. For production, update the CORS settings in `api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Considerations

- **GPU Acceleration**: Ensure CUDA is available for faster transcription
- **Concurrent Tasks**: Multiple users can process files simultaneously
- **File Cleanup**: Implement periodic cleanup of old files in `uploads/` directory
- **Task Cleanup**: Old tasks are automatically cleaned up (configurable in `task_manager.py`)

## Troubleshooting

### Port already in use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

### CUDA out of memory

Adjust the ASR model or use CPU mode by modifying `asr_service.py`:

```python
self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
```

## Next Steps

- Add authentication and authorization
- Implement file upload limits and validation
- Add RabbitMQ/Celery for distributed task processing
- Create production deployment configuration
- Add comprehensive error logging
- Implement rate limiting
