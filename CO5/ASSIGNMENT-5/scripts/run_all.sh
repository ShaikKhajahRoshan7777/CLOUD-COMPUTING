#!/usr/bin/env bash
# Reproduce every Python result: runs each script, saves its output to results/*.txt and renders
# the VS Code style screenshot (screenshots/*.png), then rebuilds the figures from the new JSON.
set -e
cd "$(dirname "$0")/.."
python src/vscode_shot.py
python src/make_figures.py
