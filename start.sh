#!/bin/bash

# Error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Print environment info
echo "=== IMForwarder Bot Startup ==="
echo "Starting services..."
echo "Python version: $(python --version 2>&1)"
echo "Node version: $(node --version 2>/dev/null || echo 'Node not installed')"
echo "OS: $(uname -a 2>/dev/null || echo 'OS info unavailable')"

# Create log directory if it doesn't exist
mkdir -p logs

# Check Python dependencies
echo "Checking Python dependencies..."
python -c "
import sys
try:
    import pyrogram
    import telethon
    import aiohttp
    print('✓ Core dependencies OK')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
    print('Please run: pip install -r requirements.txt')
    sys.exit(1)
"

# Check environment variables
echo "Validating environment variables..."
python -c "
import os
import sys

required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f'✗ Missing required environment variables: {missing_vars}')
    sys.exit(1)

# Validate LOG_GROUP if present
log_group = os.getenv('LOG_GROUP')
if log_group:
    import re
    if not re.match(r'^-?\d+$', log_group):
        print(f'⚠️ Warning: LOG_GROUP value \"{log_group}\" contains non-numeric characters. Will be cleaned automatically.')
    
# Validate API_ID is numeric
try:
    int(os.getenv('API_ID', ''))
    print('✓ Environment variables OK')
except ValueError:
    print(f'✗ API_ID must be a number, got: {os.getenv(\"API_ID\")}')
    sys.exit(1)
"

# Function to start the Flask app
start_flask() {
    echo "Starting Flask app..."
    python app.py > logs/flask.log 2>&1 &
    FLASK_PID=$!
    echo "Flask app started with PID: $FLASK_PID"
    
    # Wait for Flask to start
    echo "Waiting for Flask to initialize..."
    sleep 3
    
    # Check if Flask is running
    if ! kill -0 $FLASK_PID 2>/dev/null; then
        echo "Flask failed to start. Check logs/flask.log for details."
        exit 1
    fi
}

# Function to start the Telegram bot
start_bot() {
    echo "Starting Telegram bot..."
    python main.py > logs/bot.log 2>&1 &
    BOT_PID=$!
    
    # Wait for bot to initialize
    sleep 5
    
    # Check if bot is still running
    if ! kill -0 $BOT_PID 2>/dev/null; then
        echo "Telegram bot failed to start. Fetching last 10 lines of log:"
        tail -n 10 logs/bot.log
        return 1
    fi
    
    # Monitor the bot process
    echo "Bot running with PID: $BOT_PID. Press Ctrl+C to stop."
    wait $BOT_PID
    BOT_EXIT_CODE=$?
    
    if [ $BOT_EXIT_CODE -ne 0 ]; then
        echo "Telegram bot exited with error code $BOT_EXIT_CODE"
        echo "Last 10 lines of logs/bot.log:"
        tail -n 10 logs/bot.log
        return 1
    fi
    
    return 0
}

# Cleanup function
cleanup() {
    echo "Shutting down services..."
    # Kill the flask app if it's running
    if [ ! -z "$FLASK_PID" ] && kill -0 $FLASK_PID 2>/dev/null; then
        echo "Shutting down Flask app (PID: $FLASK_PID)..."
        kill $FLASK_PID 2>/dev/null || echo "Flask app already stopped"
    fi
    
    # Kill the bot if it's running
    if [ ! -z "$BOT_PID" ] && kill -0 $BOT_PID 2>/dev/null; then
        echo "Shutting down Telegram bot (PID: $BOT_PID)..."
        kill $BOT_PID 2>/dev/null || echo "Bot already stopped"
    fi
    
    echo "=== IMForwarder Bot Shutdown Complete ==="
    exit 0
}

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Main execution flow
MAX_RETRIES=3
RETRY_COUNT=0

start_flask

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Starting bot (attempt $(($RETRY_COUNT + 1))/$MAX_RETRIES)..."
    
    if start_bot; then
        echo "Bot exited cleanly."
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "Retrying in 5 seconds..."
            sleep 5
        else
            echo "Maximum retry attempts reached. Please check the logs for errors."
        fi
    fi
done

# Wait for user to manually terminate
wait

# Cleanup is handled by the trap 