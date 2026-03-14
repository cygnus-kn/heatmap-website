#!/bin/bash

# Navigate to the correct directory
cd "$(dirname "$0")"

# Run the python script to update data.js
python3 build.py

echo "Heatmap data updated successfully!"
