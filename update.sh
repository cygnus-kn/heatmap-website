#!/bin/bash

# Navigate to the correct directory
cd "$(dirname "$0")"

# Use virtual environment if it exists
if [ -d ".venv" ]; then
    PYTHON_CMD="./.venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

# 1. Run the python script to update data.js (from Obsidian notes)
$PYTHON_CMD build_notes.py

# 2. Run the python script to update steps_data.js (from the .db)
$PYTHON_CMD build_steps.py

# 4. Check for changes and commit/push if needed
git add data.js steps_data.js notes/*.md
if ! git diff --cached --quiet; then
    git commit -m "Update heatmap data: $(date '+%Y-%m-%d %H:%M:%S')"
    git push
    echo "Heatmap data updated and pushed successfully!"
else
    echo "No new data found. Everything is up to date."
fi
