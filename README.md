---
title: Prayer Angel
emoji: 😇
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 7860
tags:
- streamlit
pinned: false
short_description: A faith-based reflection app helping users connect with God.
license: other
---

# Prayer Angel — Beyond the Message

A faith-based reflection app (Streamlit + Docker).

## Privacy Promise

Prayer Angel (Angel Chat) is designed as a **safe space — not a profile**.

- **No accounts. No ads.**
- **Conversations are not saved or remembered.**
- We don’t build user profiles, and nothing “follows you” across sessions.
- We do not sell or share personal data.

If we ever introduce optional features that remember or follow your journey (like reminders or continuity), they will be **clearly labeled and opt-in** — never assumed.

## Files
- `app.py` — main Streamlit app
- `manifest.json` — PWA manifest (HF-safe paths)
- `sw.js` — service worker
- `icon-192.png`, `icon-512.png` — PWA icons

## Run locally (optional)
```bash
streamlit run app.py --server.port 7860 --server.address 0.0.0.0
