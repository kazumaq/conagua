#!/bin/bash
set -e

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Navigate to the directory containing the script
cd /repositories/conagua

# Activate virtual environment
source myenv/bin/activate

# Run the first script (fetch_dam_data.py)
log "Starting fetch_dam_data.py"
if python fetch_dam_data.py; then
    log "fetch_dam_data.py succeeded, running preprocessing.py"
    python preprocessing.py dam_data
    log "preprocessing.py completed"
else
    log "fetch_dam_data.py failed, not running preprocessing.py"
    deactivate  # Deactivate virtual environment before exiting
    exit 1
fi

log "All scripts completed successfully"

# Deactivate virtual environment
deactivate