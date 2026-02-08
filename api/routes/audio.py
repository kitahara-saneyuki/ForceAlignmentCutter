"""API routes for audio processing."""
import os
import json
import asyncio
import uuid
from typing import Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import StreamingResponse, FileResponse
from api.models.schemas import (
    AudioProcessRequest,
    AudioProcessResponse,
    TranscriptionResponse,
    AlignRequest,
    AlignResponse,
    ProcessingStatus,
    ErrorResponse
)
from api.services.asr_service import ASRService
from api.services.audio_service import AudioService
from api.services.task_manager import task_manager

router = APIRouter(prefix="/api/audio", tags=["audio"])

# Storage directory for uploaded files
UPLOAD_DIR = "uploads"
CHUNK_DIR = "uploads/chunks"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)


@router.post("/upload", response_model=Dict)
async def upload_audio(file: UploadFile = File(...)):
    """Upload an M4A audio file."""
    if not file.filename.endswith('.m4a'):
        raise HTTPException(status_code=400, detail="Only M4A files are supported")
    
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "filename": file.filename,
        "path": file_path,
        "size": len(content),
        "message": "File uploaded successfully"
    }


@router.post("/upload-init", response_model=Dict)
async def init_chunked_upload(
    filename: str = Form(...),
    total_size: int = Form(...),
    total_chunks: int = Form(...)
):
    """Initialize chunked upload and return task_id for progress tracking."""
    if not filename.endswith('.m4a'):
        raise HTTPException(status_code=400, detail="Only M4A files are supported")
    
    # Create upload task
    task_id = task_manager.create_task(f"upload_{filename}")
    
    # Create chunk directory for this upload
    upload_chunk_dir = os.path.join(CHUNK_DIR, task_id)
    os.makedirs(upload_chunk_dir, exist_ok=True)
    
    # Store metadata
    metadata = {
        "filename": filename,
        "total_size": total_size,
        "total_chunks": total_chunks,
        "received_chunks": 0,
        "received_chunk_indices": set(),  # Track which specific chunks received
        "upload_chunk_dir": upload_chunk_dir
    }
    
    # Store in task manager (we'll use this to track progress)
    task_manager.tasks[task_id].metadata = metadata
    
    await task_manager.update_status(task_id, ProcessingStatus.PENDING)
    await task_manager.add_progress(task_id, f"📤 Upload initialized: {filename} ({total_size / (1024*1024):.2f} MB, {total_chunks} chunks)")
    
    return {
        "task_id": task_id,
        "filename": filename,
        "chunk_size": 5 * 1024 * 1024,  # 5MB
        "message": "Chunked upload initialized"
    }


@router.post("/upload-chunk", response_model=Dict)
async def upload_chunk(
    task_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...)
):
    """Upload a single chunk (idempotent - handles retries)."""
    if task_id not in task_manager.tasks:
        raise HTTPException(status_code=404, detail="Upload task not found")
    
    task = task_manager.tasks[task_id]
    metadata = task.metadata
    
    # Check if this is a retry (chunk already received)
    is_retry = chunk_index in metadata["received_chunk_indices"]
    
    # Save chunk (overwrite if retry)
    chunk_path = os.path.join(metadata["upload_chunk_dir"], f"chunk_{chunk_index:04d}")
    with open(chunk_path, "wb") as buffer:
        content = await chunk.read()
        buffer.write(content)
    
    # Update progress only if this is a new chunk
    if not is_retry:
        metadata["received_chunk_indices"].add(chunk_index)
        metadata["received_chunks"] = len(metadata["received_chunk_indices"])
    
    received = metadata["received_chunks"]
    total = metadata["total_chunks"]
    progress_pct = (received / total) * 100
    
    # Log message
    if is_retry:
        await task_manager.add_progress(
            task_id,
            f"🔄 Chunk {chunk_index + 1} re-uploaded ({received}/{total} total, {progress_pct:.1f}%)"
        )
    else:
        await task_manager.add_progress(
            task_id,
            f"📦 Chunk {received}/{total} received ({progress_pct:.1f}%)"
        )
    
    # If all chunks received, merge them
    if received == total:
        await task_manager.add_progress(task_id, "🔄 Merging chunks...")
        
        final_path = os.path.join(UPLOAD_DIR, metadata["filename"])
        
        # Merge chunks in order
        with open(final_path, "wb") as outfile:
            for i in range(total):
                chunk_path = os.path.join(metadata["upload_chunk_dir"], f"chunk_{i:04d}")
                with open(chunk_path, "rb") as infile:
                    outfile.write(infile.read())
        
        # Clean up chunks
        import shutil
        shutil.rmtree(metadata["upload_chunk_dir"])
        
        file_size = os.path.getsize(final_path)
        await task_manager.set_result(task_id, {
            "filename": metadata["filename"],
            "path": final_path,
            "size": file_size,
            "message": "Upload completed successfully"
        })
        await task_manager.add_progress(task_id, f"✅ Upload complete: {file_size / (1024*1024):.2f} MB")
        
        return {
            "status": "completed",
            "filename": metadata["filename"],
            "size": file_size,
            "message": "All chunks received and merged"
        }
    
    return {
        "status": "in_progress",
        "received_chunks": received,
        "total_chunks": total,
        "progress": progress_pct
    }



async def process_audio_background(
    task_id: str,
    audio_path: str,
    min_silence_len: int,
    manual_silence_len: int,
    silence_thresh: int,
    asr_model: str
):
    """Background task for audio processing."""
    try:
        await task_manager.update_status(task_id, ProcessingStatus.CONVERTING)
        
        # Create ASR service
        asr_service = ASRService(model_name=asr_model)
        
        # Create progress callback
        def progress_callback(message: str):
            asyncio.create_task(task_manager.add_progress(task_id, message))
        
        # Process audio file
        await task_manager.update_status(task_id, ProcessingStatus.CHUNKING)
        await task_manager.add_progress(task_id, "Starting audio processing pipeline...")
        
        # Run synchronous processing in executor
        loop = asyncio.get_event_loop()
        combined_audio, combined_json = await loop.run_in_executor(
            None,
            asr_service.process_audio_file,
            audio_path,
            min_silence_len,
            manual_silence_len,
            silence_thresh,
            progress_callback
        )
        
        # Load and return result
        with open(combined_json, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        
        result = {
            "combined_audio": combined_audio,
            "combined_json": combined_json,
            "total_words": len(transcription_data),
            "transcription": transcription_data
        }
        
        await task_manager.set_result(task_id, result)
        
    except Exception as e:
        await task_manager.set_error(task_id, str(e))


@router.post("/process", response_model=AudioProcessResponse)
async def process_audio(
    request: AudioProcessRequest,
    background_tasks: BackgroundTasks
):
    """Start audio processing pipeline."""
    audio_path = os.path.join(UPLOAD_DIR, request.filename.replace('.m4a', ''))
    
    if not os.path.exists(f"{audio_path}.m4a"):
        raise HTTPException(status_code=404, detail=f"Audio file not found: {request.filename}")
    
    # Create task
    task_id = task_manager.create_task(request.filename)
    
    # Start background processing
    background_tasks.add_task(
        process_audio_background,
        task_id,
        audio_path,
        request.min_silence_len,
        request.manual_silence_len,
        request.silence_thresh,
        request.asr_model
    )
    
    return AudioProcessResponse(
        task_id=task_id,
        status=ProcessingStatus.PENDING,
        message="Processing started"
    )


@router.get("/transcription/{filename}", response_model=TranscriptionResponse)
async def get_transcription(filename: str):
    """Get transcription JSON for a processed file."""
    json_path = os.path.join(UPLOAD_DIR, filename.replace('.m4a', '_combined.json'))
    
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        transcription = json.load(f)
    
    return TranscriptionResponse(
        filename=filename,
        transcription=transcription,
        total_words=len(transcription)
    )


async def align_audio_background(
    task_id: str,
    filename: str,
    edited_json: Dict
):
    """Background task for audio alignment."""
    try:
        await task_manager.update_status(task_id, ProcessingStatus.ALIGNING)
        await task_manager.add_progress(task_id, "Starting audio alignment...")
        
        base_path = os.path.join(UPLOAD_DIR, filename.replace('.m4a', ''))
        original_json_path = f"{base_path}_combined.json"
        edited_json_path = f"{base_path}_edited.json"
        original_audio_path = f"{base_path}_combined.m4a"
        output_audio_path = f"{base_path}_edited.m4a"
        
        # Save edited JSON
        with open(edited_json_path, 'w', encoding='utf-8') as f:
            json.dump(edited_json, f, ensure_ascii=False, indent=2)
        
        # Create progress callback
        def progress_callback(message: str):
            asyncio.create_task(task_manager.add_progress(task_id, message))
        
        # Run alignment in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            AudioService.align_audio_with_edited_json,
            original_json_path,
            edited_json_path,
            original_audio_path,
            output_audio_path,
            progress_callback
        )
        
        result["task_id"] = task_id
        result["status"] = "completed"
        
        await task_manager.set_result(task_id, result)
        
    except Exception as e:
        await task_manager.set_error(task_id, str(e))


@router.post("/align", response_model=AlignResponse)
async def align_audio(
    request: AlignRequest,
    background_tasks: BackgroundTasks
):
    """Align audio based on edited JSON."""
    base_path = os.path.join(UPLOAD_DIR, request.filename.replace('.m4a', ''))
    
    if not os.path.exists(f"{base_path}_combined.json"):
        raise HTTPException(status_code=404, detail="Original transcription not found")
    
    if not os.path.exists(f"{base_path}_combined.m4a"):
        raise HTTPException(status_code=404, detail="Combined audio not found")
    
    # Create task
    task_id = task_manager.create_task(request.filename)
    
    # Start background alignment
    background_tasks.add_task(
        align_audio_background,
        task_id,
        request.filename,
        request.edited_json
    )
    
    return AlignResponse(
        task_id=task_id,
        status="processing",
        output_file=f"{request.filename.replace('.m4a', '_edited.m4a')}",
        original_segments=0,
        removed_segments=0,
        remaining_segments=0
    )


@router.get("/download/{filename}")
async def download_audio(filename: str):
    """Download a processed audio file."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="audio/mp4"
    )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and details."""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()
