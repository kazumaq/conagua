#!/bin/bash
set -e

# Lock file and Log file
LOCK_FILE="/tmp/conagua_script.lock"
LOG_FILE="/repositories/conagua/conagua_unified.log"
MAX_LOCK_AGE=$((2 * 60 * 60))

# Function for logging
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] BASH - $1"
    echo "$message" >> "$LOG_FILE"
    echo "$message"  
}

# Rotate log file if it's larger than 10MB
if [ -f "$LOG_FILE" ] && [ $(du -m "$LOG_FILE" | cut -f1) -gt 10 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.$(date +'%Y%m%d_%H%M%S')"
    touch "$LOG_FILE"
    log "Log file rotated due to size"
fi

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

check_stale_lock

if [ -f "$LOCK_FILE" ]; then
    log "Script is already running. Exiting."
    exit 1
fi

touch "$LOCK_FILE"

cleanup() {
    log "Cleaning up..."
    rm -f "$LOCK_FILE"
}

trap cleanup EXIT

# Navigate to the project directory
cd /repositories/conagua

# Activate virtual environment
source myenv/bin/activate

# Test connection
log "Testing connection to CONAGUA server"
if python fetch_dam_data.py --test; then
    log "Connection test successful"
else
    log "Connection test failed. Check server status and network connection."
    deactivate
    exit 1
fi

log "Starting fetch_dam_data.py"
if python fetch_dam_data.py; then
    log "fetch_dam_data.py succeeded, running preprocessing.py"
    python preprocessing.py dam_data >> "$LOG_FILE" 2>&1
    log "preprocessing.py completed"
    python twitter_post.py >> "$LOG_FILE" 2>&1
    log "Finished posting to X"
else
    exit_code=$?
    log "fetch_dam_data.py failed with exit code $exit_code. Check the log file for more details."
    log "Last 20 lines of the log file:"
    tail -n 20 "$LOG_FILE" | while IFS= read -r line; do
        log "    $line"
    done
    deactivate
    exit 1
fi

log "All scripts completed successfully"

# Deactivate virtual environment
deactivate
