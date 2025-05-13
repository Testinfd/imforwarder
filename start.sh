#!/bin/bash

# Print environment info
echo "Starting services..."
echo "Python version: $(python --version)"
echo "Node version: $(node --version 2>/dev/null || echo 'Node not installed')"

# Start the Flask app in the background
echo "Starting Flask app..."
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "Flask app started with PID: $FLASK_PID"

# Wait a moment to ensure Flask starts
sleep 2

# Start the Telegram bot with full output to console
echo "Starting Telegram bot..."
python main.py

# If the bot exits, kill the Flask app
echo "Telegram bot exited, shutting down Flask app..."
kill $FLASK_PID 