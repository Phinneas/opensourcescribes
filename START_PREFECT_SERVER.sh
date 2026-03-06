#!/bin/bash
# Start a dedicated Prefect server for orchestration
# Usage: ./START_PREFECT_SERVER.sh

echo "================================================"
echo "Starting Dedicated Prefect Server"
echo "================================================"
echo "This will start a Prefect server on port 4200"
echo "After starting, run your flows with:"
echo "  export PREFECT_API_URL='http://127.0.0.1:4200/api'"
echo "  python3 orchestration.py"
echo "================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Start Prefect server
prefect server start
