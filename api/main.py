"""FastAPI main application."""
import os
import warnings
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import audio, sse

# Suppress warnings
warnings.filterwarnings("ignore")
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    print("Starting ForceAlignmentCutter API server...")
    print("Server ready to accept requests")
    yield
    # Shutdown
    print("Shutting down ForceAlignmentCutter API server...")


# Create FastAPI app
app = FastAPI(
    title="ForceAlignmentCutter API",
    description="Audio processing pipeline with ASR transcription and forced alignment",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio.router)
app.include_router(sse.router)

# Serve static files (for web interface)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ForceAlignmentCutter API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/api/audio/upload",
            "process": "/api/audio/process",
            "transcription": "/api/audio/transcription/{filename}",
            "align": "/api/audio/align",
            "download": "/api/audio/download/{filename}",
            "task_status": "/api/audio/task/{task_id}",
            "stream": "/api/sse/stream/{task_id}",
            "tasks": "/api/sse/tasks"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
