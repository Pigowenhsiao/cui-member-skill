#!/usr/bin/env python3
"""Fetch all toggle content from Notion page and save to JSON."""
import json, subprocess, time, sys
from pathlib import Path

PAGE_ID = "36142529-badd-8063-8aaa-f927c28eb620"
OUTPUT = Path.home() / "Downloads" / "toggles_raw.json"
NTN = str(Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "ntn" / "bin" / "ntn.exe")

def ntn_api(path):
    """Call ntn API and return parsed JSON."""
    result = subprocess.run(
        [NTN, "api", f"v1/{path}"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:200]}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        print(f"Raw: {result.stdout[:300]}", file=sys.stderr)
        return None

# Get all blocks
print("Fetching block list...")
data = ntn_api(f"blocks/{PAGE_ID}/children?page_size=100")
if not data:
    sys.exit(1)

all_blocks = data.get("results", [])
has_more = data.get("has_more", False)
cursor = data.get("next_cursor", None)

while has_more and cursor:
    print(f"  Fetching next page... ({len(all_blocks)} so far)")
    time.sleep(0.5)
    data = ntn_api(f"blocks/{PAGE_ID}/children?page_size=100&start_cursor={cursor}")
    if data:
        all_blocks.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor", None)

toggles = [b for b in all_blocks if b.get("type") == "toggle"]
print(f"Found {len(toggles)} toggle blocks")

# Fetch children for each toggle
results = []
for i, t in enumerate(toggles):
    block_id = t["id"]
    obj = t.get("toggle", {})
    title = "".join(tx["plain_text"] for tx in obj.get("rich_text", []))
    
    content = ""
    if t.get("has_children"):
        time.sleep(0.3)  # Rate limit
        children = ntn_api(f"blocks/{block_id}/children")
        if children:
            lines = []
            for child in children.get("results", []):
                ctype = child.get("type", "")
                cobj = child.get(ctype, {})
                ctext = "".join(tx.get("plain_text", "") for tx in cobj.get("rich_text", []))
                if ctext.strip():
                    lines.append(ctext)
            content = "\n\n".join(lines)
    
    results.append({
        "id": block_id,
        "title": title.strip(),
        "content": content.strip()
    })
    
    if (i + 1) % 20 == 0:
        print(f"  Progress: {i+1}/{len(toggles)}")

print(f"Fetched all {len(results)} toggle contents")

# Save raw
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Saved to {OUTPUT}")
