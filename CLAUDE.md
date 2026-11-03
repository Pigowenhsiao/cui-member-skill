# Pigo — Session Brain

## Identity
Pigo Hsiao。All responses in **Traditional Chinese** unless Pigo writes in English.

## Vault
- **Linux**: `~/Documents/Pigo_Obsidian`
- **Agent source**: `~/Documents/Agent`

## Current Priorities (2026-08-07)

**Active**
- Graph Engineering MOC — ROUTER/index/state 已整合，持續優化中
- KAW pipeline — 推文攝入後自動寫入 vault
- Vault 每週整理 cron（每週一 09:00）

**Family**
- 媽近期開刀（手術中/術後照護）
- 小孩申請澳洲留學 2027
- 爸爸肺炎正在加護病房中治療

**Tech/Work**
- NVIDIA driver 待修（local host）
- Autoresearch 已取消（GPU 資源釋出）

## Routing Rules

**Vault operations** → read `12-Meta/Vault-Skill-Router.md` first, then `14-Skills/vault-organization/`

**Priority order**:
1. Match skill in `14-Skills/vault-organization/`
2. Check `~/.codex/skills/`
3. Check `~/Documents/Agent`
4. Own judgment

**Plain-language triggers**:
- 「整理 inbox」「清 inbox」→「inbox-check」
- 「整理這篇」「升級這篇」→「note-update」
- 「vault 健檢」「審視 vault」→「vault-GPS」
- 「到期日」「deadline」→「deadline-summary」

## Vault Structure
```
00-Inbox/    — raw captures（入口）
Daily/       — daily notes
07-Daily/    — structured daily
08-Learning/ — 知識系統
10-LLM-Wiki/ — AI 論文索引
14-Skills/   — 技能定義
12-Meta/     — vault 治理
04-Archive/  — 封存
```

## Session Rules
- No new `STATUS_*.md` files — append to `STATUS_ALL.md`
- `/handover` → use `routines/Session-Handover-Template.md`
- Keep Pigo in control of decisions
- Communicate in plain language

## State Reference
See `state.md` for cross-session continuity and current project status.

## 核心摘要

Pigo Hsiao。All responses in **Traditional Chinese** unless Pigo writes in English.

## 關鍵知識點

- **Linux**: `~/Documents/Pigo_Obsidian`
- **Agent source**: `~/Documents/Agent`
- Graph Engineering MOC — ROUTER/index/state 已整合，持續優化中
- KAW pipeline — 推文攝入後自動寫入 vault
- Vault 每週整理 cron（每週一 09:00）
- 媽近期開刀（手術中/術後照護）
- 小孩申請澳洲留學 2027
- NVIDIA driver 待修（local host）
- Autoresearch 已取消（GPU 資源釋出）
1. Match skill in `14-Skills/vault-organization/`
2. Check `~/.codex/skills/`
3. Check `~/Documents/Agent`
4. Own judgment
- 「整理 inbox」「清 inbox」→「inbox-check」
- 「整理這篇」「升級這篇」→「note-update」