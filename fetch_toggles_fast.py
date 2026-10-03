#!/usr/bin/env python3
"""Fast fetch all toggle content from Notion page."""
import json, subprocess, time, sys, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PAGE_ID = "36142529-badd-8063-8aaa-f927c28eb620"
OUTPUT = Path.home() / "Downloads" / "toggles_raw.json"
NTN = str(Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "ntn" / "bin" / "ntn.exe")

def ntn_api(path, retries=2):
    for attempt in range(retries):
        try:
            result = subprocess.run(
                [NTN, "api", f"v1/{path}"],
                capture_output=True, text=True, timeout=20
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            elif "429" in result.stderr or "rate" in result.stderr.lower():
                time.sleep(2)
                continue
        except Exception as e:
            time.sleep(1)
    return None

print("Fetching block list...")
data = ntn_api(f"blocks/{PAGE_ID}/children?page_size=100")
if not data:
    print("Failed to fetch blocks")
    sys.exit(1)

all_blocks = data.get("results", [])
has_more = data.get("has_more", False)
cursor = data.get("next_cursor", None)

while has_more and cursor:
    data = ntn_api(f"blocks/{PAGE_ID}/children?page_size=100&start_cursor={cursor}")
    if data:
        all_blocks.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor", None)
    else:
        break

toggles = [b for b in all_blocks if b.get("type") == "toggle"]
print(f"Found {len(toggles)} toggle blocks")

def fetch_toggle(t):
    block_id = t["id"]
    obj = t.get("toggle", {})
    title = "".join(tx["plain_text"] for tx in obj.get("rich_text", []))
    content = ""
    if t.get("has_children"):
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
    return {"id": block_id, "title": title.strip(), "content": content.strip()}

results = []
done = 0
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_toggle, t): t for t in toggles}
    for future in as_completed(futures):
        result = future.result()
        if result:
            results.append(result)
        done += 1
        if done % 20 == 0:
            print(f"  Progress: {done}/{len(toggles)}")

print(f"Fetched all {len(results)} toggle contents")
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Saved to {OUTPUT}")
