"""Task manager for handling background processing tasks."""
import asyncio
import uuid
from typing import Dict, Optional, List, Callable
from datetime import datetime
from api.models.schemas import ProcessingStatus


class Task:
    """Represents a processing task."""
    
    def __init__(self, task_id: str, filename: str):
        self.task_id = task_id
        self.filename = filename
        self.status = ProcessingStatus.PENDING
        self.messages: List[Dict] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
        self.metadata: Dict = {}  # For storing arbitrary task metadata
    
    def add_message(self, message: str, level: str = "info"):
        """Add a progress message."""
        self.messages.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })
        self.updated_at = datetime.now()
    
    def update_status(self, status: ProcessingStatus):
        """Update task status."""
        self.status = status
        self.updated_at = datetime.now()
    
    def set_error(self, error: str):
        """Set task error."""
        self.error = error
        self.status = ProcessingStatus.FAILED
        self.updated_at = datetime.now()
    
    def set_result(self, result: Dict):
        """Set task result."""
        self.result = result
        self.status = ProcessingStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "filename": self.filename,
            "status": self.status.value,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "error": self.error
        }


class TaskManager:
    """Manages background processing tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
    
    def create_task(self, filename: str) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        task = Task(task_id, filename)
        self.tasks[task_id] = task
        self._queues[task_id] = asyncio.Queue()
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_queue(self, task_id: str) -> Optional[asyncio.Queue]:
        """Get the message queue for a task."""
        return self._queues.get(task_id)
    
    async def add_progress(self, task_id: str, message: str, level: str = "info"):
        """Add a progress message to a task."""
        task = self.get_task(task_id)
        if task:
            task.add_message(message, level)
            queue = self._queues.get(task_id)
            if queue:
                await queue.put({
                    "event": "progress",
                    "data": {
                        "message": message,
                        "level": level,
                        "status": task.status.value
                    }
                })
    
    async def update_status(self, task_id: str, status: ProcessingStatus):
        """Update task status."""
        task = self.get_task(task_id)
        if task:
            task.update_status(status)
            queue = self._queues.get(task_id)
            if queue:
                await queue.put({
                    "event": "status",
                    "data": {
                        "status": status.value
                    }
                })
    
    async def set_error(self, task_id: str, error: str):
        """Set task error."""
        task = self.get_task(task_id)
        if task:
            task.set_error(error)
            queue = self._queues.get(task_id)
            if queue:
                await queue.put({
                    "event": "error",
                    "data": {
                        "error": error
                    }
                })
    
    async def set_result(self, task_id: str, result: Dict):
        """Set task result."""
        task = self.get_task(task_id)
        if task:
            task.set_result(result)
            queue = self._queues.get(task_id)
            if queue:
                await queue.put({
                    "event": "complete",
                    "data": result
                })
    
    def create_progress_callback(self, task_id: str) -> Callable:
        """Create a progress callback function for a task."""
        def callback(message: str):
            # Create async task to add progress
            asyncio.create_task(self.add_progress(task_id, message))
        return callback
    
    def cleanup_task(self, task_id: str, keep_task_hours: int = 24):
        """Clean up old tasks."""
        task = self.get_task(task_id)
        if task:
            hours_old = (datetime.now() - task.created_at).total_seconds() / 3600
            if hours_old > keep_task_hours:
                del self.tasks[task_id]
                if task_id in self._queues:
                    del self._queues[task_id]


# Global task manager instance
task_manager = TaskManager()
