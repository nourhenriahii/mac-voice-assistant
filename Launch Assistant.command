#!/bin/bash
# Double-click this file to install (first time) and launch the assistant.
# No Terminal knowledge needed.

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Setting things up for the first time, this may take a few minutes..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --quiet -r requirements.txt
    pip install --quiet rumps
else
    source venv/bin/activate
fi

if ! command -v brew &> /dev/null; then
    echo "Note: Homebrew isn't installed. If the microphone doesn't work, install PortAudio manually: brew install portaudio"
elif ! brew list portaudio &> /dev/null; then
    echo "Installing PortAudio (needed for the microphone)..."
    brew install portaudio
fi

python menubar_app.py
