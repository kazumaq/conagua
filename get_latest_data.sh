#!/bin/bash
set -e

# Lock file
LOCK_FILE="/tmp/conagua_script.lock"
# Maximum age of lock file in seconds (2 hours)
MAX_LOCK_AGE=$((2 * 60 * 60))

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check and remove stale lock file
check_stale_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local file_age=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE")))
        if [ $file_age -gt $MAX_LOCK_AGE ]; then
            log "Removing stale lock file (age: $file_age seconds)"
            rm -f "$LOCK_FILE"
        fi
    fi
}

# Check for stale lock and remove if necessary
check_stale_lock

# Check if the script is already running
if [ -f "$LOCK_FILE" ]; then
    log "Script is already running. Exiting."
    exit 1
fi

# Create lock file
touch "$LOCK_FILE"

# Function to remove lock file on exit
cleanup() {
    log "Cleaning up..."
    rm -f "$LOCK_FILE"
}

# Set up trap to ensure cleanup happens even if script fails
trap cleanup EXIT

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
    log "fetch_dam_data.py failed or no new data, not running preprocessing.py"
    deactivate  # Deactivate virtual environment before exiting
    exit 1
fi

log "All scripts completed successfully"

# Deactivate virtual environment
deactivate

# Lock file will be automatically removed by the cleanup function