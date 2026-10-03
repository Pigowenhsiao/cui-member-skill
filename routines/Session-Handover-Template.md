---
type: template
title: "Session Handover"
tags: [template, routine, session]
date: "2026-08-07"
status: active
---

# /handover — Session Handover

> 每個 session 結束前使用。將上下文傳遞給下一個 session，確保連續性。

## 格式

```markdown
## ✅ 今日完成
- 

## 🎯 明日優先
- 

## 🚧 阻塞點
- 

## 📝 待記錄決定
- 

## 🔗 相關檔案
- 

## ⏰ 計時
- 開始：
- 結束：
- 耗時：
```

## 使用方式

1. 在 session 結束前，輸入 `/handover`
2. 系統自動填入時間戳（見下方）
3. 濃縮填寫每個區塊
4. 檔案自動存入：`07-Daily/YYYY-MM-DD_Handover.md`

## 自動產出欄位

| 欄位 | 說明 |
|------|------|
| 今日完成 | 這次 session 實際交付了什麼 |
| 明日優先 | 下一個 session 第一件事 |
| 阻塞點 | 無法推進的原因（Pigo 需要做的決定、外部依賴等）|
| 待記錄決定 | 任何討論中確立的結論 |
| 相關檔案 | 這次 session 觸及或修改的 vault 檔案 |
| 計時 | 自計，方便日後回顧時間分佈 |

## 範例

```markdown
## ✅ 今日完成
- 強化了 root CLAUDE.md（新增 Current Priorities、Routing Rules）
- 建立了 session handover template
- 確認 vault vs semichenkko 文章差距

## 🎯 明日優先
- 測試新版 CLAUDE.md 是否正常運作
- 決定是否要將 AGENTS.md 簡化或維護現狀

## 🚧 阻塞點
- 無

## 📝 待記錄決定
- CLAUDE.md 和 AGENTS.md 長期共存：CLAUDE.md = session brain，AGENTS.md = Codex runtime

## 🔗 相關檔案
- CLAUDE.md
- routines/Session-Handover-Template.md
- state.md

## ⏰ 計時
- 開始：2026-08-07 HH:MM
- 結束：2026-08-07 HH:MM
- 耗時：X 分鐘
```
