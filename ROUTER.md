---
type: router
date: "2026-08-05"
tags: [graph, router, vault-operations]
status: active
---

# Graph Router — AI Session Entry Point

> Keep under 500 tokens. Read this first, every session.

## What This Is

This vault is a graph, not a pile. 5,434 indexed Markdown notes, organized by durable topic. The AI reads **this file first**, then uses the index or `.vault-index` before opening notes. It does NOT scan the whole vault.

## Quick Structure

| Folder | What It's For |
|--------|--------------|
| `00-Inbox/` | 2 deferred pipeline notes; `index.md` is the intake entry |
| `08-Learning/` | 3,596 notes — AI Agent, Knowledge Systems, Design, Finance, Papers |
| `10-LLM-Wiki/` | llm-wiki system and workflow |
| `09-Article-Notes/` | 363 article summaries — concept/workflow/guide/tool |
| `14-Skills/` | Pigo's built skills — vault org, agent eng, twitter watch |
| `18-Wealth/` | Investments, insurance, taxes, Taiwan stocks |
| `04-Archive/` | Done/dead content — don't read unless specifically asked |
| `03-Resources/` | Tool lists, prompt engineering, visual design |

## Session Rules

1. **Start here** — read this file, then `index.md` for the detailed map
2. **Route before reading** — use `.vault-index/query_vault.py` when the topic is unclear; open only the best matching notes
3. **Go narrow** — never scan `08-Learning/` broadly; follow one purposeful wikilink edge when needed
4. **Index maintenance** — new notes go to `00-Inbox/`, then file them to the right topic folder and rebuild the index
5. **State the result** — record changes, failures, and the next entry point in `state.md`

## State

See `state.md` for what happened in previous sessions.
