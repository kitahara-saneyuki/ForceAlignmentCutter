#!/bin/bash
# Start FastAPI server for ForceAlignmentCutter

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ForceAlignmentCutter

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start server
echo "Starting ForceAlignmentCutter API server..."
echo "Web interface: http://localhost:8000/static/index.html"
echo "API docs: http://localhost:8000/docs"
echo ""

python -m api.main
