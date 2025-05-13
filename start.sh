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
    if ! ps -p $FLASK_PID > /dev/null; then
        echo "Flask failed to start. Check logs/flask.log for details."
        exit 1
    fi
}

# Function to start the Telegram bot
start_bot() {
    echo "Starting Telegram bot..."
    python main.py > logs/bot.log 2>&1
    BOT_EXIT_CODE=$?
    
    if [ $BOT_EXIT_CODE -ne 0 ]; then
        echo "Telegram bot exited with error code $BOT_EXIT_CODE"
        echo "Check logs/bot.log for details"
        return 1
    fi
    
    return 0
}

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

# Cleanup
echo "Shutting down Flask app (PID: $FLASK_PID)..."
kill $FLASK_PID 2>/dev/null || echo "Flask app already stopped"

echo "=== IMForwarder Bot Shutdown Complete ===" 