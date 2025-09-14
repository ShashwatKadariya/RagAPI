#!/bin/sh
set -e

# Start Ollama server in background
ollama serve &
SERVER_PID=$!

# Wait until Ollama server is ready
echo "Waiting for Ollama server to be ready..."
until curl -s http://localhost:11434/api/health; do
  sleep 1
done
echo "Ollama server is ready!"

# Pull Mistral model
ollama pull mistral

# Bring server process to foreground
wait $SERVER_PID
