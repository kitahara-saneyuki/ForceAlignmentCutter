# Plan

## Backend Implementation

1.  [x] Refactor the backend from Jupyter Notebook to Python FastAPI project. Using FastAPI to create a web interface for users to upload audio files and manually edit the ASR output JSON file, and then download the updated audio file. 
    1.  [x] The web interface should also support Server-Sent Events (SSE) to show the progress of the different processes in real-time.
    1.  [ ] Deploy the FastAPI application on a server and make it accessible to users.
1.  [ ] Using RabbitMQ / Celery to make the backend processes asynchronous and scalable, allowing for multiple users to upload and process their audio files simultaneously without blocking the server.

## Frontend Implementation

1.  [ ] Create a simple web interface using Flutter that allows users to upload audio files, view the ASR output JSON file, and manually edit it.
