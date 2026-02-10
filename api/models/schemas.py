"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal
from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing status enum."""
    PENDING = "pending"
    CONVERTING = "converting"
    CHUNKING = "chunking"
    TRANSCRIBING = "transcribing"
    ALIGNING = "aligning"
    CONCATENATING = "concatenating"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioProcessRequest(BaseModel):
    """Request model for starting audio processing."""
    filename: str = Field(..., description="Name of the uploaded audio file")
    min_silence_len: int = Field(default=800, description="Minimum silence length in ms")
    manual_silence_len: int = Field(default=300, description="Manual silence interval in ms")
    silence_thresh: int = Field(default=-60, description="Silence threshold in dBFS")
    asr_model: str = Field(
        default="deepdml/faster-whisper-large-v3-turbo-ct2",
        description="ASR model to use"
    )


class AudioProcessResponse(BaseModel):
    """Response model for audio processing."""
    task_id: str
    status: ProcessingStatus
    message: str


class WordEntry(BaseModel):
    """Word entry with timestamps."""
    word: str
    start_time: float
    end_time: float


class TranscriptionResponse(BaseModel):
    """Response model for transcription data."""
    filename: str
    transcription: Dict[int, WordEntry]
    total_words: int


class AlignRequest(BaseModel):
    """Request model for audio alignment."""
    filename: str
    edited_json: Dict[int, WordEntry]


class AlignResponse(BaseModel):
    """Response model for audio alignment."""
    task_id: str
    status: str
    output_file: str
    original_segments: int
    removed_segments: int
    remaining_segments: int


class SSEMessage(BaseModel):
    """Server-Sent Event message."""
    event: str
    data: Dict
    
    
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
