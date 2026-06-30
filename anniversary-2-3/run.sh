#!/bin/bash
echo "📦 Installing dependencies..."
pip install flask flask-cors pillow --break-system-packages -q
echo "💕 Starting Your Anniversary Website..."
echo "🌸 Open http://localhost:5555 in your browser"
python3 app.py
