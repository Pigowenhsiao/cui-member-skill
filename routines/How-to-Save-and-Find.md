# How to Save / How to Find

> This folder is `routines/`. It holds the SOPs for how Pigo saves notes and how Pigo finds notes.
> These are the operating agreements that keep the vault from turning back into a pile.

---

## 1. How to Save a New Note

**Step 1: Where does it go first?**
Always `00-Inbox/`. Never skip the inbox. The inbox is the sorting area, not the final destination.

**Step 2: What name does it get?**
Format: `YYYY-MM-DD_source-type_slug.md`

Examples:
- `2026-08-04_x-note_unicode_graph-engineering.md`
- `2026-08-04_youtube_gary-chen-day1.md`
- `2026-08-04_paper-synthesis_sv101-models.md`

**Step 3: What frontmatter does it need?**
```yaml
---
type: note
date: "2026-08-04"
source: "<original URL if any>"
tags: [tag1, tag2]
status: draft
---
```

**Step 4: After saving to inbox, do four things:**
1. Add one line to `index.md` under the correct category
2. If the note belongs in `08-Learning/`, file it to the correct subfolder immediately (don't let it rot in inbox)
3. Add a line to `log.md` describing what was added
4. Rebuild `.vault-index/notes.db` and verify the new path is queryable

For a batch move, first save a Git checkpoint and a reversible move map. Do not merge, delete, or rewrite ambiguous notes in the same batch.

**Rule: If you can't explain in one sentence why a note exists, it shouldn't be a separate node.**

---

## 2. How to Find a Note

**When answering a question:**

1. Read `ROUTER.md` first (< 500 tokens)
2. Check `index.md` for the topic area
3. Go directly to that subfolder — don't scan `08-Learning/` broadly
4. Use `.vault-index/query_vault.py` for full-text search when topic is unclear
5. Open only the top matching note; follow one purposeful wikilink edge when the answer requires it
6. If the index is stale or empty, rebuild it before broadening the search

**When browsing:**
- `11-MOC/` — concept maps for cross-topic navigation
- `09-Article-Notes/` — structured article summaries
- `14-Skills/` — Pigo's own skill documentation

**When looking for a person:**
- `05-People/` — person nodes with key quotes and context

**When looking for tools:**
- `03-Resources/AI-Tools/` — curated tool list
- `14-Skills/` — Pigo's built skills

---

## 3. Filing Rules

**By topic, not by source.**

Source types (X/Twitter, YouTube, newsletter, arXiv, GitHub) are provenance metadata. They must NOT be the filing destination.

**Correct filing:**
- `@unicodef1wn Graph Engineering tweet` → `08-Learning/02_Knowledge-Systems/`
- `Gary Chen YouTube video` → `08-Learning/01_AI-Agent/` or relevant topic folder

**Only exceptions:**
- Unprocessed captures stay in `00-Inbox/`; historical migration records belong in `08-Learning/99_Maintenance/source-retired/`.
- Inbox captures that haven't been processed yet

---

## 4. What Makes a Good Node

| Good | Bad |
|------|-----|
| One idea per file | Mega-note with 10 topics |
| Title tells you exactly what's inside | Vague title like "Notes" or "Ideas" |
| Linked to related nodes | Orphan note with no connections |
| Has one clear question it answers | Dense wall of text |
| Under 500 lines | Over 1,000 lines |

**If a node grows past 500 lines, split it.**

---

## 5. Maintenance Triggers

The vault needs maintenance when:
- `00-Inbox/` has more than 50 notes (backlog risk)
- `index.md` hasn't been updated in 2 weeks
- You can't find a note you know exists (router/index gap)
- A folder has no README and you don't know what belongs there

See `12-Meta/` for maintenance scripts and health checks.

## 6. Verification and Recovery

Before a structural batch, record `git status`, the current commit, and a file manifest outside the Vault. After each batch, run the boundary check, rebuild the index, and inspect the changed paths. If verification fails, revert only the latest checkpoint commit or restore the corresponding move map; never delete the original note as part of the first pass.
