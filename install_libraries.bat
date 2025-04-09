@echo off
echo Installing libraries and dependencies for Moodlifter...

:: Update pip
python -m pip install --upgrade pip

:: Install machine learning and NLP libraries
pip install transformers
pip install torch
pip install datasets


:: Install music API and audio libraries
pip install spotipy
pip install pydub
pip install requests
pip install langdetect
pip install ratelimit

:: Install web framework libraries
pip install flask
pip install streamlit


:: Done
echo Dependencies have been installed.
pause
