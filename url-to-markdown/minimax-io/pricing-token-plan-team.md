---
title: "Token Plan for Teams - MiniMax API Docs"
url: "https://platform.minimax.io/docs/guides/pricing-token-plan-team"
requestedUrl: "https://platform.minimax.io/docs/guides/pricing-token-plan-team"
coverImage: "https://filecdn.minimax.chat/public/58eca777-e31f-448a-9823-e2220e49b426.png"
siteName: "MiniMax API Docs"
summary: "Token Plan for Teams is for multi-member collaboration in Teams. The Team Owner can buy Token Plan seats and a shared Credits pool, and members use assigned or shared resources through their own Subscription Key."
adapter: "generic"
capturedAt: "2026-08-02T07:48:53.019Z"
conversionMethod: "legacy:readability"
fallbackReason: "Defuddle returned empty or incomplete markdown"
kind: "generic/article"
language: "en"
---

# Token Plan for Teams - MiniMax API Docs

Token Plan for Teams is for multi-member collaboration in Teams. The Team Owner can buy Token Plan seats and a shared Credits pool, and members use assigned or shared resources through their own Subscription Key.

Teams are for multi-member collaboration:

-   The Team Owner can buy Token Plan seats.
-   Token Plan seats are assigned **1:1** to members.
-   Members use their assigned plan quota through their own Subscription Key.
-   A subscription can be reassigned during a billing cycle. Reassignment does not reset usage; the new assignee inherits the current subscription usage state.

Teams can use a shared Credits pool:

-   The Team Owner buys Credits for the pool.
-   Members consume shared Credits through their own Subscription Key.
-   Members without an assigned Token Plan can still use shared Credits if Credits access is enabled for them.
-   Owner and Admin can manage member access to shared Credits.

## Pay-As-You-Go

Pay-as-you-go remains separate from Token Plan and Credits:

-   Pay-as-you-go API Keys are separate from Subscription Keys.
-   Each Team has its own Open Platform wallet balance.
-   A pay-as-you-go API Key created inside a Team consumes that Team’s wallet balance.