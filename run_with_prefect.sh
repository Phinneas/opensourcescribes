#!/bin/bash
# This script properly starts Prefect server and runs orchestration
# Usage: ./run_with_prefect.sh [orchestration|pipeline]

set -e  # Exit on error

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
cd "$SCRIPTPATH" || exit 1

# Default to orchestration if no argument provided
FLOW="${1:-orchestration}"

case $FLOW in
    "orchestration")
        PYTHON_SCRIPT="orchestration.py"
        ;;
    "pipeline")
        PYTHON_SCRIPT="pipeline.py"
        ;;
    *)
        echo "Usage: $0 [orchestration|pipeline]"
        echo "Default: orchestration"
        exit 1
        ;;
esac

echo "================================================"
echo "Prefect Server + $FLOW Flow Runner"
echo "================================================"
echo "Starting Prefect Server..."

# Check if Prefect server is already running
if curl -s http://127.0.0.1:4200/api > /dev/null 2>&1; then
    echo "Prefect server already running on port 4200"
    echo "Using existing server..."
else
    # Start Prefect server in background
    source venv/bin/activate
    prefect server start > /tmp/prefect_server.log 2>&1 &
    PREFECT_PID=$!

    echo "Waiting for Prefect server to start..."
    
    # Wait for server to be ready (up to 30 seconds)
    for i in {1..30}; do
        if curl -s http://127.0.0.1:4200/api > /dev/null 2>&1; then
            echo "Prefect server started successfully (PID: $PREFECT_PID)"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "Prefect server failed to start. Check /tmp/prefect_server.log"
            cat /tmp/prefect_server.log
            kill $PREFECT_PID 2>/dev/null
            exit 1
        fi
        sleep 1
    done
fi

echo "================================================"
echo "Starting $FLOW pipeline..."
echo "================================================"

# Run orchestration with proper environment
export PREFECT_API_URL="http://127.0.0.1:4200/api"
source venv/bin/activate
python3 "$PYTHON_SCRIPT"

EXITCODE=$?

# Only kill server if we started it
if [ -n "$PREFECT_PID" ]; then
    echo "================================================"
    echo "Stopping Prefect server (PID: $PREFECT_PID)..."
    kill $PREFECT_PID 2>/dev/null || echo "Server already stopped"
    echo "Done!"
fi

exit $EXITCODE
