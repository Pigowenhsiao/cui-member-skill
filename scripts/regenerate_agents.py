#!/usr/bin/env python3
"""
regenerate_agents.py
===================
Reads .path-config.json → replaces {{VAR}} placeholders in AGENTS.md.template
→ writes AGENTS.md.

Usage:
    python scripts/regenerate_agents.py [--template AGENTS.md.template]

If --template is not specified, looks for AGENTS.md.template in the vault root.
If no template exists, reads the existing AGENTS.md and replaces any
{{...}} placeholders using .path-config.json values.
"""
import json, sys, re
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent.resolve()
CONFIG_FILE = VAULT_ROOT / ".path-config.json"
TEMPLATE_FILE = VAULT_ROOT / "AGENTS.md.template"
OUTPUT_FILE = VAULT_ROOT / "AGENTS.md"


def load_config():
    if not CONFIG_FILE.exists():
        print(f"[ERROR] {CONFIG_FILE} not found. Copy .path-config.json.example to .path-config.json and fill in your paths.")
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    # Filter out metadata keys
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_template(cfg):
    """Return template content. Falls back to existing AGENTS.md with {{VAR}} replacement."""
    if TEMPLATE_FILE.exists():
        print(f"[INFO] Using template: {TEMPLATE_FILE}")
        return TEMPLATE_FILE.read_text(encoding="utf-8")

    # Fallback: patch existing AGENTS.md
    if OUTPUT_FILE.exists():
        print(f"[INFO] No template found — patching existing AGENTS.md")
        return OUTPUT_FILE.read_text(encoding="utf-8")

    print(f"[ERROR] No template and no existing AGENTS.md found.")
    sys.exit(1)


def substitute(template: str, config: dict) -> str:
    """Replace {{VAR_NAME}} (case-insensitive) with config values."""
    def replacer(m):
        key = m.group(1).strip().upper()
        # Try exact match first, then case-insensitive
        val = config.get(key) or next((v for k, v in config.items() if k.upper() == key), None)
        if val is None:
            print(f"[WARN] No config value for {{{m.group(1)}}}, leaving as-is.")
            return m.group(0)
        return str(val)

    return re.sub(r"\{\{([^}]+)\}\}", replacer, template)


def main():
    print(f"[INFO] Vault root : {VAULT_ROOT}")
    print(f"[INFO] Config file: {CONFIG_FILE}")
    cfg = load_config()
    print(f"[INFO] Loaded {len(cfg)} config keys: {list(cfg.keys())}")

    template = load_template(cfg)
    result = substitute(template, cfg)

    OUTPUT_FILE.write_text(result, encoding="utf-8")
    print(f"[OK] AGENTS.md regenerated → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
