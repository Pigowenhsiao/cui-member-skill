#!/usr/bin/env python3
"""Incremental fetch - saves after every 50 entries."""
import json, subprocess, time, sys
from pathlib import Path

PAGE_ID = "36142529-badd-8063-8aaa-f927c28eb620"
OUTPUT = Path.home() / "Downloads" / "toggles_raw.json"
PROGRESS = Path.home() / "Downloads" / "toggles_progress.json"
NTN = str(Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "ntn" / "bin" / "ntn.exe")

def ntn(path):
    result = subprocess.run(
        [NTN, "api", f"v1/{path}"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except:
        return None

print("Fetching block list...", flush=True)
data = ntn(f"blocks/{PAGE_ID}/children?page_size=100")
if not data:
    sys.exit(1)

all_blocks = data.get("results", [])
while data.get("has_more") and data.get("next_cursor"):
    cursor = data["next_cursor"]
    data = ntn(f"blocks/{PAGE_ID}/children?page_size=100&start_cursor={cursor}")
    if data:
        all_blocks.extend(data.get("results", []))

toggles = [b for b in all_blocks if b.get("type") == "toggle"]
print(f"Found {len(toggles)} toggle blocks", flush=True)

# Load existing progress if any
if PROGRESS.exists():
    with open(PROGRESS) as f:
        results = json.load(f)
    start = len(results)
    print(f"Resuming from {start}", flush=True)
else:
    results = []
    start = 0

errors = 0
for i, t in enumerate(toggles[start:], start):
    block_id = t["id"]
    title = "".join(tx["plain_text"] for tx in t.get("toggle", {}).get("rich_text", []))
    content = ""
    if t.get("has_children"):
        children = ntn(f"blocks/{block_id}/children")
        if children:
            lines = []
            for child in children.get("results", []):
                ctype = child.get("type", "")
                cobj = child.get(ctype, {})
                ctext = "".join(tx.get("plain_text", "") for tx in cobj.get("rich_text", []))
                if ctext.strip():
                    lines.append(ctext)
            content = "\n\n".join(lines)
    if content:
        results.append({"id": block_id, "title": title.strip(), "content": content.strip()})
    else:
        errors += 1
    if (i + 1) % 50 == 0:
        with open(PROGRESS, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  Saved {i+1}/{len(toggles)} ({errors} empty)", flush=True)
    time.sleep(0.15)

with open(PROGRESS, "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
with open(OUTPUT, "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Done: {len(results)} with content, {errors} empty")
print(f"Saved to {OUTPUT}")
