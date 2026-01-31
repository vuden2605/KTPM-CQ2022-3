#!/bin/bash

echo "========================================"
echo "🚀 STARTING OLLAMA SERVER..."
echo "========================================"

ollama serve &
OLLAMA_PID=$!

echo "⏳ Waiting 20s for Ollama server to start..."
sleep 20

echo "✅ Ollama server should be ready now!"

MODEL_NAME="gemma3:1b"
echo "========================================"
echo "📥 Pulling model '$MODEL_NAME'..."
echo "========================================"

ollama pull "$MODEL_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Model '$MODEL_NAME' pulled successfully!"
else
    echo "❌ Failed to pull model '$MODEL_NAME'"
    echo "🔄 Trying fallback model: gemma2:2b"
    ollama pull gemma2:2b
    
    if [ $? -eq 0 ]; then
        echo "✅ Fallback model gemma2:2b pulled successfully!"
        echo "⚠️  Using gemma2:2b instead of gemma3:1b"
    else
        echo "❌ Failed to pull any model"
        exit 1
    fi
fi

echo "========================================"
echo "📋 Available models:"
ollama list
echo "========================================"

echo "✅ Ollama is ready to serve requests!"
wait $OLLAMA_PID
