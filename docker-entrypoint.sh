#!/bin/bash
set -e

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate ForceAlignmentCutter

# Create necessary directories
mkdir -p /app/uploads
mkdir -p /app/static

# Execute the main command
exec "$@"
