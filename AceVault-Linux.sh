#!/bin/bash
cd "$(dirname "$0")"
export KIVY_WINDOW=sdl2
export KIVY_GL_BACKEND=mock
export SDL_VIDEODRIVER=dummy
export KIVY_NO_ARGS=1
export KIVY_METRICS_DENSITY=1
export KIVY_METRICS_FONTSCALE=1
python -c "
import os
os.environ['KIVY_WINDOW'] = 'sdl2'
os.environ['KIVY_GL_BACKEND'] = 'mock'
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Patch Kivy before importing
import sys
from unittest.mock import MagicMock

# Mock the window creation
sys.modules['kivy.core.window.window_sdl2'] = MagicMock()

# Now run the app
exec(open('main.py').read())
" "$@"
