"""Server-Sent Events (SSE) routes for real-time progress updates."""
import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.services.task_manager import task_manager

router = APIRouter(prefix="/api/sse", tags=["sse"])


async def event_generator(task_id: str):
    """Generate SSE events for a task."""
    task = task_manager.get_task(task_id)
    if not task:
        yield f"event: error\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
        return
    
    queue = task_manager.get_queue(task_id)
    if not queue:
        yield f"event: error\ndata: {json.dumps({'error': 'Task queue not found'})}\n\n"
        return
    
    # Send initial status
    yield f"event: status\ndata: {json.dumps({'status': task.status.value})}\n\n"
    
    # Send existing messages
    for msg in task.messages:
        yield f"event: progress\ndata: {json.dumps(msg)}\n\n"
    
    try:
        while True:
            # Wait for new messages with timeout
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                event_type = message.get("event", "message")
                data = message.get("data", {})
                
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                
                # If task is complete or failed, send final message and break
                if event_type in ["complete", "error"]:
                    break
                    
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield f": keepalive\n\n"
                
                # Check if task is complete
                if task.status in ["completed", "failed"]:
                    break
                    
    except asyncio.CancelledError:
        # Client disconnected
        pass
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.get("/stream/{task_id}")
async def stream_progress(task_id: str):
    """Stream real-time progress updates for a task using SSE."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return StreamingResponse(
        event_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/tasks")
async def list_tasks():
    """List all tasks."""
    tasks = []
    for task_id, task in task_manager.tasks.items():
        tasks.append({
            "task_id": task_id,
            "filename": task.filename,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        })
    return {"tasks": tasks}
