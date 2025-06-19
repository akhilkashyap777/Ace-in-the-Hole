#!/bin/bash
cd "$(dirname "$0")"
export KIVY_WINDOW=sdl2
export KIVY_GL_BACKEND=mock
export SDL_VIDEODRIVER=dummy
python main.py "$@"
