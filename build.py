import os
import re
import json
import shutil

OBSIDIAN_LOGS_DIR = "/Users/cygnus/Library/Mobile Documents/iCloud~md~obsidian/Documents/Cygnus/1. Daily logs"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "data.js")
NOTES_DEST_DIR = os.path.join(BASE_DIR, "notes")

if not os.path.exists(NOTES_DEST_DIR):
    os.makedirs(NOTES_DEST_DIR)

heatmap_data = {}

for root, _, files in os.walk(OBSIDIAN_LOGS_DIR):
    for filename in files:
        if filename.endswith(".md"):
            # Match date format: (YYYY-MM-DD)
            match = re.search(r'\((\d{4}-\d{2}-\d{2})\)(.*)\.md', filename)
            if match:
                date_str = match.group(1)
                title_str = match.group(2).strip()
                if title_str.startswith("-"):
                    title_str = title_str[1:].strip()
                
                filepath = os.path.join(root, filename)
                
                dest_filename = filename
                dest_filepath = os.path.join(NOTES_DEST_DIR, dest_filename)
                rel_path = f"notes/{dest_filename}"

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # Calculate words
                    word_count = len(content.split())
                    heatmap_data[date_str] = {
                        "count": word_count,
                        "title": title_str,
                        "path": rel_path
                    }
                    
                    # Copy file to notes directory
                    shutil.copy2(filepath, dest_filepath)
                    
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

# Save data.js
js_content = f"const heatmapData = {json.dumps(heatmap_data, indent=2)};"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"Generated {OUTPUT_FILE} with {len(heatmap_data)} days of data.")
