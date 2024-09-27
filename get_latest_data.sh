#!/bin/bash
set -e

# Log file
LOG_FILE="/repositories/conagua/conagua_unified.log"

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
