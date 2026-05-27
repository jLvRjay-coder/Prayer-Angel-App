# ============================================================
# FULL app.py â€” Beyond the Message / Prayer Angel (Single File)
# UI POLISH UPDATE (NO CACHE / PWA TROUBLESHOOTING)
# FIX INCLUDED: f-string braces crash in inject_css() (try{ ... } in JS)
# FIX INCLUDED: Streamlit session_state crash in Angel composer
# FIX INCLUDED: Story "Ask a Question" now answers INLINE (no clunky reroute)
# FIX INCLUDED: Journal email now has reliable Download (.txt) fallback
# FIX INCLUDED: Journal Email draft renders clean (no "+"; NO recipient set)
# FIX INCLUDED: Line 1194 f-string backslash crash fixed (no "\n" inside f-string expr)
# FIX INCLUDED: Fix broken quote in btm-hr markup near footer
# UPDATE: ARC SELECTOR for Story Reader (fixes mixed/chaotic dropdown flow)
# UPDATE: JEZEBEL ARC support + selector always visible (even if only one arc)
# ============================================================

import os
import json
import glob
import re
import urllib.parse
import uuid
import io
from datetime import datetime
import time

import streamlit as st
import streamlit.components.v1 as components

# =========================
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# =========================
try:
    from PIL import Image
    _ICON = Image.open("icon-192.png")  # keep this file at repo root
except Exception:
    _ICON = "ðŸ•¯ï¸"

st.set_page_config(
    page_title="Prayer Angel â€” Beyond the Message",
    page_icon=_ICON,
    layout="centered",
)

# =========================
# PWA INJECT (HF-safe relative paths)
# =========================
def inject_pwa():
    st.markdown(
        """
        <link rel="manifest" href="./manifest.json">
        <meta name="theme-color" content="#1A1B26">
        <link rel="icon" href="./icon-192.png">
        <link rel="apple-touch-icon" href="./icon-192.png">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <script>
          (function () {
            try {
              if ("serviceWorker" in navigator) {
                window.addEventListener("load", function () {
                  navigator.serviceWorker.register("./sw.js", { scope: "./" }).catch(function(e){});
                });
              }
            } catch(e) {}
          })();
        </script>
        """,
        unsafe_allow_html=True
    )

inject_pwa()

# =========================
# COLORS / TOKENS â€” VIRTUAL SANCTUARY PALETTE
# Deep Scholarly Navy (Ink) Â· Muted Altar Gold Â· Vellum
# =========================
NAVY   = "#1A1B26"   # Deep Scholarly Navy (Ink)
GOLD   = "#A68966"   # Muted Altar Gold (Accents)
SLATE  = "#3A3B45"   # Deeper slate
LIGHT  = "#F9F7F2"   # Vellum
MID    = "#5C5A5E"   # Muted scholar grey
BORDER = "rgba(26,27,38,0.10)"
INK    = "#1A1B26"

PROD_FOOTER = "BEYOND THE MESSAGE â€¢ angel.beyondthemessage.org"

# =========================
# ROUTER STATE
# =========================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | angel | bible | steps | about

# Sync view from URL (so bottom nav links + deep-links work)
try:
    _qp = dict(st.query_params)
except Exception:
    _qp = {}
_v = _qp.get("v")
if _v in {"home", "angel", "bible", "steps", "about"} and _v != st.session_state.view:
    st.session_state.view = _v

if "angel_prefill" not in st.session_state:
    st.session_state.angel_prefill = ""

def goto(view_key: str):
    # Update router + URL param so deep-links and the bottom nav anchors stay in sync
    st.session_state.view = view_key
    try:
        st.query_params["v"] = view_key
    except Exception:
        pass
    st.rerun()

# =========================
# THEME STATE (PERSISTED IN URL)
# =========================
THEMES = {"light", "dark"}

def _get_theme() -> str:
    theme = st.session_state.get("theme")
    if theme in THEMES:
        return theme
    try:
        qp = dict(st.query_params)
    except Exception:
        qp = {}
    raw = qp.get("theme", "")
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    theme = (raw or "").strip().lower()
    if theme not in THEMES:
        theme = "light"
    st.session_state.theme = theme
    return theme

def _set_theme(theme: str) -> None:
    theme = (theme or "").strip().lower()
    if theme not in THEMES:
        theme = "light"
    st.session_state.theme = theme
    try:
        st.query_params["theme"] = theme
    except Exception:
        pass

# =========================
# SESSION PERSIST (tablet rotation / reload safe)
# =========================
def _ensure_sid() -> str:
    try:
        qp = dict(st.query_params)
    except Exception:
        qp = {}

    sid = qp.get("sid", "")
    if isinstance(sid, list):
        sid = sid[0] if sid else ""
    sid = (sid or "").strip()

    if not sid:
        sid = uuid.uuid4().hex[:12]
        try:
            st.query_params["sid"] = sid
        except Exception:
            pass

    return sid

def _session_path(sid: str) -> str:
    os.makedirs(".btm_sessions", exist_ok=True)
    return os.path.join(".btm_sessions", f"{sid}.json")

def _save_angel_state():
    try:
        sid = st.session_state.get("_sid", "") or _ensure_sid()
        st.session_state["_sid"] = sid

        payload = {
            "mode": st.session_state.get("mode", None),
            "chat": st.session_state.get("chat", []),
            "angel_share": st.session_state.get("angel_share", {"caption": "", "hashtags": "", "kjv_ref": ""}),
            "angel_prefill": st.session_state.get("angel_prefill", ""),
            "privacy_ack": st.session_state.get("privacy_ack", False),
            # Relational Memory â€” what the person is carrying this week.
            "burden": st.session_state.get("burden", ""),
            "mode_pinned": st.session_state.get("mode_pinned", False),
        }
        with open(_session_path(sid), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception:
        pass

def _load_angel_state_if_any():
    try:
        sid = st.session_state.get("_sid", "") or _ensure_sid()
        st.session_state["_sid"] = sid

        p = _session_path(sid)
        if not os.path.exists(p):
            return

        # If chat already exists this run, don't overwrite
        if "chat" in st.session_state and st.session_state.get("chat"):
            return

        with open(p, "r", encoding="utf-8") as f:
            payload = json.load(f) or {}

        st.session_state.mode = payload.get("mode", None)
        st.session_state.chat = payload.get("chat", [])
        st.session_state.angel_share = payload.get("angel_share", {"caption": "", "hashtags": "", "kjv_ref": ""})
        st.session_state.angel_prefill = payload.get("angel_prefill", "")
        st.session_state.privacy_ack = payload.get("privacy_ack", False)
        # Relational Memory restore.
        st.session_state.burden = payload.get("burden", "")
        st.session_state.mode_pinned = payload.get("mode_pinned", False)
    except Exception:
        pass

# =========================
# STYLE (BRAND + BUTTON TYPES)
# FIX: DO NOT USE f""" ... { ... } ... """ with JS/CSS braces
# =========================

def _theme_tokens(theme: str) -> dict:
    if theme == "dark":
        return {
            "bg": "#0F1014",
            "card": "#1A1B26",
            "text": "#EDE7DA",
            "muted": "#9E9A92",
            "border": "rgba(237,231,218,0.10)",
            "card_glow": "rgba(166,137,102,0.08)",
            "chip_bg": "rgba(166,137,102,0.14)",
            "chip_border": "rgba(166,137,102,0.30)",
        }
    return {
        "bg": LIGHT,
        "card": "#FFFFFF",
        "text": "#1A1B26",
        "muted": MID,
        "border": BORDER,
        "card_glow": "rgba(166,137,102,0.06)",
        "chip_bg": "rgba(166,137,102,0.12)",
        "chip_border": "rgba(166,137,102,0.22)",
    }

def inject_css(theme: str):
    tokens = _theme_tokens(theme)
    # NOTE: Plain triple-quoted string (NOT f-string). Tokens like __NAVY__ are
    # substituted via .replace() below â€” so JS/CSS braces {...} are 100% safe.
    css = """
    <style>
      /* ========= TYPOGRAPHY â€” Cormorant Garamond (serif, Scripture + headings)
         paired with Inter (variable, utility) ========= */
      @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&family=Inter:wght@300;400;500;600;700;800;900&display=swap');

      /* ========= THEME TOKENS â€” VIRTUAL SANCTUARY ========= */
      :root{
        --bg: __BG__;
        --card: __CARD__;
        --text: __TEXT__;
        --muted: __MUTED__;
        --navy: __NAVY__;
        --ink: __NAVY__;
        --gold: __GOLD__;
        --gold-soft:   rgba(166,137,102,0.14);
        --gold-glow:   rgba(166,137,102,0.28);
        --gold-strong: rgba(166,137,102,0.55);
        --vellum:         #F9F7F2;
        --vellum-raised:  #FBFAF5;
        --vellum-pressed: #F3EFE6;
        --border: __BORDER__;
        --border-strong: rgba(26,27,38,0.16);
        --card-glow:   __CARD_GLOW__;
        --chip-bg:     __CHIP_BG__;
        --chip-border: __CHIP_BORDER__;
        --success: #4F7A4B;
        --warning: #B47A3A;
        --error:   #9C3B3B;
        --focus:   rgba(166,137,102,0.45);
        /* Dual-layer shadow system */
        --shadow-low:   0 1px 0 rgba(255,255,255,0.6) inset, 0 1px 2px rgba(26,27,38,0.05), 0 18px 52px rgba(26,27,38,0.06);
        --shadow-mid:   0 1px 0 rgba(255,255,255,0.7) inset, 0 1px 2px rgba(26,27,38,0.06), 0 28px 72px rgba(26,27,38,0.09);
        --shadow-high:  0 1px 0 rgba(255,255,255,0.75) inset, 0 1px 2px rgba(26,27,38,0.08), 0 42px 96px rgba(26,27,38,0.12);
        --serif: "Cormorant Garamond", "Cormorant", "EB Garamond", Georgia, serif;
        --sans:  "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      /* ========= VELLUM BASE â€” paper texture + altar-gold halo ========= */
      html, body, .stApp{
        background:
          radial-gradient(1100px 520px at 10% -8%, rgba(166,137,102,0.07), transparent 44%),
          radial-gradient(900px 460px at 92% 4%, rgba(26,27,38,0.04), transparent 36%),
          linear-gradient(180deg, rgba(251,250,245,0.72), rgba(249,247,242,0.92)),
          var(--vellum) !important;
        color: var(--text) !important;
        font-family: var(--sans);
        font-feature-settings: "ss01","cv11","tnum";
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }
      /* Vellum noise â€” SVG data URI, fixed so it never scrolls */
      .stApp:before{
        content:"";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: .55;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320' viewBox='0 0 320 320'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.10  0 0 0 0 0.10  0 0 0 0 0.10  0 0 0 0.06 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
        background-size: 320px 320px;
        mix-blend-mode: multiply;
      }
      .stApp > *{ position: relative; z-index: 1; }

      /* ========= SCHOLARLY-MODERN TYPOGRAPHY ========= */
      h1, h2, h3, h4, h5 {
        font-family: var(--serif);
        font-weight: 600;
        letter-spacing: -0.015em;
        color: var(--ink);
        text-wrap: balance;
      }
      h1 em, h2 em, h3 em, .btm-serif-italic{
        font-style: italic;
        color: var(--gold);
      }
      a {
        color: var(--ink);
        text-decoration-color: var(--gold);
        text-underline-offset: 3px;
        text-decoration-thickness: 1.5px;
      }
      a:hover{ color: var(--gold); }
      :focus-visible {
        outline: 2px solid var(--focus);
        outline-offset: 3px;
        border-radius: 10px;
      }

      .block-container {
        padding-top: 2.25rem;
        padding-bottom: 2.25rem;
        max-width: 980px;
      }

      #MainMenu { visibility: hidden; }
      header    { visibility: hidden; }
      footer    { visibility: hidden; }

      .btm-wrap {
        max-width: 980px;
        margin: 0 auto;
        color: var(--text);
      }

      /* ========= LEGACY HERO â€” still used on the How It Works view ========= */
      .btm-hero {
        padding: 28px 26px 24px 26px;
        border-radius: 24px;
        background:
          radial-gradient(1200px 380px at 18% -12%, rgba(166,137,102,0.22), transparent 58%),
          linear-gradient(155deg, #121319 0%, #1A1B26 58%, #121319 100%);
        box-shadow: var(--shadow-high);
        margin-bottom: 18px;
        overflow: hidden;
        border: 1px solid rgba(237,231,218,0.06);
      }
      .btm-hero h1 {
        margin: 0;
        font-family: var(--serif);
        font-size: 46px;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: #F4EFE3;
      }
      .btm-hero h1 span { color: __GOLD__; font-style: italic; }
      .btm-hero p {
        margin: 12px 0 0 0;
        color: #CFC7B6;
        font-size: 15px;
        line-height: 1.62;
      }
      .btm-hero-title{
        font-family: var(--serif);
        font-size: 38px; font-weight: 700; color: #F4EFE3;
        letter-spacing: -0.02em; line-height:1.05;
      }
      .btm-hero-sub{
        margin-top: 10px;
        color: #CFC7B6;
        font-size: 15px;
        line-height: 1.6;
        font-family: var(--serif);
        font-style: italic;
      }
      .btm-note {
        color: var(--muted);
        font-size: 13px;
        margin: 8px 0 0 0;
      }

      .btm-page-title {
        font-family: var(--serif);
        font-size: 40px;
        font-weight: 700;
        letter-spacing: -0.025em;
        margin: 6px 0 2px 0;
        color: var(--ink);
        text-wrap: balance;
      }
      .btm-sub {
        color: var(--muted);
        font-size: 14.5px;
        margin-bottom: 14px;
        font-style: italic;
        font-family: var(--serif);
      }

      /* Section title â€” hairline gold underline */
      .btm-sec-title{
        font-family: var(--serif);
        font-weight: 700;
        color: var(--ink);
        font-size: 22px;
        letter-spacing: -0.01em;
        margin: 2px 0 14px 0;
        display:inline-block;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--gold-strong);
      }
      .btm-sec-title.is-serif{ font-family: var(--serif); }

      /* ========= CARDS â€” Floating Vellum (dual-layer shadow) ========= */
      .btm-card {
        background:
          linear-gradient(180deg, rgba(255,255,255,0.78), rgba(255,255,255,0.94)),
          var(--card);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 22px;
        box-shadow: var(--shadow-mid);
        margin-bottom: 16px;
        animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
      }
      .btm-card-tight {
        background:
          linear-gradient(180deg, rgba(255,255,255,0.76), rgba(255,255,255,0.92)),
          var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px;
        box-shadow: var(--shadow-low);
        margin-bottom: 14px;
      }

      .btm-hr {
        height: 1px;
        border: 0;
        background: linear-gradient(90deg, rgba(166,137,102,0), rgba(166,137,102,0.32), rgba(166,137,102,0));
        margin: 22px 0;
      }

      .btm-small {
        font-size: 12.5px;
        color: var(--muted);
        font-style: italic;
        font-family: var(--serif);
      }
      .btm-kicker{
        text-transform: uppercase;
        letter-spacing: .22em;
        font-size: 10.5px;
        font-weight: 700;
        color: var(--gold);
        font-family: var(--sans);
      }
      .btm-badge{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding: 5px 11px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: .06em;
        border: 1px solid var(--gold-soft);
        background: rgba(166,137,102,0.10);
        color: var(--ink);
      }
      .btm-badge.success{ background: rgba(79,122,75,0.12);  color: var(--success); border-color: rgba(79,122,75,0.25); }
      .btm-badge.warn{    background: rgba(180,122,58,0.12); color: var(--warning); border-color: rgba(180,122,58,0.25); }
      .btm-badge.error{   background: rgba(156,59,59,0.12);  color: var(--error);   border-color: rgba(156,59,59,0.25); }

      /* ========= SCRIPTURE BOX â€” ink ground, gilded anchor ========= */
      .btm-scripture {
        background:
          radial-gradient(600px 220px at 0% 0%, rgba(166,137,102,0.20), transparent 60%),
          linear-gradient(160deg, #16171F 0%, #1A1B26 55%, #101118 100%);
        border: 1px solid rgba(237,231,218,0.06);
        border-radius: 20px;
        padding: 22px 22px 20px 22px;
        color: #F2ECDE;
        box-shadow: var(--shadow-high);
        margin-bottom: 16px;
        animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
      }
      .btm-scripture h3 {
        margin: 0 0 12px 0;
        font-size: 17px;
        color: __GOLD__;
        font-weight: 600;
        letter-spacing: .04em;
        font-family: var(--serif);
        font-style: italic;
      }
      .btm-scripture a {
        color: #E6D4B3;
        font-family: var(--serif);
        font-weight: 600;
        font-style: italic;
        font-size: 17px;
        text-decoration-color: rgba(166,137,102,0.55);
      }
      .btm-scripture a:hover{ color: #F5E7C9; }
      .btm-scripture ul{ margin: 4px 0 0 0; padding-left: 18px; }
      .btm-scripture li{ margin: 6px 0; }

      /* ========= RHYTHM CALLOUT â€” altar strip ========= */
      .btm-rhythm {
        border: 1px solid var(--gold-soft);
        background:
          linear-gradient(180deg, rgba(166,137,102,0.08), rgba(166,137,102,0.02)),
          var(--vellum-raised);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: var(--shadow-low);
      }
      .btm-rhythm h4 {
        margin: 0 0 6px 0;
        color: var(--ink);
        font-size: 20px;
        font-family: var(--serif);
        font-weight: 600;
        letter-spacing: -0.01em;
      }
      .btm-rhythm p {
        margin: 0;
        color: var(--muted);
        font-size: 13.5px;
        line-height: 1.55;
        font-family: var(--serif);
        font-style: italic;
      }
      .btm-rhythm .btm-rhythm-steps {
        margin-top: 12px;
        font-weight: 600;
        color: var(--ink);
        letter-spacing: .14em;
        font-size: 11.5px;
        text-transform: uppercase;
        font-family: var(--sans);
      }
      .btm-rhythm .dot {
        display:inline-block;
        width: 4px;
        height: 4px;
        border-radius: 999px;
        background: var(--gold);
        margin: 0 12px 2px 12px;
        opacity: 0.85;
      }

      /* ========= SHARE CARD PREVIEW ========= */
      .btm-sharecard {
        background:
          radial-gradient(500px 200px at 100% 0%, rgba(166,137,102,0.22), transparent 60%),
          linear-gradient(160deg, #16171F 0%, #1A1B26 60%, #0F1016 100%);
        border-radius: 20px;
        padding: 22px;
        color: #F2ECDE;
        box-shadow: var(--shadow-high);
        border: 1px solid rgba(237,231,218,0.07);
        overflow:hidden;
        margin-bottom: 12px;
        animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
      }
      .btm-sharecard .bar {
        background: linear-gradient(90deg, #B59877, #A68966);
        color: #1A1B26;
        font-weight: 700;
        letter-spacing: .22em;
        font-size: 11px;
        padding: 9px 14px;
        border-radius: 999px;
        display:inline-block;
        margin-bottom: 14px;
        text-transform: uppercase;
        font-family: var(--sans);
        box-shadow: 0 8px 20px rgba(166,137,102,0.28);
      }
      .btm-sharecard .body {
        font-family: var(--serif);
        font-size: 19px;
        font-weight: 500;
        line-height: 1.55;
        color: #EAE2D1;
        margin-bottom: 14px;
        white-space: pre-wrap;
        font-style: italic;
      }
      .btm-sharecard .ref {
        font-family: var(--serif);
        font-weight: 700;
        color: __GOLD__;
        margin-top: 8px;
        font-size: 14px;
        letter-spacing: .02em;
      }
      .btm-sharecard .foot {
        margin-top: 18px;
        font-size: 10.5px;
        color: rgba(242,236,222,0.65);
        letter-spacing: .2em;
        text-transform: uppercase;
        font-family: var(--sans);
      }

      /* ========= INPUTS ========= */
      input, textarea, select {
        border-radius: 14px !important;
        border: 1px solid var(--border-strong) !important;
        background: var(--vellum-raised) !important;
        color: var(--text) !important;
        padding: 12px 14px !important;
        font-family: var(--sans) !important;
      }
      input:focus, textarea:focus, select:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 3px rgba(166,137,102,0.18) !important;
        background: #FFFFFF !important;
      }

      /* Hide Streamlit inline input instructions */
      div[data-testid="stTextInput"] [data-testid="InputInstructions"],
      div[data-testid="stTextArea"]  [data-testid="InputInstructions"],
      div[data-testid="stTextInput"] div[aria-live="polite"],
      div[data-testid="stTextArea"]  div[aria-live="polite"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
      }

      /* ========= BUTTON SYSTEM â€” Ink primary / Vellum-outlined secondary ========= */
      div[data-testid="stButton"] > button{
        font-family: var(--sans) !important;
        letter-spacing: .04em !important;
        transition: transform .18s ease, box-shadow .18s ease, background .18s ease, color .18s ease, border-color .18s ease !important;
      }
      div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(180deg, #22232E, #1A1B26) !important;
        color: #F4EFE3 !important;
        font-weight: 600 !important;
        border: 1px solid #0E0F14 !important;
        border-radius: 14px !important;
        padding: 13px 20px !important;
        box-shadow:
          0 1px 0 rgba(255,255,255,0.05) inset,
          0 1px 2px rgba(26,27,38,0.24),
          0 18px 44px rgba(26,27,38,0.24) !important;
      }
      div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow:
          0 1px 0 rgba(255,255,255,0.07) inset,
          0 1px 2px rgba(26,27,38,0.28),
          0 24px 56px rgba(26,27,38,0.30),
          0 0 0 1px rgba(166,137,102,0.45) !important;
      }
      div[data-testid="stButton"] > button[kind="primary"].gold-cta {
        background: linear-gradient(180deg, #B59877, #A68966) !important;
        color: #1A1B26 !important;
        box-shadow: 0 14px 32px rgba(166,137,102,0.30) !important;
      }

      div[data-testid="stButton"] > button[kind="secondary"] {
        background: var(--vellum-raised) !important;
        color: var(--ink) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 14px !important;
        padding: 13px 20px !important;
        box-shadow: var(--shadow-low) !important;
      }
      div[data-testid="stButton"] > button[kind="secondary"]:hover {
        transform: translateY(-1px);
        background: var(--ink) !important;
        color: #F4EFE3 !important;
        border-color: var(--gold) !important;
        box-shadow: 0 20px 44px rgba(26,27,38,0.22) !important;
      }

      /* Mail link button */
      .btm-mail {
        display:block;
        width:100%;
        text-align:center;
        text-decoration:none;
        font-weight:600;
        font-family: var(--sans);
        letter-spacing: .04em;
        color: var(--ink);
        background: var(--vellum-raised);
        border:1px solid var(--border-strong);
        border-radius:14px;
        padding:13px 18px;
        box-shadow: var(--shadow-low);
        transition: all .18s ease;
      }
      .btm-mail:hover{
        background: var(--ink);
        color: #F4EFE3;
        border-color: var(--gold);
      }

      /* ========= INLINE Q&A BUBBLES ========= */
      .btm-qa-wrap{
        border: 1px solid var(--border);
        border-left: 3px solid var(--gold);
        border-radius: 0 16px 16px 0;
        padding: 16px 18px;
        background:
          linear-gradient(90deg, rgba(166,137,102,0.08), rgba(166,137,102,0.01)),
          var(--vellum-raised);
        animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
      }
      .btm-qa-q{
        font-family: var(--serif);
        font-style: italic;
        font-weight: 600;
        font-size: 17px;
        color: var(--ink);
        margin: 0 0 8px 0;
        letter-spacing: -0.005em;
      }
      .btm-qa-a{
        margin: 0;
        color: var(--text);
        line-height: 1.65;
        font-size: 15px;
        font-family: var(--sans);
      }

      /* ========= PILL RADIO CONTROLS ========= */
      div[data-testid="stRadio"] div[role="radiogroup"] { gap: 8px; }
      div[data-testid="stRadio"] div[role="radiogroup"] > label {
        border-radius: 999px;
        padding: 7px 16px;
        border: 1px solid var(--chip-border);
        background: var(--chip-bg);
        color: var(--ink);
        font-weight: 600;
        font-family: var(--sans);
        letter-spacing: .04em;
        font-size: 12.5px;
        box-shadow: var(--shadow-low);
        transition: all .18s ease;
      }
      div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        border-color: var(--gold);
        background: rgba(166,137,102,0.12);
      }
      div[data-testid="stRadio"] div[role="radiogroup"] > label input:checked + div {
        background: var(--ink);
        color: #F4EFE3;
        border-radius: 999px;
        padding: 7px 16px;
        box-shadow:
          0 1px 0 rgba(255,255,255,0.06) inset,
          0 12px 28px rgba(26,27,38,0.28);
      }

      /* ========= MOBILE BUTTON SIZING ========= */
      @media (max-width: 520px){
        div[data-testid="stButton"] > button{
          padding: 11px 14px !important;
          border-radius: 12px !important;
          font-size: 0.95rem !important;
          line-height: 1.15 !important;
        }
        .btm-card{ padding: 18px !important; border-radius: 18px !important; }
        .btm-card-tight{ padding: 14px !important; }
        .btm-page-title{ font-size: 32px !important; }
      }

      /* ========= PRIVACY REASSURANCE ========= */
      .btm-privacy{
        border: 1px solid var(--gold-soft);
        background:
          linear-gradient(180deg, rgba(166,137,102,0.06), rgba(166,137,102,0.01)),
          var(--vellum-raised);
        border-radius: 18px;
        padding: 18px 18px;
        margin: 10px 0 16px 0;
        box-shadow: var(--shadow-low);
      }
      .btm-privacy .title{
        font-family: var(--serif);
        font-weight: 600;
        font-size: 19px;
        color: var(--ink);
        letter-spacing: -0.01em;
        margin: 0 0 8px 0;
      }
      .btm-privacy .line{
        margin: 0;
        font-size: 14px;
        line-height: 1.55;
        color: var(--muted);
        font-family: var(--sans);
      }
      .btm-privacy .strong{ color: var(--text); font-weight: 700; }
      .btm-privacy .bullets{
        margin: 12px 0 0 0;
        padding-left: 20px;
        color: var(--muted);
        font-size: 13.5px;
        line-height: 1.65;
        font-family: var(--sans);
      }
      .btm-privacy-mini{
        margin-top: 12px;
        padding: 11px 14px;
        border-radius: 14px;
        border: 1px dashed var(--gold-soft);
        background: rgba(166,137,102,0.06);
        color: var(--muted);
        font-size: 12.5px;
        line-height: 1.55;
        font-family: var(--serif);
        font-style: italic;
      }

      /* ========= BOTTOM NAV â€” Vellum glass ========= */
      .btm-bottom-nav{
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        padding: 12px 14px calc(12px + env(safe-area-inset-bottom));
        background: linear-gradient(180deg, rgba(249,247,242,0), rgba(249,247,242,0.86));
        backdrop-filter: blur(14px) saturate(1.05);
      }
      .btm-nav-item{
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        border: 1px solid var(--border-strong);
        background: rgba(255,255,255,0.85);
        color: var(--text);
        border-radius: 14px;
        height: 54px;
        box-shadow: var(--shadow-low);
        padding: 0 10px;
        font-family: var(--sans);
        transition: all .22s ease;
      }
      .btm-nav-item:hover{
        border-color: var(--gold);
        transform: translateY(-1px);
      }
      .btm-nav-item .btm-nav-label{
        font-weight: 600;
        font-size: 13.5px;
        letter-spacing: .04em;
        line-height: 1.1;
        text-align: center;
      }
      .btm-nav-item.active{
        background: var(--ink);
        color: #F4EFE3 !important;
        border-color: var(--gold);
        box-shadow:
          0 1px 0 rgba(255,255,255,0.06) inset,
          0 20px 44px rgba(26,27,38,0.22);
      }
      .btm-nav-item.active .btm-nav-label{ text-decoration: none !important; }

      section.main > div{ padding-bottom: 130px !important; }

      /* ========= HOW IT WORKS ========= */
      .btm-grid-2{
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
      }
      @media (min-width: 900px){ .btm-grid-2{ grid-template-columns: 1fr 1fr; } }
      .btm-section-title{
        font-family: var(--serif);
        font-size: 22px;
        font-weight: 600;
        letter-spacing: -0.01em;
        margin-bottom: 10px;
        color: var(--ink);
      }
      .btm-step{
        padding: 14px 0;
        border-top: 1px solid var(--border);
      }
      .btm-step:first-of-type{ border-top: none; padding-top: 2px; }
      .btm-step-title{
        font-family: var(--serif);
        font-weight: 600;
        font-size: 18px;
        margin-bottom: 4px;
        color: var(--ink);
      }
      .btm-step-desc{
        color: var(--muted);
        font-weight: 400;
        font-size: 14.5px;
        line-height: 1.6;
        font-family: var(--sans);
      }
      .btm-bullets{ display: grid; gap: 12px; }
      .btm-bullet{ display:flex; gap:12px; align-items:flex-start; font-size: 14px; color: var(--text); line-height:1.55; }
      .btm-bullet .dot{
        width: 6px; height: 6px; border-radius: 999px;
        background: var(--gold);
        margin-top: 9px;
        flex: 0 0 auto;
        box-shadow: 0 0 0 3px rgba(166,137,102,0.18);
      }

      .btm-note{ border: 1px solid var(--gold-soft); }
      .btm-note-text{ font-weight: 500; color: var(--text); line-height: 1.6; }

      /* ========= External CTA pills ========= */
      .btm-pill-link {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 48px;
        width: 100%;
        text-decoration: none !important;
        font-weight: 600;
        font-family: var(--sans);
        letter-spacing: .04em;
        border-radius: 14px;
        padding: 12px 18px;
        box-sizing: border-box;
        transition: all .22s ease;
      }
      .btm-pill-link.secondary {
        background: var(--vellum-raised);
        color: var(--ink) !important;
        border: 1px solid var(--border-strong);
        box-shadow: var(--shadow-low);
      }
      .btm-pill-link.secondary:hover {
        transform: translateY(-1px);
        background: var(--ink);
        color: #F4EFE3 !important;
        border-color: var(--gold);
        box-shadow: 0 20px 44px rgba(26,27,38,0.22);
      }
      .btm-pill-link.primary {
        background: linear-gradient(180deg, #22232E, #1A1B26);
        color: #F4EFE3 !important;
        border: 1px solid #0E0F14;
        box-shadow:
          0 1px 0 rgba(255,255,255,0.05) inset,
          0 18px 44px rgba(26,27,38,0.24);
      }
      .btm-voice-wrap {
        border: 1px dashed var(--gold-soft);
        border-radius: 14px;
        padding: 13px 15px;
        background: rgba(166,137,102,0.06);
        margin: 10px 0 12px 0;
      }
      .btm-voice-title {
        font-family: var(--serif);
        font-weight: 600;
        color: var(--ink);
        font-size: 17px;
        margin-bottom: 4px;
      }
      .btm-voice-copy {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
        font-family: var(--sans);
      }

      /* ========= MATERIALIZATION + RITUAL PULSE KEYFRAMES ========= */
      @keyframes btmMaterialize{
        0%   { opacity: 0; transform: translateY(14px); filter: blur(3px); }
        60%  { opacity: 1; filter: blur(0); }
        100% { opacity: 1; transform: translateY(0);   filter: blur(0); }
      }
      @keyframes btmFadeDown{
        from{ opacity:0; transform: translateY(-8px); filter: blur(2px); }
        to  { opacity:1; transform: translateY(0);    filter: blur(0); }
      }
      @keyframes btmRitualPulse{
        0%, 100%{
          box-shadow:
            0 1px 0 rgba(255,255,255,0.75) inset,
            0 1px 2px rgba(26,27,38,0.06),
            0 28px 72px rgba(26,27,38,0.08),
            0 0 0 1px rgba(166,137,102,0.14),
            0 0 0 10px rgba(166,137,102,0.03);
        }
        50%{
          box-shadow:
            0 1px 0 rgba(255,255,255,0.85) inset,
            0 1px 2px rgba(26,27,38,0.08),
            0 40px 92px rgba(166,137,102,0.16),
            0 0 0 1px rgba(166,137,102,0.30),
            0 0 0 18px rgba(166,137,102,0.07);
        }
      }

      /* Streamlit chat message â€” scholarly card */
      div[data-testid="stChatMessage"]{
        background: var(--vellum-raised) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        box-shadow: var(--shadow-low);
        animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
      }
      div[data-testid="stChatMessage"] p{
        font-family: var(--sans);
        font-size: 15px;
        line-height: 1.7;
        color: var(--text);
      }

      /* Selectbox */
      div[data-baseweb="select"] > div{
        border-radius: 14px !important;
        background: var(--vellum-raised) !important;
        border: 1px solid var(--border-strong) !important;
      }

      /* Expander summary */
      details summary{
        font-family: var(--sans);
        font-weight: 600;
        color: var(--ink);
        letter-spacing: .02em;
      }

      /* Alert bubbles â€” softened */
      div[data-testid="stAlert"]{
        border-radius: 16px !important;
        border: 1px solid var(--border) !important;
        background: var(--vellum-raised) !important;
        box-shadow: var(--shadow-low);
      }

      /* Markdown content inside story body â€” prose refinements */
      .btm-card p{ font-size: 15.5px; line-height: 1.72; color: var(--text); }
      .btm-card blockquote{
        border-left: 3px solid var(--gold);
        background: rgba(166,137,102,0.05);
        margin: 14px 0;
        padding: 10px 16px;
        border-radius: 0 12px 12px 0;
        font-family: var(--serif);
        font-style: italic;
        color: var(--text);
      }
    </style>
    """

    css = (css
        .replace("__NAVY__", NAVY)
        .replace("__GOLD__", GOLD)
        .replace("__SLATE__", SLATE)
        .replace("__LIGHT__", LIGHT)
        .replace("__MID__", MID)
        .replace("__BORDER__", BORDER)
        .replace("__BG__", tokens["bg"])
        .replace("__CARD__", tokens["card"])
        .replace("__TEXT__", tokens["text"])
        .replace("__MUTED__", tokens["muted"])
        .replace("__CARD_GLOW__", tokens["card_glow"])
        .replace("__CHIP_BG__", tokens["chip_bg"])
        .replace("__CHIP_BORDER__", tokens["chip_border"])
    )

    st.markdown(css, unsafe_allow_html=True)

inject_css(_get_theme())

def inject_premium_layout_css():
    # Plain string â€” tokens are literal CSS. No f-strings, no brace collisions.
    st.markdown(
        """
        <style>
        /* ========= PREMIUM VELLUM LAYOUT (Hero Composer + Home + Response Shell) ========= */
        .stApp{
          background:
            radial-gradient(1200px 520px at 8% -8%, rgba(166,137,102,0.10), transparent 44%),
            radial-gradient(900px 460px at 92% 2%, rgba(26,27,38,0.05), transparent 36%),
            linear-gradient(180deg, rgba(251,250,245,0.76), rgba(249,247,242,0.94)),
            var(--bg) !important;
          position: relative;
        }
        .block-container{
          max-width: 920px;
          padding-top: 2rem;
        }

        /* ========= HOME HERO â€” scholarly Ink panel with gold halo ========= */
        .btm-home-hero{
          padding: 40px 34px 34px;
          border-radius: 28px;
          background:
            radial-gradient(900px 280px at 14% -10%, rgba(166,137,102,0.24), transparent 50%),
            radial-gradient(500px 200px at 100% 0%, rgba(166,137,102,0.10), transparent 60%),
            linear-gradient(155deg,#16171F 0%, #1A1B26 52%, #111218 100%);
          border: 1px solid rgba(237,231,218,0.07);
          box-shadow:
            0 1px 0 rgba(255,255,255,0.12) inset,
            0 1px 2px rgba(26,27,38,0.20),
            0 32px 80px rgba(26,27,38,0.22),
            0 60px 140px rgba(26,27,38,0.18);
          margin-bottom: 22px;
          overflow: hidden;
          position: relative;
          animation: btmMaterialize 0.9s cubic-bezier(0.22,0.61,0.36,1) both;
        }
        .btm-home-hero::after{
          content:"";
          position:absolute; inset:0;
          pointer-events:none;
          background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='1.1' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.07 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
          mix-blend-mode: overlay;
          opacity: .4;
        }
        .btm-home-kicker{
          display:inline-flex;align-items:center;gap:10px;
          padding:8px 14px;border-radius:999px;
          background:rgba(166,137,102,0.12);
          border:1px solid rgba(166,137,102,0.26);
          color:#E6D4B3;font-size:10.5px;font-weight:700;
          letter-spacing:.22em;text-transform:uppercase;margin-bottom:18px;
          font-family: "Inter", system-ui, sans-serif;
        }
        .btm-home-title{
          margin:0;
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-size:52px;font-weight:600;
          letter-spacing:-.025em;line-height:1.02;
          color:#F4EFE3;
          text-wrap: balance;
        }
        .btm-home-title span{ color:#E6D4B3; font-style: italic; }
        .btm-home-copy{
          margin:16px 0 0 0;
          color:#CFC7B6;font-size:16px;line-height:1.68;
          max-width:690px;letter-spacing:.005em;
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-style: italic;
        }
        .btm-home-chip-row{
          display:flex;flex-wrap:wrap;gap:10px;margin-top:20px;
        }
        .btm-home-chip{
          display:inline-flex;align-items:center;gap:6px;
          padding:8px 13px;border-radius:999px;
          background:rgba(244,239,227,0.06);
          border:1px solid rgba(244,239,227,0.14);
          color:#EFE8D8;font-size:11.5px;font-weight:600;
          letter-spacing:.08em;
          font-family:"Inter",system-ui,sans-serif;
          transition: all .22s ease;
        }
        .btm-home-chip:hover{
          background:rgba(166,137,102,0.16);
          border-color: rgba(166,137,102,0.42);
          color:#F5E7C9;
          transform: translateY(-1px);
        }
        .btm-home-cta-note{
          margin-top:18px;
          color:#B8B0A0;font-size:13px;line-height:1.6;
          font-family:"Cormorant Garamond",Georgia,serif;
          font-style: italic;
        }

        /* ========= FLOATING VELLUM PANELS ========= */
        .btm-path-card, .btm-footer-tools, .btm-response-shell, .btm-hero-composer{
          background:
            linear-gradient(180deg, rgba(255,255,255,0.82), rgba(255,255,255,0.96)),
            var(--card);
          border: 1px solid rgba(166,137,102,0.14);
          border-radius: 24px;
          box-shadow:
            0 1px 0 rgba(255,255,255,0.88) inset,
            0 1px 2px rgba(26,27,38,0.05),
            0 20px 44px rgba(26,27,38,0.08),
            0 48px 96px rgba(26,27,38,0.10);
        }
        .btm-path-card{
          padding:26px 24px;
          animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
        }
        .btm-path-title{
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-size:26px;font-weight:600;letter-spacing:-.02em;
          color:var(--ink);margin:0 0 10px 0;text-wrap:balance;
        }
        .btm-path-copy, .btm-tool-copy, .btm-support-copy, .btm-send-note, .btm-angel-sub, .btm-composer-prompt{
          color:var(--muted);
          font-size:15px;
          line-height:1.68;
          letter-spacing:.005em;
          font-family:"Inter",system-ui,sans-serif;
        }

        /* ========= ANGEL HERO ========= */
        .btm-angel-hero{ padding:14px 0 8px 0; text-align:center; }
        .btm-angel-kicker{
          display:inline-flex;align-items:center;gap:10px;
          padding:7px 14px;border-radius:999px;
          background:rgba(166,137,102,0.10);
          border:1px solid rgba(166,137,102,0.24);
          color:#7D6242;font-size:10.5px;font-weight:700;
          letter-spacing:.22em;text-transform:uppercase;
          font-family:"Inter",system-ui,sans-serif;
        }
        .btm-angel-title{
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-size:54px;font-weight:600;
          letter-spacing:-.03em;color:var(--ink);margin:14px 0 10px 0;
          line-height:1.02;text-wrap:balance;
        }
        .btm-angel-sub{
          max-width:680px;margin:0 auto 10px auto;
          text-wrap:balance;
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-style: italic;
          font-size: 17px;
          color: var(--muted);
        }
        .btm-mode-chip-row{
          display:flex;justify-content:center;flex-wrap:wrap;gap:8px;margin:10px 0 14px 0;
        }
        .btm-mode-chip{
          display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:999px;
          background:rgba(166,137,102,0.10);border:1px solid rgba(166,137,102,0.20);
          color:#7D6242;font-size:11.5px;font-weight:600;letter-spacing:.10em;
          font-family:"Inter",system-ui,sans-serif;
          text-transform: uppercase;
          transition: all .22s ease;
        }
        .btm-mode-chip:hover{
          background: rgba(166,137,102,0.18);
          border-color: rgba(166,137,102,0.40);
          transform: translateY(-1px);
        }

        /* ========= HERO COMPOSER â€” center of gravity, with RITUAL PULSE ========= */
        .btm-hero-composer{
          position:relative;
          padding:28px 24px 22px;
          margin:20px auto 16px;
          max-width: 760px;
          animation: btmMaterialize 0.9s cubic-bezier(0.22,0.61,0.36,1) both,
                     btmRitualPulse 5.4s ease-in-out 1.2s infinite;
        }
        .btm-hero-composer:before{
          content:"";
          position:absolute;inset:-1px;border-radius:24px;
          pointer-events:none;
          box-shadow:
            0 0 0 1px rgba(166,137,102,0.14),
            0 0 0 10px rgba(166,137,102,0.035);
        }
        .btm-hero-composer:after{
          /* Subtle gilded corner mark */
          content:"âœ¦";
          position:absolute; top:14px; right:18px;
          color: var(--gold);
          font-size: 14px;
          opacity: 0.55;
          pointer-events:none;
        }
        .btm-composer-kicker{
          font-size:10.5px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
          color:#7D6242;margin-bottom:14px;text-align:center;
          font-family:"Inter",system-ui,sans-serif;
        }
        .btm-send-note{
          font-size:12.5px;margin-top:10px;text-align:center;
          font-style: italic;
          font-family:"Cormorant Garamond",Georgia,serif;
          color: var(--muted);
        }
        .btm-prompt-strip{
          display:flex;flex-wrap:wrap;gap:10px;justify-content:center;
          margin:8px auto 0;
          max-width:760px;
        }

        .btm-chat-frame{ margin-top:10px; }

        /* ========= RESPONSE SHELL â€” materializes with the words ========= */
        .btm-response-shell{
          padding:26px 24px 22px;
          margin:18px auto 16px;
          max-width: 760px;
          animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
          position: relative;
        }
        .btm-response-shell:before{
          content:"";
          position:absolute; left:-1px; top:24px;
          width: 3px; height: calc(100% - 48px);
          background: linear-gradient(180deg, transparent, var(--gold), transparent);
          opacity: 0.45;
          border-radius: 0 3px 3px 0;
        }
        .btm-response-kicker{
          font-size:10.5px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
          color:#7D6242;margin-bottom:12px;
          font-family:"Inter",system-ui,sans-serif;
        }

        /* ========= SCRIPTURE ANCHOR â€” gilded verse ========= */
        .btm-scripture-anchor{
          border-left:3px solid var(--gold);
          background:
            linear-gradient(90deg, rgba(166,137,102,0.10), rgba(166,137,102,0.01));
          padding:18px 20px;border-radius:0 18px 18px 0;margin:0 0 18px 0;
          animation: btmFadeDown 0.8s cubic-bezier(0.22,0.61,0.36,1) 0.15s both;
        }
        .btm-scripture-anchor .label{
          font-size:10.5px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
          color:#7D6242;margin-bottom:9px;
          font-family:"Inter",system-ui,sans-serif;
        }
        .btm-scripture-anchor .ref{
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-size:28px;font-weight:600;
          font-style: italic;
          color:var(--ink);line-height:1.18;
          text-wrap:balance;
          letter-spacing: -0.01em;
        }

        .btm-tool-title{
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif;
          font-weight:600;color:var(--ink);font-size:26px;margin-bottom:10px;
          text-wrap: balance;
          letter-spacing: -0.02em;
        }
        .btm-footer-tools{
          padding:24px;margin-top:18px;
          animation: btmMaterialize 0.8s cubic-bezier(0.22,0.61,0.36,1) both;
        }
        .btm-minor-divider{
          height:1px;border:0;
          background:linear-gradient(90deg, rgba(226,232,240,0), rgba(166,137,102,0.36), rgba(226,232,240,0));
          margin:14px 0 16px 0;
        }

        /* ========= HERO TEXT INPUT â€” the "composer" field ========= */
        div[data-testid="stTextInput"]{
          max-width: 760px;
          margin: 0 auto;
        }
        div[data-testid="stTextInput"] input{
          min-height:64px !important;
          border-radius:20px !important;
          border:1px solid rgba(166,137,102,0.30) !important;
          background:rgba(255,255,255,0.95) !important;
          color:#1A1B26 !important;
          box-shadow:
            0 1px 0 rgba(255,255,255,0.88) inset,
            0 12px 24px rgba(26,27,38,0.06),
            0 0 0 8px rgba(166,137,102,0.04) !important;
          font-size:17px !important;
          font-family:"Cormorant Garamond","Cormorant","EB Garamond",Georgia,serif !important;
          font-style: italic;
          padding:0 20px !important;
          transition: all .32s ease !important;
          letter-spacing: 0.005em;
        }
        div[data-testid="stTextInput"] input:focus{
          border-color:rgba(166,137,102,0.70) !important;
          box-shadow:
            0 1px 0 rgba(255,255,255,0.96) inset,
            0 18px 36px rgba(26,27,38,0.09),
            0 0 0 12px rgba(166,137,102,0.10) !important;
          background: #FFFFFF !important;
        }
        div[data-testid="stTextInput"] input::placeholder{
          color:#7A7268 !important;
          opacity:1 !important;
          font-style: italic;
        }

        div[data-testid="stButton"] > button{
          transition: all .3s ease !important;
          letter-spacing:.04em !important;
        }
        .btm-pill-link, .btm-home-chip, .btm-mode-chip, .btm-badge{
          transition: all .3s ease;
        }
        .btm-home-chip:hover, .btm-mode-chip:hover{
          transform: translateY(-1px);
          box-shadow: 0 10px 22px rgba(26,27,38,0.10);
        }
        h1,h2,h3,h4,h5,
        .btm-home-title, .btm-angel-title, .btm-path-title,
        .btm-tool-title, .btm-scripture-anchor .ref{
          text-wrap: balance;
        }

        /* Keyframes (duplicated from inject_css so premium layer stands alone) */
        @keyframes btmMaterialize{
          0%   { opacity:0; transform: translateY(14px); filter: blur(3px); }
          60%  { opacity:1; filter: blur(0); }
          100% { opacity:1; transform: translateY(0);   filter: blur(0); }
        }
        @keyframes btmFadeDown{
          from{ opacity:0; transform: translateY(-8px); filter: blur(2px); }
          to  { opacity:1; transform: translateY(0);    filter: blur(0); }
        }
        @keyframes btmRitualPulse{
          0%, 100%{
            box-shadow:
              0 1px 0 rgba(255,255,255,0.88) inset,
              0 1px 2px rgba(26,27,38,0.05),
              0 20px 44px rgba(26,27,38,0.08),
              0 48px 96px rgba(26,27,38,0.10),
              0 0 0 1px rgba(166,137,102,0.12),
              0 0 0 10px rgba(166,137,102,0.025);
          }
          50%{
            box-shadow:
              0 1px 0 rgba(255,255,255,0.92) inset,
              0 1px 2px rgba(26,27,38,0.07),
              0 28px 60px rgba(26,27,38,0.12),
              0 60px 120px rgba(166,137,102,0.14),
              0 0 0 1px rgba(166,137,102,0.32),
              0 0 0 18px rgba(166,137,102,0.06);
          }
        }
        /* Respect reduced motion preference */
        @media (prefers-reduced-motion: reduce){
          .btm-card, .btm-scripture, .btm-sharecard, .btm-response-shell,
          .btm-hero-composer, .btm-home-hero, .btm-qa-wrap, .btm-footer-tools,
          .btm-path-card, .btm-scripture-anchor, div[data-testid="stChatMessage"]{
            animation: none !important;
          }
        }

        @media (max-width: 520px){
          .btm-home-hero{ padding: 28px 22px 26px; }
          .btm-home-title{ font-size: 40px; }
          .btm-angel-title{ font-size: 38px; }
          .btm-hero-composer, .btm-response-shell, .btm-footer-tools{
            padding: 22px 18px 18px;
          }
          .btm-scripture-anchor .ref{ font-size: 22px; }
        }

        /* ================================================================
           TOTAL EXPERIENCE OVERHAUL â€” Sacred Minimalism layer
           Sanctuary Invite, Sacred Glassmorphism, Illuminated Scripture,
           Quiet Menu, Center-Anchored Companion Column.
           ================================================================ */

        /* --- Hide Streamlit chrome so the sanctuary has no product frame --- */
        #MainMenu, footer, header { visibility: hidden !important; }
        div[data-testid="stDecoration"] { display: none !important; }
        div[data-testid="stToolbar"] { display: none !important; }
        [data-testid="stStatusWidget"] { display: none !important; }

        /* --- SANCTUARY INVITE (Home) --- */
        .btm-sanctuary-wrap{
          padding-top: 6vh;
        }
        .btm-sanctuary-invite{
          text-align: center;
          padding: 48px 20px 36px;
          animation: btmMaterialize 1.2s cubic-bezier(0.22,0.61,0.36,1) both;
        }
        .btm-sanctuary-ornament{
          font-size: 28px;
          color: #A68966;
          letter-spacing: 0.2em;
          margin-bottom: 22px;
          opacity: 0.72;
          animation: btmRitualPulse 6s ease-in-out infinite;
        }
        .btm-sanctuary-kicker{
          font-family: 'Inter', sans-serif;
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.28em;
          text-transform: uppercase;
          color: rgba(26,27,38,0.52);
          margin-bottom: 18px;
        }
        .btm-sanctuary-title{
          font-family: 'Cormorant Garamond', serif;
          font-weight: 400;
          font-size: clamp(44px, 7vw, 72px);
          line-height: 1.02;
          letter-spacing: -0.015em;
          color: #1A1B26;
          margin: 0 0 18px;
        }
        .btm-sanctuary-title em{
          font-style: italic;
          color: #A68966;
          font-weight: 400;
        }
        .btm-sanctuary-whisper{
          font-family: 'Cormorant Garamond', serif;
          font-style: italic;
          font-size: clamp(18px, 2.1vw, 22px);
          line-height: 1.55;
          color: rgba(26,27,38,0.62);
          max-width: 520px;
          margin: 0 auto 38px;
        }
        .btm-sanctuary-subnote{
          text-align: center;
          font-family: 'Inter', sans-serif;
          font-size: 12px;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          color: rgba(26,27,38,0.38);
          margin-top: 22px;
        }

        /* Give the single Enter button a breathing gilded presence. */
        .btm-sanctuary-wrap div[data-testid="stButton"] > button[kind="primary"]{
          background: linear-gradient(180deg, #23243049 0%, #1A1B26 100%);
          color: #F9F7F2;
          border: 1px solid rgba(166,137,102,0.55);
          border-radius: 999px;
          padding: 18px 28px;
          font-family: 'Cormorant Garamond', serif;
          font-style: italic;
          font-weight: 500;
          font-size: 20px;
          letter-spacing: 0.04em;
          animation: btmRitualPulse 5.4s ease-in-out 1.2s infinite;
          transition: transform 200ms ease, letter-spacing 300ms ease;
        }
        .btm-sanctuary-wrap div[data-testid="stButton"] > button[kind="primary"]:hover{
          transform: translateY(-1px);
          letter-spacing: 0.08em;
        }

        /* Quiet pop-over (expander) â€” Other ways in, More drawer. */
        details[data-testid="stExpander"]{
          background: rgba(249,247,242,0.55);
          backdrop-filter: blur(12px) saturate(1.1);
          -webkit-backdrop-filter: blur(12px) saturate(1.1);
          border: 1px solid rgba(26,27,38,0.06);
          border-radius: 16px;
          margin-top: 12px;
          box-shadow: 0 2px 12px rgba(26,27,38,0.04);
        }
        details[data-testid="stExpander"] summary{
          font-family: 'Inter', sans-serif;
          font-size: 13px;
          color: rgba(26,27,38,0.58);
          padding: 12px 18px;
          letter-spacing: 0.04em;
        }
        .btm-quiet-menu-intro{
          font-family: 'Cormorant Garamond', serif;
          font-style: italic;
          color: rgba(26,27,38,0.58);
          font-size: 16px;
          line-height: 1.55;
          margin-bottom: 14px;
        }

        /* --- SANCTUARY ANGEL CHAT HERO --- */
        .btm-sanctuary-column{
          padding-top: 3vh;
        }
        .btm-sanctuary-angel-hero{
          text-align: center;
          padding: 24px 12px 28px;
          animation: btmMaterialize 1.0s cubic-bezier(0.22,0.61,0.36,1) both;
        }
        .btm-sanctuary-angel-title{
          font-family: 'Cormorant Garamond', serif;
          font-weight: 400;
          font-size: clamp(32px, 4.4vw, 48px);
          line-height: 1.1;
          color: #1A1B26;
          margin: 6px 0 12px;
        }
        .btm-sanctuary-angel-sub{
          font-family: 'Cormorant Garamond', serif;
          font-style: italic;
          font-size: 18px;
          line-height: 1.55;
          color: rgba(26,27,38,0.58);
          max-width: 480px;
          margin: 0 auto;
        }

        /* --- SACRED GLASSMORPHISM â€”  translucent navy panels --- */
        .btm-sanctuary-glass{
          background: linear-gradient(180deg,
            rgba(26,27,38,0.04) 0%,
            rgba(249,247,242,0.75) 100%);
          backdrop-filter: blur(24px) saturate(1.2);
          -webkit-backdrop-filter: blur(24px) saturate(1.2);
          border: 1px solid rgba(26,27,38,0.08);
          border-radius: 24px;
          padding: 28px 32px;
          box-shadow:
            0 1px 0 rgba(255,255,255,0.88) inset,
            0 24px 64px rgba(26,27,38,0.08),
            0 1px 0 rgba(166,137,102,0.14);
          position: relative;
          overflow: hidden;
        }
        .btm-sanctuary-glass::before{
          content:"";
          position:absolute;
          inset:0;
          background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='2' seed='3'/><feColorMatrix values='0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0 0.15  0 0 0 0.018 0'/></filter><rect width='240' height='240' filter='url(%23n)' opacity='0.7'/></svg>");
          opacity:0.5;
          pointer-events:none;
          mix-blend-mode: multiply;
        }

        /* --- ILLUMINATED SCRIPTURE ANCHOR â€” manuscript look --- */
        .btm-scripture-anchor.btm-illuminated{
          text-align: center;
          padding: 28px 24px 32px;
          background:
            radial-gradient(circle at 50% 0%, rgba(166,137,102,0.10) 0%, transparent 60%),
            linear-gradient(180deg, rgba(249,247,242,0.95) 0%, rgba(249,247,242,0.75) 100%);
          border: none;
          border-radius: 18px;
          position: relative;
          animation: btmFadeDown 1.0s cubic-bezier(0.22,0.61,0.36,1) both;
        }
        .btm-illuminated-rule{
          width: 60%;
          max-width: 280px;
          height: 1px;
          margin: 0 auto 14px;
          background: linear-gradient(90deg,
            transparent 0%,
            rgba(166,137,102,0.45) 25%,
            #A68966 50%,
            rgba(166,137,102,0.45) 75%,
            transparent 100%);
        }
        .btm-illuminated-rule:last-child{
          margin: 16px auto 0;
        }
        .btm-scripture-anchor.btm-illuminated .label{
          font-family: 'Inter', sans-serif;
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 0.32em;
          text-transform: uppercase;
          color: rgba(166,137,102,0.82);
          margin-bottom: 14px;
        }
        .btm-scripture-anchor.btm-illuminated .ref{
          font-family: 'Cormorant Garamond', serif;
          font-style: italic;
          font-weight: 500;
          font-size: 32px;
          line-height: 1.15;
          color: #1A1B26;
          letter-spacing: 0.005em;
          display: flex;
          align-items: baseline;
          justify-content: center;
          gap: 10px;
        }
        .btm-dropcap{
          font-family: 'Cormorant Garamond', serif;
          font-style: normal;
          color: #A68966;
          font-size: 28px;
          line-height: 1;
          opacity: 0.9;
        }
        .btm-illuminated-sub{
          font-family: 'Cormorant Garamond', serif;
          font-style: italic;
          font-size: 13px;
          color: rgba(26,27,38,0.42);
          margin-top: 10px;
          letter-spacing: 0.02em;
        }

        /* --- SANCTUARY COMPOSER â€” st.chat_input with ritual pulse --- */
        .btm-sanctuary-composer-wrap{
          margin-top: 24px;
          padding: 4px;
          border-radius: 999px;
          animation: btmRitualPulse 5.4s ease-in-out 0.8s infinite;
        }
        /* Target Streamlit's st.chat_input container */
        div[data-testid="stChatInput"],
        section[data-testid="stChatInput"]{
          background: rgba(249,247,242,0.92) !important;
          backdrop-filter: blur(14px) saturate(1.1);
          -webkit-backdrop-filter: blur(14px) saturate(1.1);
          border: 1px solid rgba(166,137,102,0.25) !important;
          border-radius: 999px !important;
          box-shadow:
            0 1px 0 rgba(255,255,255,0.9) inset,
            0 14px 40px rgba(26,27,38,0.06) !important;
        }
        div[data-testid="stChatInput"] textarea,
        section[data-testid="stChatInput"] textarea{
          background: transparent !important;
          font-family: 'Cormorant Garamond', serif !important;
          font-style: italic !important;
          font-size: 18px !important;
          color: #1A1B26 !important;
          padding: 6px 8px !important;
        }
        div[data-testid="stChatInput"] textarea::placeholder,
        section[data-testid="stChatInput"] textarea::placeholder{
          color: rgba(26,27,38,0.38) !important;
          font-style: italic !important;
        }

        /* Sanctuary chat message bubbles â€” softer, less boxed */
        .btm-sanctuary-chat div[data-testid="stChatMessage"]{
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 18px 0 !important;
          border-bottom: 1px solid rgba(26,27,38,0.06) !important;
          border-radius: 0 !important;
        }
        .btm-sanctuary-chat div[data-testid="stChatMessage"] p{
          font-family: 'Cormorant Garamond', serif;
          font-size: 19px;
          line-height: 1.65;
          color: #1A1B26;
        }
        .btm-sanctuary-chat{
          margin-bottom: 8px;
        }

        .btm-sanctuary-privacy{
          background: rgba(249,247,242,0.7);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border: 1px solid rgba(26,27,38,0.06);
          border-radius: 16px;
          padding: 18px 22px;
          margin: 10px 0 18px;
        }

        .btm-sanctuary-footnote{
          margin-top: 30px;
          padding-top: 16px;
          border-top: 1px solid rgba(26,27,38,0.06);
          opacity: 0.68;
        }

        @media (prefers-reduced-motion: reduce){
          .btm-sanctuary-invite, .btm-sanctuary-angel-hero,
          .btm-sanctuary-composer-wrap, .btm-sanctuary-ornament,
          .btm-scripture-anchor.btm-illuminated,
          .btm-sanctuary-wrap div[data-testid="stButton"] > button[kind="primary"]{
            animation: none !important;
          }
        }

        @media (max-width: 520px){
          .btm-sanctuary-title{ font-size: 40px; }
          .btm-sanctuary-angel-title{ font-size: 30px; }
          .btm-scripture-anchor.btm-illuminated .ref{ font-size: 24px; }
          .btm-sanctuary-glass{ padding: 22px 20px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Apply the premium Vellum layer AFTER the base theme â€” this is what turns the
# dashboard into the Virtual Sanctuary: ritual pulse, materialization, scripture
# anchors, floating vellum panels.
inject_premium_layout_css()


def render_external_pill(label: str, url: str, variant: str = "secondary"):
    st.markdown(
        f'<a class="btm-pill-link {variant}" href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>',
        unsafe_allow_html=True,
    )


def render_top_nav(active: str):
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        if st.button("Home", use_container_width=True, disabled=(active == "home"), key=f"nav_home_{active}", type="secondary"):
            goto("home")
    with c2:
        if st.button("Angel Chat", use_container_width=True, disabled=(active == "angel"), key=f"nav_angel_{active}", type="secondary"):
            goto("angel")
    with c3:
        if st.button("Bible Stories", use_container_width=True, disabled=(active == "bible"), key=f"nav_bible_{active}", type="secondary"):
            goto("bible")
    with c4:
        render_external_pill("Study Hub", "https://beyondthemessage.org/study-hub/", variant="secondary")

    st.markdown('<div class="btm-hr"></div>', unsafe_allow_html=True)

# =========================
# BOTTOM NAV (MOBILE-FIRST)
# =========================
def _build_href(view_key: str) -> str:
    # Preserve existing query params (sid/theme/etc.), but set v=<view_key>
    try:
        qp = dict(st.query_params)
    except Exception:
        qp = {}
    qp["v"] = view_key
    # normalize: Streamlit may store lists; keep simple
    for k, v in list(qp.items()):
        if isinstance(v, (list, tuple)) and v:
            qp[k] = v[0]
    return "?" + urllib.parse.urlencode(qp, doseq=False)

def render_bottom_nav(active: str):
    # 4-tab bottom nav: Angel Chat | Bible Stories | Study Hub | How It Works
    items = [
        {"key": "angel", "label": "Angel Chat", "href": _build_href("angel"), "external": False},
        {"key": "bible", "label": "Bible Stories", "href": _build_href("bible"), "external": False},
        {
            "key": "study",
            "label": "Study Hub",
            "href": "https://beyondthemessage.org/study-hub/",
            "external": True,
        },
        {"key": "about", "label": "How It Works", "href": _build_href("about"), "external": False},
    ]

    links_html = []
    for item in items:
        key = item["key"]
        label = item["label"]
        href = item["href"]
        cls = "btm-nav-item active" if key == active else "btm-nav-item"
        target = ' target="_blank" rel="noopener noreferrer"' if item.get("external") else ""
        links_html.append(
            f'<a class="{cls}" href="{href}" aria-label="{label}" title="{label}"{target}>'
            f'<span class="btm-nav-label">{label}</span>'
            '</a>'
        )

    st.markdown(
        '<div class="btm-bottom-nav" role="navigation" aria-label="Bottom Navigation">'
        + "".join(links_html)
        + "</div>",
        unsafe_allow_html=True,
    )

# =========================
# HOW IT WORKS (DEDICATED PAGE)
# =========================

def render_how_it_works():
    st.markdown('<div class="btm-page">', unsafe_allow_html=True)

    st.markdown('<div class="btm-hero">', unsafe_allow_html=True)
    st.markdown('<div class="btm-hero-title">How Beyond the Message Works</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="btm-hero-sub">Two clear lanes: Study Hub guides your week. Angel Chat helps you in the moment.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown('<div class="btm-section-title">Choose the right lane</div>', unsafe_allow_html=True)

    steps = [
        ('1 â€” Start in Study Hub', 'Use Study Hub for structured weekly lessons, Daily Compass prompts, teacher notes, Journey Map, and reflection tools that keep you engaged beyond Sunday.'),
        ('2 â€” Use Angel Chat for real-life questions', 'Come to Angel Chat when you need prayer help, a practical next step, a deeper dive into Scripture, or guidance for what you are facing right now.'),
        ('3 â€” Move between them as needed', 'Study Hub gives you the guided path. Angel Chat gives you personal support in the moment. Together they create a steady rhythm for discipleship.'),
    ]
    for title, desc in steps:
        st.markdown(f'<div class="btm-step"><div class="btm-step-title">{title}</div><div class="btm-step-desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btm-grid-2">', unsafe_allow_html=True)

    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown('<div class="btm-section-title">Study Hub is best for</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="btm-bullets">'
        '<div class="btm-bullet"><span class="dot"></span><div>Sunday Message review and structured weekly learning.</div></div>'
        '<div class="btm-bullet"><span class="dot"></span><div>Daily Compass prompts that encourage steady daily use.</div></div>'
        '<div class="btm-bullet"><span class="dot"></span><div>Teacher Notes, leader flow, and guided reflection.</div></div>'
        '<div class="btm-bullet"><span class="dot"></span><div>Quick tools, Journey Map, and study-focused exploration.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown('<div class="btm-section-title">Angel Chat is best for</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="btm-bullets">'
        '<div class="btm-bullet"><span class="dot"></span><div>Prayer guidance for today, this week, or a specific burden.</div></div>'
        '<div class="btm-bullet"><span class="dot"></span><div>Practical questions where you need a next faithful step.</div></div>'
        '<div class="btm-bullet"><span class="dot"></span><div>Deeper biblical reflection when something is weighing on you.</div></div>'
        '<div class="btm-bullet"><span class="dot"></span><div>A Scripture-rooted companion that helps you respond, not just react.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btm-card btm-note">', unsafe_allow_html=True)
    st.markdown(
        '<div class="btm-note-text"><b>Simple rule:</b> Start in Study Hub for guided lessons and daily reflection. Open Angel Chat when you need personal support, practical direction, prayer help, or a deeper dive.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        render_external_pill('Open Study Hub', 'https://beyondthemessage.org/study-hub/', variant='secondary')
    with c2:
        if st.button('Open Angel Chat', use_container_width=True, key='how_open_angel', type='primary'):
            goto('angel')

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# UTIL: CLEAN + CLICKABLE SCRIPTURE LINKS (KJV)
# =========================
def _clean_ref(ref: str) -> str:
    r = (ref or "").strip()
    r = re.sub(r"\s*\((?:NKJV|KJV)\)\s*$", "", r, flags=re.IGNORECASE)
    r = re.sub(r"\s+(?:NKJV|KJV)\s*$", "", r, flags=re.IGNORECASE)
    r = re.sub(r"\s+", " ", r).strip()
    return r

def bg_url(ref: str, version: str = "KJV") -> str:
    clean = _clean_ref(ref)
    q = urllib.parse.quote(clean)
    v = (version or "KJV").upper()
    return f"https://www.biblegateway.com/passage/?search={q}&version={v}"

def kjv_url(ref: str) -> str:
    # Backward compatibility
    return bg_url(ref, "KJV")

def render_scripture_links(refs, story_md: str, version: str = "KJV"):
    """Render Scripture links from meta.json `scripture_refs`.

    We ONLY skip rendering if the MD already contains an explicit Scripture *section header*.
    (Some story MD files include their own formatted Scripture links.)
    """
    if not refs:
        return

    md_lower = (story_md or "").lower()

    # Skip only if there is an explicit Scripture header/section already in the MD
    has_scripture_section = bool(
        re.search(r"(?m)^\s*#{1,6}\s*scripture\b", md_lower)
        or "scripture (tap to read" in md_lower
        or "scripture:" in md_lower
    )
    if has_scripture_section:
        return

    v = (version or "KJV").upper()

    st.markdown('<div class="btm-scripture">', unsafe_allow_html=True)
    st.markdown(f"ðŸ“– Read First (tap to read â€” {v})", unsafe_allow_html=True)
    st.markdown("<ul>", unsafe_allow_html=True)
    for r in refs:
        label = f"{_clean_ref(r)} ({v})"
        url = bg_url(r, v)
        st.markdown(f'<li><a href="{url}">{label}</a></li>', unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SHARE CARD (HTML Preview) â€” DO NOT CHANGE
# =========================
def render_share_card_preview(body_text: str, kjv_ref: str = "", footer: str = PROD_FOOTER):
    body = (body_text or "").strip()
    ref = (kjv_ref or "").strip()
    st.markdown(
        f"""
        <div class="btm-sharecard">
          <div class="bar">SHARE THIS ENCOURAGEMENT</div>
          <div class="body">{body}</div>
          {f'<div class="ref">{ref}</div>' if ref else ''}
          <div class="foot">{footer}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption("Tip: Screenshot this card to share on TikTok, Instagram, or with a friend.")

# =========================
# OPENAI HELPERS

def _lock_try(name: str, timeout_s: int = 45) -> bool:
    now = time.time()
    flag = st.session_state.get(name, False)
    since = st.session_state.get(f"{name}_since", 0.0)
    if flag and since and (now - since) < timeout_s:
        return False
    st.session_state[name] = True
    st.session_state[f"{name}_since"] = now
    return True

def _lock_release(name: str):
    st.session_state[name] = False
    st.session_state[f"{name}_since"] = 0.0

# =========================
def _openai_client():
    """Return a cached OpenAI client (fast + stable across Streamlit reruns)."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    if not OPENAI_API_KEY:
        return None

    @st.cache_resource
    def _get_client(key: str):
        from openai import OpenAI
        return OpenAI(api_key=key)

    try:
        return _get_client(OPENAI_API_KEY)
    except Exception:
        return None

def _extract_plain_text(md: str, max_chars: int = 1800) -> str:
    if not md:
        return ""
    txt = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    txt = re.sub(r"^#{1,6}\s+", "", txt, flags=re.MULTILINE)
    txt = re.sub(r"\*\*(.*?)\*\*", r"\1", txt)
    txt = re.sub(r"\*(.*?)\*", r"\1", txt)
    txt = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:max_chars]

def _strip_json_fences(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _find_kjv_ref_in_text(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"\(([^)]{3,60}?\d+:\d+(?:[-â€“]\d+)?[^)]{0,20})\)", text)
    if m:
        return m.group(1).strip()
    return ""

def build_share_card(title: str, story_md: str, refs) -> dict:
    clean_refs = [_clean_ref(r) for r in (refs or []) if _clean_ref(r)]
    kjv_ref = clean_refs[0] if clean_refs else ""
    story_text = _extract_plain_text(story_md)

    client = _openai_client()
    if client is None:
        base = "Iâ€™m choosing to seek God early and trust Him in the middle of the noise.\nEven small obedience matters."
        hashtags = "#BeyondTheMessage #PrayerOnTheSteps #Faith #Prayer #Jesus"
        return {"caption": base.strip(), "hashtags": hashtags, "kjv_ref": kjv_ref}

    system = (
        "You write short, clear, non-cheesy faith-based social captions.\n"
        "Output JSON only with keys: caption, hashtags, kjv_ref.\n"
        "Rules:\n"
        "- Caption: 260 characters max. Punchy. Encouraging. Not preachy.\n"
        "- No long scripture quotes. Only a reference.\n"
        "- Hashtags: 3 to 6 hashtags, space-separated, include #BeyondTheMessage and #PrayerOnTheSteps.\n"
        "- Keep it safe for families.\n"
        "- Do NOT wrap JSON in markdown fences.\n"
    )

    user = (
        f"Story title: {title}\n"
        f"Story text (summary source): {story_text}\n"
        f"Preferred reference (reference only, no quotes): {kjv_ref}\n"
        "Make a share card."
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
        )
        raw = _strip_json_fences(resp.choices[0].message.content.strip())

        try:
            data = json.loads(raw)
            caption = (data.get("caption") or "").strip()
            hashtags = (data.get("hashtags") or "").strip()
            kjv_ref_out = (data.get("kjv_ref") or kjv_ref).strip()
        except Exception:
            caption = raw[:260].strip()
            hashtags = "#BeyondTheMessage #PrayerOnTheSteps #Faith #Prayer"
            kjv_ref_out = kjv_ref

        caption = caption[:260].strip()
        if not hashtags:
            hashtags = "#BeyondTheMessage #PrayerOnTheSteps #Faith #Prayer"
        if kjv_ref_out and len(kjv_ref_out) > 60:
            kjv_ref_out = kjv_ref

        return {"caption": caption, "hashtags": hashtags, "kjv_ref": kjv_ref_out}

    except Exception:
        base = "Iâ€™m choosing to seek God early and trust Him in the middle of the noise.\nEven small obedience matters."
        hashtags = "#BeyondTheMessage #PrayerOnTheSteps #Faith #Prayer #Jesus"
        return {"caption": base.strip(), "hashtags": hashtags, "kjv_ref": kjv_ref}

def build_angel_share_card_from_text(angel_text: str) -> dict:
    clean = _extract_plain_text(angel_text, max_chars=1800)
    kjv_ref = _find_kjv_ref_in_text(angel_text) or ""

    client = _openai_client()
    if client is None:
        caption = clean[:240].strip()
        hashtags = "#BeyondTheMessage #Faith #Prayer"
        return {"caption": caption, "hashtags": hashtags, "kjv_ref": kjv_ref}

    system = (
        "You write short, clear, non-cheesy faith-based share card text.\n"
        "Output JSON only with keys: caption, hashtags, kjv_ref.\n"
        "Rules:\n"
        "- Caption: 220 characters max.\n"
        "- Keep it encouraging, plainspoken.\n"
        "- No long scripture quotes; reference only if present.\n"
        "- Hashtags: 3 to 6 hashtags, space-separated, include #BeyondTheMessage.\n"
        "- Do NOT wrap JSON in markdown fences.\n"
    )
    user = (
        f"Source text (Angel response): {clean}\n"
        f"Detected reference (if any): {kjv_ref}\n"
        "Make a share card."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
        )
        raw = _strip_json_fences(resp.choices[0].message.content.strip())

        try:
            data = json.loads(raw)
            caption = (data.get("caption") or "").strip()
            hashtags = (data.get("hashtags") or "").strip()
            kjv_ref_out = (data.get("kjv_ref") or kjv_ref).strip()
        except Exception:
            caption = raw[:220].strip()
            hashtags = "#BeyondTheMessage #Faith #Prayer"
            kjv_ref_out = kjv_ref

        caption = caption[:220].strip()
        if not hashtags:
            hashtags = "#BeyondTheMessage #Faith #Prayer"
        if kjv_ref_out and len(kjv_ref_out) > 60:
            kjv_ref_out = kjv_ref
        return {"caption": caption, "hashtags": hashtags, "kjv_ref": kjv_ref_out}
    except Exception:
        caption = clean[:220].strip()
        hashtags = "#BeyondTheMessage #Faith #Prayer"
        return {"caption": caption, "hashtags": hashtags, "kjv_ref": kjv_ref}

# =========================
# INLINE STORY Q&A (stays on the same screen)
# =========================
def answer_story_question_inline(story_title: str, story_md: str, user_question: str) -> str:
    q = (user_question or "").strip()
    if not q:
        return ""

    client = _openai_client()
    if client is None:
        return (
            "Angel Q&A is ready â€” but your OpenAI key isnâ€™t connected in this Space yet.\n\n"
            "Add a Hugging Face Secret named OPENAI_API_KEY, then restart the Space."
        )

    story_text = _extract_plain_text(story_md, max_chars=1400)

    system = (
        "You are Beyond the Message â€” Story Q&A.\n"
        "Tone: calm, confident, plainspoken. Not cheesy.\n"
        "Audience: families (kids + parents). Keep it safe.\n"
        "Use KJV references (reference-only). Do not invent verses.\n"
        "Do NOT quote long scripture passages. Keep any quote very short.\n"
        "Answer format:\n"
        "1) 2â€“5 sentence answer.\n"
        "2) 1â€“2 KJV references (reference-only).\n"
        "3) One simple application step.\n"
        "4) End with ONE short follow-up question.\n"
    )

    user = (
        f"Story title: {story_title}\n"
        f"Story context (summary): {story_text}\n\n"
        f"Question: {q}\n"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.6,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"I hit an error answering that.\n\nDetails: {e}"

# =========================
# SHARE IMAGE: 1080x1080 PNG (optional)
# =========================
def build_share_image_png(title: str, caption: str, kjv_ref: str, hashtags: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    import io, textwrap

    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), "#0b1220")
    d = ImageDraw.Draw(img)

    NAVY_RGB  = (30, 58, 138)
    GOLD_RGB  = (250, 204, 21)
    CARD_BG   = (255, 255, 255)
    TEXT_DARK = (15, 23, 42)
    TEXT_MID  = (51, 65, 85)
    LIGHT_RGB = (248, 250, 252)

    d.ellipse((-380, -520, 980, 520), fill=(24, 55, 120))
    d.ellipse((-340, -480, 940, 480), fill=(11, 18, 32))

    def load_font(size: int, bold: bool = False):
        candidates = []
        if bold:
            candidates += [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "DejaVuSans-Bold.ttf",
                "LiberationSans-Bold.ttf",
            ]
        else:
            candidates += [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf",
            ]
        for p in candidates:
            try:
                if p.startswith("/") and not os.path.exists(p):
                    continue
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return None

    title_font = load_font(64, bold=True)
    body_font  = load_font(52, bold=True)
    ref_font   = load_font(34, bold=False)
    brand_font = load_font(28, bold=True)

    if not all([title_font, body_font, ref_font, brand_font]):
        return None

    pad = 70
    card_x1, card_y1 = pad, 180
    card_x2, card_y2 = W - pad, H - 170

    d.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=46, fill=CARD_BG)
    d.rounded_rectangle((card_x1, card_y1, card_x2, card_y1 + 26), radius=46, fill=GOLD_RGB)

    def mbbox(txt: str, font):
        return d.multiline_textbbox((0, 0), txt, font=font, spacing=14, align="left")

    inner_pad = 58
    x = card_x1 + inner_pad
    y_top = card_y1 + 58
    y_bottom = card_y2 - 52

    t = (title or "").strip()
    title_wrapped = textwrap.fill(t, width=22)
    d.multiline_text((x, y_top), title_wrapped, fill=NAVY_RGB, font=title_font, spacing=12)
    tb = mbbox(title_wrapped, title_font)
    title_h = tb[3] - tb[1]

    ref_line = (kjv_ref or "").strip()
    ref_h = 0
    if ref_line:
        rb = mbbox(ref_line, ref_font)
        ref_h = (rb[3] - rb[1]) + 20

    cap = (caption or "").strip()
    cap = re.sub(r"\s+", " ", cap).strip()

    caption_area_top = y_top + title_h + 26
    caption_area_bottom = y_bottom - ref_h
    cap_area_h = max(80, caption_area_bottom - caption_area_top)

    wrap_width = 26
    cap_wrapped = textwrap.fill(cap, width=wrap_width)
    cap_box = mbbox(cap_wrapped, body_font)
    cap_h = cap_box[3] - cap_box[1]

    for w in (28, 30, 32, 24, 22, 20):
        if cap_h <= cap_area_h:
            break
        cap_wrapped = textwrap.fill(cap, width=w)
        cap_box = mbbox(cap_wrapped, body_font)
        cap_h = cap_box[3] - cap_box[1]

    cap_y = caption_area_top + max(0, (cap_area_h - cap_h) // 2)
    d.multiline_text((x, cap_y), cap_wrapped, fill=TEXT_MID, font=body_font, spacing=16)

    if ref_line:
        d.text((x, y_bottom - (ref_h - 10)), ref_line, fill=TEXT_DARK, font=ref_font)

    d.text((pad, H - 95), "Beyond the Message", fill=LIGHT_RGB, font=brand_font)
    d.text((pad, H - 55), "#PrayerOnTheSteps", fill=GOLD_RGB, font=brand_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# =========================
# AGE SECTION PARSER (ROBUST + FALLBACK)
# =========================
def _normalize_dashes(s: str) -> str:
    return (s or "").replace("â€”", "-").replace("â€“", "-").replace("âˆ’", "-")

def _detect_section_level(heading_text: str) -> str:
    h = _normalize_dashes(heading_text).lower()

    if "young adult" in h or re.search(r"\badult\b", h):
        return "adult"

    if re.search(r"\bages?\b", h):
        if re.search(r"\b6\s*-\s*9\b", h):
            return "6-9"
        if re.search(r"\b10\s*-\s*13\b", h):
            return "10-13"

    if re.search(r"\b6\s*-\s*9\b", h):
        return "6-9"
    if re.search(r"\b10\s*-\s*13\b", h):
        return "10-13"

    return ""

def _slice_sections(md: str):
    text = md or ""
    matches = list(re.finditer(r"(?m)^##\s+(.*)$", text))
    sections = []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        lvl = _detect_section_level(heading)
        if not lvl:
            continue
        content_start = m.end()
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((lvl, content_start, content_end))
    return sections

def extract_age_section(md: str, age_label: str) -> str:
    if not md:
        return ""

    want = {"6â€“10": "6-9", "9â€“13": "10-13", "Adult": "adult"}.get(age_label, "adult")
    sections = _slice_sections(md)

    lookup = {}
    for lvl, s, e in sections:
        lookup[lvl] = (s, e)

    def _get(lvl: str):
        if lvl in lookup:
            s, e = lookup[lvl]
            return (md[s:e]).strip()
        return ""

    out = _get(want)
    if out:
        return out

    fallback_order = {
        "adult": ["10-13", "6-9"],
        "10-13": ["6-9"],
        "6-9": ["10-13"],
    }.get(want, [])

    for lvl in fallback_order:
        out = _get(lvl)
        if out:
            return out

    return md

# =========================
# STORY LOADER
# =========================
def load_story_cards(series_prefix):
    prefixes = series_prefix if isinstance(series_prefix, (list, tuple)) else [series_prefix]
    meta_paths = []

    for p in prefixes:
        meta_paths.extend(glob.glob(f"stories/{p}.*.meta.json"))
        meta_paths.extend(glob.glob(f"stories/{p}.*.6-10.meta.json"))
        meta_paths.extend(glob.glob(f"stories/{p}.*.9-13.meta.json"))
        meta_paths.extend(glob.glob(f"stories/{p}.*.adult.meta.json"))
        meta_paths.extend(glob.glob(f"{p}.*.meta.json"))
        meta_paths.extend(glob.glob(f"{p}-*.meta.json"))

    meta_paths = sorted(set(meta_paths))

    cards = []
    for mp in meta_paths:
        try:
            with open(mp, "r", encoding="utf-8") as f:
                meta = json.load(f)

            md_path = mp.replace(".meta.json", ".md")
            if not os.path.exists(md_path):
                alt = "stories/" + os.path.basename(md_path)
                if os.path.exists(alt):
                    md_path = alt
                else:
                    continue

            meta["_meta_path"] = mp
            meta["_md_path"] = md_path
            cards.append(meta)
        except Exception:
            continue

    def key_fn(m):
        o = m.get("order", 9999)
        t = (m.get("title") or "").lower()
        return (o, t)

    return sorted(cards, key=key_fn)

def render_rhythm_callout():
    st.markdown(
        """
        <div class="btm-card">
          <div class="btm-rhythm">
            <h4>A simple rhythm</h4>
            <p>Read the story, open the Scripture links, then journal a quick prayer or takeaway.</p>
            <div class="btm-rhythm-steps">
              Read <span class="dot"></span> Reflect <span class="dot"></span> Journal <span class="dot"></span> Share
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def _story_has_talk_about_it(story_md: str) -> bool:
    md = (story_md or "").lower()
    return ("talk about it" in md) or ("talk about it:" in md) or ("### talk about it" in md)

# =========================
# STORY READER (INLINE Q&A + Journal download fallback + ARC SELECTOR)
# =========================
def render_story_reader(series_prefix, page_title: str, subtitle: str):
    prefix_key = "-".join(series_prefix) if isinstance(series_prefix, (list, tuple)) else str(series_prefix)

    st.markdown(f'<div class="btm-page-title">{page_title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="btm-sub">{subtitle}</div>', unsafe_allow_html=True)

    render_rhythm_callout()

    # =========================
    # ARC SELECTOR
    # =========================
    def _infer_arc_from_paths(meta_path: str, md_path: str, title: str = "") -> str:
        base = (os.path.basename(md_path or meta_path or "")).lower()
        meta_l = (meta_path or "").lower()
        md_l = (md_path or "").lower()
        t = (title or "").lower()

        # Root arcs
        if base.startswith("saul-") or "saul-" in base:
            return "King Saul"
        if base.startswith("josiah-") or "josiah-" in base:
            return "King Josiah"

        # ARC 1 â€” Bridge
        if base.startswith("bridge-") or "bridge-" in base:
            return "ARC 1 Bridge"
        if base.startswith("ahab-") or "ahab-" in base:
            return "King Ahab"
        if base.startswith("elijah-") or "elijah-" in base:
            return "Elijah"
        if base.startswith("jezebel-") or "jezebel-" in base:
            return "Jezebel"

        # ARC 2 â€” The Promised King (Jesus)
        if base.startswith("jesus-") or "jesus-" in base:
            return "The Promised King"
        if base.startswith("promised-king-") or "promised-king-" in base:
            return "The Promised King"
        if "bible-stories.jesus" in base or "bible-stories.jesus" in meta_l or "bible-stories.jesus" in md_l:
            return "The Promised King"
        if "promised king" in t or "the promised king" in t:
            return "The Promised King"

            return "Jezebel"

        # Prayer on the Steps
        if "prayer-on-the-steps" in base or "prayer-on-the-steps" in meta_l or "prayer-on-the-steps" in md_l:
            return "Prayer on the Steps"

        # David series
        if "bible-stories.david" in base or "bible-stories.david" in meta_l or "bible-stories.david" in md_l:
            return "King David"

        # Saul series (older stories/ format)
        if "death-of-saul" in base or "death-of-saul" in meta_l or "death-of-saul" in md_l or "bible-stories.saul" in base:
            return "King Saul"

        # Jezebel in stories folder format
        if "bible-stories.jezebel" in base or "bible-stories.jezebel" in meta_l or "bible-stories.jezebel" in md_l:
            return "Jezebel"

        # Soft fallback from title
        if "jezebel" in t:
            return "Jezebel"
        if "david" in t:
            return "King David"
        if "josiah" in t:
            return "King Josiah"
        if "ahab" in t:
            return "King Ahab"

        return "Other Bible Stories"

    def _norm(tag: str) -> str:
        t = (tag or "").strip().lower()
        t = t.replace("â€“", "-")
        if t in ("6-10", "6-9", "6-8", "6â€“10", "6â€“9"):
            return "6-9"
        if t in ("9-13", "10-13", "9â€“13", "10â€“13"):
            return "10-13"
        if t in ("adult", "young adult", "young-adult", "youngadult"):
            return "adult"
        return t

    # Load cards once
    cards = load_story_cards(series_prefix)
    if not cards:
        st.warning(
            "No stories found.\n\n"
            "Expected files (examples):\n"
            "- stories/bible-stories.your-slug.meta.json\n"
            "- stories/bible-stories.your-slug.md\n"
            "- josiah-01-something.meta.json  (repo root)\n"
            "- josiah-01-something.md         (repo root)\n\n"
            "Meta should include reading_level like: [\"6-9\",\"10-13\",\"adult\"]."
        )
        return

    # Build arc map
    arc_map = {}
    for c in cards:
        arc = _infer_arc_from_paths(c.get("_meta_path", ""), c.get("_md_path", ""), c.get("title", ""))
        arc_map.setdefault(arc, []).append(c)

    arc_order = [
        # ARC 1 â€” Kings / Prophets
        "King Saul",
        "King David",
        "King Ahab",
        "Elijah",
        "Jezebel",
        "King Josiah",

        # ARC 2 â€” The Promised King
        "ARC 1 Bridge",

        # ARC 2 â€” The Promised King
        "The Promised King",

        # Other
        "Prayer on the Steps",
        "Other Bible Stories",
    ]
    arcs = [a for a in arc_order if (a in arc_map) or (a in ["ARC 1 Bridge", "The Promised King"])]
    arcs += [a for a in sorted(arc_map.keys()) if a not in arcs]
    arcs = sorted(arcs, key=lambda a: (arc_order.index(a) if a in arc_order else 999, a))

    # âœ… Always show the arc selector (even if only one arc) so it never â€œdisappearsâ€
    arc_pick = st.selectbox(
        "Choose an arc",
        options=arcs,
        index=0,
        key=f"arc_{prefix_key}",
    )

    # Age selector (key includes arc so switching arc doesnâ€™t cross-wire)
    age_label = st.radio(
        "Age range",
        ["6â€“10", "9â€“13", "Adult"],
        horizontal=True,
        key=f"age_{prefix_key}_{arc_pick}",
    )

    want = {"6â€“10": "6-9", "9â€“13": "10-13", "Adult": "adult"}[age_label]

    def _infer_levels_from_path(meta_path: str, md_path: str):
        p = f"{meta_path} {md_path}".lower()
        if ".6-10." in p or ".6-9." in p:
            return {"6-9"}
        if ".9-13." in p or ".10-13." in p:
            return {"10-13"}
        if ".adult." in p:
            return {"adult"}
        return set()

    # Filter only within arc_pick
    filtered = []
    for c in arc_map.get(arc_pick, []):
        levels = c.get("reading_level", None)

        if not levels:
            inferred = _infer_levels_from_path(c.get("_meta_path", ""), c.get("_md_path", ""))
            if inferred:
                if want in inferred:
                    filtered.append(c)
            else:
                filtered.append(c)
            continue

        if isinstance(levels, str):
            levels = [levels]
        norm_levels = {_norm(x) for x in levels}
        if want in norm_levels:
            filtered.append(c)

    if not filtered:
        # Adult fallback: if a story has only 6â€“10 and 9â€“13 versions, let Adult default to 9â€“13
        if want == "adult":
            fallback_want = "10-13"
            fallback = []
            for c in arc_map.get(arc_pick, []):
                levels = c.get("reading_level", None)
                if not levels:
                    inferred = _infer_levels_from_path(c.get("_meta_path", ""), c.get("_md_path", ""))
                    if inferred and (fallback_want in inferred):
                        fallback.append(c)
                    continue
                if isinstance(levels, str):
                    levels = [levels]
                norm_levels = {_norm(x) for x in levels}
                if fallback_want in norm_levels:
                    fallback.append(c)

            if fallback:
                st.info("Adult version isnâ€™t available for every story yet â€” showing the 9â€“13 version for now.")
                filtered = fallback
                want = fallback_want
            else:
                st.warning("No stories match this age range in this arc. Check meta: reading_level.")
                return
        else:
            st.warning("No stories match this age range in this arc. Check meta: reading_level.")
            return

    picked = st.selectbox(
        "Choose a story",
        options=filtered,
        format_func=lambda x: x.get("title", "Story"),
        key=f"pick_{prefix_key}_{arc_pick}_{want}",
    )

    try:
        story_md = open(picked["_md_path"], "r", encoding="utf-8").read()
    except Exception:
        st.error("Could not read the story file.")
        return

    shown_md = extract_age_section(story_md, age_label)

    st.markdown(
       f"""
        <div class="btm-card">
          <h3 style="margin:0;color:{NAVY};font-weight:900;">{picked.get('title','Story')}</h3>
          {f"<div class='btm-small'>{picked.get('subtitle')}</div>" if picked.get("subtitle") else ""}
          <div class="btm-small" style="margin-top:6px;">Arc: <b>{arc_pick}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    refs = picked.get("scripture_refs", []) or []
    render_scripture_links(refs, story_md, picked.get('version', 'KJV'))

    st.markdown(shown_md)

    questions = picked.get("reflection_questions", []) or []
    if questions and (not _story_has_talk_about_it(story_md)):
        st.markdown('<div class="btm-card">', unsafe_allow_html=True)
        st.markdown("<div class='btm-sec-title'>Talk About It</div>", unsafe_allow_html=True)
        for q in questions:
            st.markdown(f"- {q}")
        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # Ask a Question (INLINE â€” no reroute)
    # =========================
    order = picked.get("order", 0)
    qa_state_key = f"qa_{prefix_key}_{arc_pick}_{order}_{want}"
    if qa_state_key not in st.session_state:
        st.session_state[qa_state_key] = []

    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown("<div class='btm-sec-title'>Ask a Question</div>", unsafe_allow_html=True)
    st.markdown("<div class='btm-small'>Ask about the story and get an answer right here.</div>", unsafe_allow_html=True)

    with st.form(f"ask_form_{qa_state_key}", clear_on_submit=True):
        user_q = st.text_input(
            "Your question",
            value="",
            label_visibility="collapsed",
            placeholder="Type your question hereâ€¦",
        )
        cA, cB = st.columns([1, 1])
        with cA:
            ask_inline = st.form_submit_button("Ask About This Story", use_container_width=True)
        with cB:
            send_to_angel = st.form_submit_button("Send to Angel Chat", use_container_width=True)

    if ask_inline:
        q = (user_q or "").strip()
        if q:
            with st.spinner("Answeringâ€¦"):
                ans = answer_story_question_inline(picked.get("title", "Story"), story_md, q)
            st.session_state[qa_state_key].append({
                "q": q,
                "a": ans,
                "ts": datetime.utcnow().isoformat() + "Z",
            })
        else:
            st.info("Type a question first.")

    if send_to_angel:
        title = picked.get("title", "this story")
        base = f"My question is about the story titled '{title}'.\n\nHereâ€™s my question:\n"
        st.session_state.angel_prefill = base + ((user_q or "").strip())
        goto("angel")

    qa_items = st.session_state.get(qa_state_key, [])
    if qa_items:
        st.markdown("<div class='btm-hr'></div>", unsafe_allow_html=True)
        for item in reversed(qa_items[-6:]):
            qtxt = (item.get("q") or "").strip()
            atxt = (item.get("a") or "").strip()
            atxt_html = atxt.replace("\n", "<br>")
            st.markdown(
                f"""
                <div class="btm-qa-wrap" style="margin-bottom:12px;">
                  <div class="btm-qa-q">Q: {qtxt}</div>
                  <div class="btm-qa-a">{atxt_html}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # Journal (mailto + download fallback) â€” PRIVACY SAFE
    # =========================
    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown("<div class='btm-sec-title'>Journal Your Thoughts</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='btm-small'>Write a prayer, a reflection, or what you feel God is speaking. This stays on your device.</div>",
        unsafe_allow_html=True
    )

    jkey = f"journal_{prefix_key}_{arc_pick}_{order}_{want}"
    journal_text = st.text_area(
        "Journal",
        value="",
        key=jkey,
        label_visibility="collapsed",
        height=160
    )

    # âœ… Privacy-safe: do NOT set recipient. User chooses who to send to.
    subject = f"Journal Notes â€” {picked.get('title','Story')}"
    body = journal_text or ""

    query = urllib.parse.urlencode(
        {"subject": subject, "body": body},
        quote_via=urllib.parse.quote  # avoids "+" for spaces
    )
    mailto = f"mailto:?{query}"

    jA, jB = st.columns([1, 1])
    with jA:
        st.markdown(f'<a class="btm-mail" href="{mailto}">Open Email Draft</a>', unsafe_allow_html=True)
        st.caption("Your email app will open. Add your email address in To: then send.")
    with jB:
        fname = f"{prefix_key}.{arc_pick}.{order}.{want}.journal.txt".replace(" ", "-")
        st.download_button(
            "Download Journal (.txt)",
            data=(body or "").encode("utf-8"),
            file_name=fname,
            mime="text/plain",
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # Share (preview + optional PNG)
    # =========================
    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown("<div class='btm-sec-title'>Share</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='btm-small'>Tap Generate, then screenshot the share card. (No copy buttons.)</div>",
        unsafe_allow_html=True
    )

    share_key = f"share_{prefix_key}_{arc_pick}_{order}_{want}"
    if share_key not in st.session_state:
        st.session_state[share_key] = {"caption": "", "hashtags": "", "kjv_ref": ""}

    cA, cB = st.columns([1, 1])
    with cA:
        if st.button("Generate Share Card", use_container_width=True, key=f"gen_{share_key}", type="secondary"):
            with st.spinner("Generatingâ€¦"):
                card = build_share_card(picked.get("title", "Story"), story_md, refs)
            st.session_state[share_key] = card

    with cB:
        if st.button("Regenerate", use_container_width=True, key=f"regen_{share_key}", type="secondary"):
            with st.spinner("Regeneratingâ€¦"):
                card = build_share_card(picked.get("title", "Story"), story_md, refs)
            st.session_state[share_key] = card

    card = st.session_state.get(share_key, {"caption": "", "hashtags": "", "kjv_ref": ""})
    caption = (card.get("caption") or "").strip()
    kjv_ref = (card.get("kjv_ref") or "").strip()
    hashtags = (card.get("hashtags") or "").strip()

    if caption:
        render_share_card_preview(caption, kjv_ref=kjv_ref, footer=PROD_FOOTER)
        if hashtags:
            st.caption(hashtags)

        png_bytes = build_share_image_png(
            title=picked.get("title", "Story"),
            caption=caption,
            kjv_ref=(kjv_ref if kjv_ref else ""),
            hashtags=hashtags
        )
        if png_bytes:
            st.download_button(
                "Download Share Image (PNG) â€” optional",
                data=png_bytes,
                file_name=f"{prefix_key}.{arc_pick}.{order}.{want}.share.png".replace(" ", "-"),
                mime="image/png",
                use_container_width=True
            )
        else:
            st.caption("PNG export needs a system font (DejaVu/Liberation). Screenshot the card above instead.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# ANGEL CHAT
# =========================
def render_angel_chat():
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

    _load_angel_state_if_any()

    client = None
    try:
        from openai import OpenAI
        if OPENAI_API_KEY:
            client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None

    if "mode" not in st.session_state:
        st.session_state.mode = None
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "last_user_text" not in st.session_state:
        st.session_state.last_user_text = ""
    if "busy" not in st.session_state:
        st.session_state.busy = False
    if "busy_since" not in st.session_state:
        st.session_state.busy_since = 0.0
    if "openai_lock" not in st.session_state:
        st.session_state.openai_lock = False
    if "openai_lock_since" not in st.session_state:
        st.session_state.openai_lock_since = 0.0
    if "angel_share" not in st.session_state:
        st.session_state.angel_share = {"caption": "", "hashtags": "", "kjv_ref": ""}
    if "privacy_ack" not in st.session_state:
        st.session_state.privacy_ack = False
    if "angel_message_input" not in st.session_state:
        st.session_state.angel_message_input = st.session_state.get("angel_prefill", "")
    if "last_voice_hash" not in st.session_state:
        st.session_state.last_voice_hash = ""
    if "angel_placeholder_index" not in st.session_state:
        st.session_state.angel_placeholder_index = 0
    # Relational Memory â€” distilled "burden" of the conversation.
    if "burden" not in st.session_state:
        st.session_state.burden = ""
    # Hidden Intent Routing default â€” the companion senses unless user pins.
    if "mode_pinned" not in st.session_state:
        st.session_state.mode_pinned = False

    placeholder_options = [
        "I read Romans 15 today. Give me the context, key people, and leadership lessons.",
        "Explain this passage to me like a study companion and help me apply it this week.",
        "Tell me about the main person in this chapter and why their story matters.",
        "Create me a 7-day study plan from the chapter I read today.",
    ]

    def reset_chat():
        st.session_state.chat = []
        st.session_state.mode = None
        st.session_state.last_user_text = ""
        st.session_state.busy = False
        st.session_state.busy_since = 0.0
        st.session_state.angel_share = {"caption": "", "hashtags": "", "kjv_ref": ""}
        st.session_state.angel_prefill = ""
        st.session_state.angel_message_input = ""
        st.session_state.last_voice_hash = ""
        st.session_state.burden = ""
        st.session_state.mode_pinned = False
        _save_angel_state()

    def mode_label(mode_key: str) -> str:
        return {
            "prayer": "Prayer",
            "scripture": "Scripture",
            "encouragement": "Encouragement",
            "living": "Leadership & Living It Out",
        }.get(mode_key, "Scripture")

    def build_system_prompt_for_mode(mode_key: str) -> str:
        # === FAITH-ORIENTED FRIEND ===
        # The voice is a trusted Christian friend, not a tool, app, or AI.
        # Empathy precedes Scripture. Always.
        base = (
            "You are a quiet, faith-oriented friend in conversation with someone who has come to "
            "a sacred space to be heard. You are NOT an AI, a tool, an app, an assistant, or a chatbot. "
            "Never refer to yourself as such. Never say 'as an AI' or 'I am here to help'. "
            "You are simply present, the way a trusted Christian friend is present.\n\n"
            "VOICE: warm, grounded, unhurried, plainspoken. Never preachy. Never saccharine. "
            "Never academic-cold. The way someone you trust speaks to you over coffee â€” with gravity, "
            "but also tenderness.\n\n"
            "FLOW (this order matters):\n"
            "1) FIRST, name the weight. Acknowledge what the person is carrying â€” the emotion, the "
            "situation, the question beneath the question. Two or three sentences of pure presence "
            "before any Scripture.\n"
            "2) THEN, gently bring the Word. Offer 1â€“2 KJV verses that meet the moment. Not as proof "
            "texts. As gifts.\n"
            "3) THEN, illuminate. A short, thoughtful insight â€” what this Scripture is saying into "
            "their specific situation.\n"
            "4) THEN, a small invitation. One concrete next step they could take today, or a quiet "
            "prayer they could carry.\n"
            "5) FINALLY, one gentle question to keep the door open.\n\n"
            "RULES:\n"
            "â€¢ User prefers KJV; use KJV references.\n"
            "â€¢ Do NOT invent verses. Quote short â€” a phrase or a single verse, never long passages.\n"
            "â€¢ Do NOT use bullet headers like 'Scripture Anchor:' or 'Application:'. Write in prose, "
            "the way a friend writes a letter.\n"
            "â€¢ Do NOT moralize, lecture, or rebuke unless explicitly asked.\n"
            "â€¢ If the person is in crisis, gently encourage them to also reach out to a trusted "
            "person or pastor in their life.\n"
        )

        # Relational Memory â€” what the person is carrying this week.
        burden = (st.session_state.get("burden") or "").strip()
        if burden:
            base += (
                "\nWHAT YOUR FRIEND IS CARRYING (do not quote this back; let it shape your tone):\n"
                f'"{burden}"\n'
            )

        if mode_key == "prayer":
            return base + (
                "\nTHIS MOMENT â€” PRAYER:\n"
                "They are carrying something heavy. Lead with empathy. Then offer a short, sincere "
                "prayer (3â€“6 lines, second person â€” 'Lordâ€¦', 'Fatherâ€¦'). Anchor with one KJV verse. "
                "Close with a single gentle question.\n"
            )
        if mode_key == "scripture":
            return base + (
                "\nTHIS MOMENT â€” STUDY:\n"
                "They want to understand. Open with one sentence of presence ('That's a beautiful "
                "passage to sit withâ€¦' or similar). Then give the context like a friend who knows "
                "the story. Offer 2â€“3 KJV references woven into prose. Close with a single gentle "
                "question that invites them deeper.\n"
            )
        if mode_key == "encouragement":
            return base + (
                "\nTHIS MOMENT â€” ENCOURAGEMENT:\n"
                "They may not have asked for much. Be present anyway. Acknowledge whatever they "
                "shared â€” even briefly. Offer one true thing and one KJV verse that meets them. "
                "Close with a single gentle question.\n"
            )
        return base + (
            "\nTHIS MOMENT â€” LIVING IT OUT:\n"
            "They are facing a real situation. Honor the weight of it before advising. Then name "
            "the next right step â€” one concrete, small thing. Anchor with one KJV verse. Add a "
            "short prayer they can carry. Close with a single gentle question.\n"
        )

    def safe_model_response(system_prompt: str, user_text: str) -> str:
        if client is None:
            return (
                "Angel Chat is ready â€” but your OpenAI key is not connected in this Space yet.\n\n"
                "Add a Hugging Face Secret named OPENAI_API_KEY, then restart the Space."
            )
        messages = [{"role": "system", "content": system_prompt}]
        history = st.session_state.chat[-12:] if len(st.session_state.chat) > 12 else st.session_state.chat
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_text})
        if not _lock_try("openai_lock", timeout_s=45):
            return "â³ Still working on your last requestâ€¦ give it a moment, then try again."
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e)
            if "Another request is already running" in msg:
                return "â³ Still working on your last requestâ€¦ give it a moment, then try again."
            if "401" in msg or "invalid_api_key" in msg.lower():
                return "âš ï¸ OpenAI authentication error. Please re-check your OPENAI_API_KEY secret and restart the Space."
            return "I hit an error generating a response.\n\nDetails: " + msg
        finally:
            _lock_release("openai_lock")

    def set_mode(mode_key: str):
        st.session_state.mode = mode_key
        if not st.session_state.chat:
            st.session_state.chat.append({
                "role": "assistant",
                "content": "Iâ€™m ready. Start with the passage you read today, or tap one of the quick starts below."
            })
        _save_angel_state()

    def run_quick_start(prompt_text: str):
        now = time.time()
        if st.session_state.busy and st.session_state.get("busy_since", 0.0) and (now - st.session_state.get("busy_since", 0.0)) > 45:
            st.session_state.busy = False
            st.session_state.busy_since = 0.0
        if st.session_state.busy:
            st.info("â³ Still working on your last requestâ€¦ give it a moment, then try again.")
            return
        st.session_state.busy = True
        st.session_state.busy_since = now
        if not st.session_state.mode:
            st.session_state.mode = "scripture"
        st.session_state.chat.append({"role": "user", "content": prompt_text})
        _save_angel_state()
        try:
            with st.spinner("Angel Chat is writingâ€¦"):
                reply = safe_model_response(build_system_prompt_for_mode(st.session_state.mode), prompt_text)
        finally:
            st.session_state.busy = False
            st.session_state.busy_since = 0.0
        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.session_state.angel_placeholder_index = (st.session_state.angel_placeholder_index + 1) % len(placeholder_options)
        _save_angel_state()
        st.rerun()

    def _latest_angel_answer() -> str:
        for m in reversed(st.session_state.chat):
            if m.get("role") == "assistant":
                txt = (m.get("content") or "").strip()
                if txt:
                    return txt
        return ""

    def detect_intent(text: str) -> str:
        """Hidden Intent Routing â€” silently choose a mode from what the user said.

        The user never sees a mode picker. The companion feels the weight and shifts.
        Keyword-gated for now; can be upgraded to a small classify call later.
        """
        t = (text or "").lower()
        # Prayer: emotional weight, struggle, lament
        prayer_signals = (
            "pray", "prayer", "struggling", "struggle", "hurting", "hurt", "anxious",
            "anxiety", "afraid", "fear", "alone", "lonely", "tired", "exhausted",
            "broken", "lost", "grief", "grieving", "depressed", "sad", "weary",
            "burden", "burdened", "overwhelm", "i can't", "i cant", "give up",
            "heart is heavy", "need peace", "need help", "help me",
        )
        # Scripture/study: explanation, context, who/what
        scripture_signals = (
            "explain", "what does", "what is", "who is", "context", "background",
            "meaning of", "study", "teach me", "tell me about", "history of",
            "verse", "chapter", "book of", "translation", "interpret",
        )
        # Living/leadership: decisions, team, action
        living_signals = (
            "lead", "leader", "leadership", "team", "decision", "should i",
            "how do i", "at work", "my job", "boss", "career", "manage",
            "marriage", "parent", "parenting", "discipline",
        )
        if any(s in t for s in prayer_signals):
            return "prayer"
        if any(s in t for s in living_signals):
            return "living"
        if any(s in t for s in scripture_signals):
            return "scripture"
        # Default: encouragement (the gentlest fallback for short or open prompts)
        return "encouragement"

    def _distill_burden(recent_user_text: str) -> str:
        """Update st.session_state.burden â€” a short distilled string of what the
        person is carrying this week. Heuristic only; no extra API calls.
        Stored on session and persisted via _save_angel_state.
        """
        existing = (st.session_state.get("burden", "") or "").strip()
        t = (recent_user_text or "").strip()
        if not t:
            return existing
        # Lightweight heuristic: if the message is short and feels like a state
        # (mentions feeling words), we use it directly; else we keep the prior burden.
        feeling_markers = (
            "i feel", "i'm feeling", "im feeling", "i am feeling",
            "struggling", "hurting", "anxious", "afraid", "tired",
            "alone", "broken", "lost", "grieving", "weary", "overwhelmed",
            "burden", "heavy", "stuck",
        )
        low = t.lower()
        if any(m in low for m in feeling_markers):
            # Keep it short â€” first 140 chars, single line.
            distilled = " ".join(t.split())[:140]
            st.session_state.burden = distilled
            return distilled
        return existing

    def _send_user_message(text: str):
        text = (text or "").strip()
        if not text or st.session_state.busy:
            return
        st.session_state.busy = True
        st.session_state.busy_since = time.time()

        # Hidden Intent Routing â€” the companion picks the mode silently.
        # User-pinned modes (set via the hidden drawer) are respected.
        if not st.session_state.get("mode_pinned", False):
            st.session_state.mode = detect_intent(text)

        # Relational Memory â€” quietly track the burden of the conversation.
        _distill_burden(text)

        if st.session_state.angel_prefill:
            st.session_state.angel_prefill = ""
        st.session_state.last_user_text = text
        st.session_state.chat.append({"role": "user", "content": text})
        _save_angel_state()
        try:
            with st.spinner("â€¦"):
                system_prompt = build_system_prompt_for_mode(st.session_state.mode)
                reply = safe_model_response(system_prompt, text)
        finally:
            st.session_state.busy = False
            st.session_state.busy_since = 0.0
        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.session_state.angel_placeholder_index = (st.session_state.angel_placeholder_index + 1) % len(placeholder_options)
        _save_angel_state()
        st.rerun()

    placeholder_text = "What is on your heart? (e.g., I need peace todayâ€¦)"

    # ============================================================
    # CENTER-ANCHORED SANCTUARY COLUMN
    # The entire conversation lives in a single 700-ish px reading column.
    # ============================================================
    st.markdown('<div class="btm-sanctuary-column">', unsafe_allow_html=True)
    sanctuary_left, sanctuary_center, sanctuary_right = st.columns([1, 2, 1])

    with sanctuary_center:
        # Quiet hero â€” no kicker chip, no "AI companion" framing.
        st.markdown(
            """
            <div class="btm-sanctuary-angel-hero">
              <div class="btm-sanctuary-ornament">âœ¦</div>
              <h1 class="btm-sanctuary-angel-title">A quiet place in Scripture</h1>
              <p class="btm-sanctuary-angel-sub">Bring what is on your heart. The Word will meet you here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Privacy acknowledgement â€” softened.
        if not st.session_state.get("privacy_ack", False):
            st.markdown(
                """
                <div class="btm-privacy btm-sanctuary-privacy">
                  <div class="title">A quiet promise</div>
                  <p class="line"><span class="strong">What you share stays here.</span> Nothing is saved, remembered, or tracked across sessions.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Continue", use_container_width=True, key="privacy_ack_btn", type="primary"):
                st.session_state.privacy_ack = True
                _save_angel_state()
                st.rerun()

        # ============================================================
        # CHAT HISTORY (renders above composer)
        # ============================================================
        st.markdown('<div class="btm-sanctuary-chat">', unsafe_allow_html=True)
        for m in st.session_state.chat:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # RESPONSE SHELL â€” Progressive Reveal (Scripture Anchor first)
        # ============================================================
        latest = _latest_angel_answer()
        detected_ref = _find_kjv_ref_in_text(latest)
        if latest:
            st.markdown('<div class="btm-response-shell btm-sanctuary-glass">', unsafe_allow_html=True)
            if detected_ref:
                st.markdown(
                    f"""
                    <div class="btm-scripture-anchor btm-illuminated">
                      <div class="btm-illuminated-rule"></div>
                      <div class="label">Scripture Anchor</div>
                      <div class="ref"><span class="btm-dropcap">&#10023;</span>{detected_ref}</div>
                      <div class="btm-illuminated-sub">Verily, the Word is a lamp.</div>
                      <div class="btm-illuminated-rule"></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # THE COMPOSER â€” single breathing input, no mode buttons visible
        # ============================================================
        st.markdown('<div class="btm-sanctuary-composer-wrap">', unsafe_allow_html=True)
        user_msg = st.chat_input(
            placeholder=placeholder_text,
            key="angel_chat_input",
            disabled=st.session_state.busy,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if user_msg:
            _send_user_message(user_msg)

        # ============================================================
        # QUIET "MORE" DRAWER â€” mode pinning + quick starts + deeper tools
        # Everything that was a persistent button is now one collapse away.
        # ============================================================
        with st.expander("â‹¯  More", expanded=False):
            st.markdown(
                '<div class="btm-quiet-menu-intro">The companion senses your intent. These are here if you want to steer it yourself.</div>',
                unsafe_allow_html=True,
            )

            st.markdown("**Pin a mode** (optional)")
            pin_cols = st.columns(4)
            with pin_cols[0]:
                if st.button("Auto-sense", use_container_width=True, key="pin_auto", type="secondary"):
                    st.session_state.mode_pinned = False
                    st.session_state.mode = None
                    _save_angel_state()
                    st.rerun()
            with pin_cols[1]:
                if st.button("Scripture", use_container_width=True, key="pin_scripture", type="secondary"):
                    st.session_state.mode_pinned = True
                    set_mode("scripture")
                    st.rerun()
            with pin_cols[2]:
                if st.button("Prayer", use_container_width=True, key="pin_prayer", type="secondary"):
                    st.session_state.mode_pinned = True
                    set_mode("prayer")
                    st.rerun()
            with pin_cols[3]:
                if st.button("Leadership", use_container_width=True, key="pin_living", type="secondary"):
                    st.session_state.mode_pinned = True
                    set_mode("living")
                    st.rerun()

            if st.session_state.get("mode_pinned"):
                st.caption(f"Currently pinned: **{mode_label(st.session_state.mode)}**")
            else:
                st.caption("Auto-sensing mode from what you share.")

            st.markdown("---")
            st.markdown("**Quick starts**")
            q1, q2 = st.columns(2)
            with q1:
                if st.button("Context of what I read", use_container_width=True, disabled=st.session_state.busy, key="qs_context", type="secondary"):
                    run_quick_start("Give me the context of the chapter I read today â€” what is happening, who is involved, and why it matters.")
                if st.button("7-Day plan from this passage", use_container_width=True, disabled=st.session_state.busy, key="qs_weekly_plan", type="secondary"):
                    run_quick_start("Create me a 7-day study plan from the passage I read today, anchored in KJV scripture.")
            with q2:
                if st.button("Leadership lens", use_container_width=True, disabled=st.session_state.busy, key="qs_leadership", type="secondary"):
                    run_quick_start("Show me the leadership lens from the passage I read today and how I can apply it.")
                if st.button("The person in this chapter", use_container_width=True, disabled=st.session_state.busy, key="qs_person", type="secondary"):
                    run_quick_start("Tell me about the main person in the passage I read today, including context, character, and what I can learn from them.")

            if latest:
                st.markdown("---")
                st.markdown("**Go deeper with the last response**")
                d1, d2, d3 = st.columns(3)
                with d1:
                    if st.button("Deeper into this chapter", use_container_width=True, key="deeper_chapter", type="secondary"):
                        run_quick_start("Go deeper into the same chapter and help me see more of the context, structure, and main ideas.")
                with d2:
                    if st.button("Build a weekly plan", use_container_width=True, key="deeper_plan", type="secondary"):
                        run_quick_start("Take this response and turn it into a 7-day Bible study plan with KJV anchors for each day.")
                with d3:
                    if st.button("Leadership lens", use_container_width=True, key="deeper_leadership", type="secondary"):
                        run_quick_start("Take this same passage and teach it through a leadership lens with clear application.")

                st.markdown("---")
                st.markdown("**Share**")
                cA, cB, cC = st.columns([1, 1, 1])
                with cA:
                    if st.button("Create Share Card", use_container_width=True, disabled=st.session_state.busy or (not latest), key="angel_make_share", type="primary"):
                        with st.spinner("Creatingâ€¦"):
                            st.session_state.angel_share = build_angel_share_card_from_text(latest)
                        _save_angel_state()
                with cB:
                    if st.button("Regenerate", use_container_width=True, disabled=st.session_state.busy or (not latest), key="angel_regen_share", type="secondary"):
                        with st.spinner("Regeneratingâ€¦"):
                            st.session_state.angel_share = build_angel_share_card_from_text(latest)
                        _save_angel_state()
                with cC:
                    share_url = f"https://angel.beyondthemessage.org/?v=angel&theme={_get_theme()}"
                    st.link_button("Share with a Friend", share_url, use_container_width=True)

                a = st.session_state.angel_share
                a_caption = (a.get("caption") or "").strip()
                a_tags = (a.get("hashtags") or "").strip()
                a_ref = (a.get("kjv_ref") or detected_ref or "").strip()
                if a_caption:
                    render_share_card_preview(a_caption, kjv_ref=a_ref, footer=PROD_FOOTER)
                    if a_ref:
                        st.caption(f"Anchor verse: {a_ref} (KJV)")
                    if a_tags:
                        st.caption(a_tags)
                    png_bytes = build_share_image_png(
                        title="Share This Encouragement",
                        caption=a_caption,
                        kjv_ref=(a_ref if a_ref else ""),
                        hashtags=a_tags,
                    )
                    if png_bytes:
                        st.download_button(
                            "Download Share Image (PNG)",
                            data=png_bytes,
                            file_name="angel.share.png",
                            mime="image/png",
                            use_container_width=True,
                        )

            st.markdown("---")
            st.markdown("**Other ways in**")
            r1, r2, r3 = st.columns(3)
            with r1:
                render_external_pill("Study Hub", "https://beyondthemessage.org/study-hub/", variant="secondary")
            with r2:
                if st.button("Bible Stories", use_container_width=True, key="angel_to_bible", type="secondary"):
                    goto("bible")
            with r3:
                if st.button("New conversation", use_container_width=True, disabled=st.session_state.busy, key="angel_new_chat", type="secondary"):
                    reset_chat()
                    st.rerun()

        # Quiet footer caption
        st.markdown('<div class="btm-sanctuary-footnote">', unsafe_allow_html=True)
        footL, footR = st.columns([1, 1])
        with footL:
            st.caption("Please verify with Scripture (KJV).")
        with footR:
            st.caption("Key connected" if OPENAI_API_KEY else "Add Secret: OPENAI_API_KEY")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# HOME
# =========================
def render_home():
    st.markdown('<div class="btm-wrap btm-sanctuary-wrap">', unsafe_allow_html=True)

    # Single invitation — no dashboard, no path cards, no chip rows on first view.
    # The sanctuary asks one thing: come in.
    left_sp, center_col, right_sp = st.columns([1, 2, 1])
    with center_col:
        st.markdown(
            """
            <div class="btm-sanctuary-invite">
              <div class="btm-sanctuary-ornament">✦</div>
              <div class="btm-sanctuary-kicker">A quiet place in Scripture</div>
              <h1 class="btm-sanctuary-title">Beyond the <em>Message</em></h1>
              <p class="btm-sanctuary-whisper">Bring what is on your heart. The Word will meet you here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Enter Angel Chat",
            use_container_width=True,
            key="home_enter_angel_chat",
            type="primary",
        ):
            goto("angel")

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        st.markdown(
            """
            <style>
              .btm-sanctuary-wrap div[data-testid="stLinkButton"] a,
              .btm-sanctuary-wrap a[data-testid="stBaseButton-primary"] {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
                min-height: 58px !important;
                background: linear-gradient(180deg, #232430 0%, #1A1B26 100%) !important;
                color: #F9F7F2 !important;
                border: 1px solid rgba(166,137,102,0.55) !important;
                border-radius: 999px !important;
                font-family: 'Cormorant Garamond', serif !important;
                font-style: italic !important;
                font-size: 20px !important;
                font-weight: 500 !important;
                letter-spacing: 0.04em !important;
                text-decoration: none !important;
                box-shadow:
                  0 1px 0 rgba(255,255,255,0.05) inset,
                  0 1px 2px rgba(26,27,38,0.24),
                  0 18px 44px rgba(26,27,38,0.24) !important;
                transition: transform 200ms ease, letter-spacing 300ms ease, box-shadow 200ms ease !important;
              }
              .btm-sanctuary-wrap div[data-testid="stLinkButton"] a:hover,
              .btm-sanctuary-wrap a[data-testid="stBaseButton-primary"]:hover {
                transform: translateY(-1px) !important;
                letter-spacing: 0.08em !important;
                box-shadow:
                  0 1px 0 rgba(255,255,255,0.07) inset,
                  0 1px 2px rgba(26,27,38,0.28),
                  0 24px 56px rgba(26,27,38,0.30),
                  0 0 0 1px rgba(166,137,102,0.45) !important;
              }
              .btm-sanctuary-wrap div[data-testid="stLinkButton"] p {
                color: #F9F7F2 !important;
                font-family: 'Cormorant Garamond', serif !important;
                font-style: italic !important;
                font-size: 20px !important;
                font-weight: 500 !important;
                letter-spacing: inherit !important;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.link_button(
            "Enter King's Counsel",
            "https://king-s-counsel-leadership-app.vercel.app/",
            use_container_width=True,
            type="primary",
        )

        st.markdown(
            '<div class="btm-sanctuary-subnote">One conversation. No menus. No noise.</div>',
            unsafe_allow_html=True,
        )

    # Quiet secondary tools — tucked into a soft pop-over, not shouting.
    with st.expander("⋯  Other ways in", expanded=False):
        st.markdown(
            '<div class="btm-quiet-menu-intro">When you are ready to go deeper, these stay accessible.</div>',
            unsafe_allow_html=True,
        )
        qmenu_a, qmenu_b, qmenu_c = st.columns(3)
        with qmenu_a:
            if st.button("Bible Stories", use_container_width=True, key="home_quiet_bible", type="secondary"):
                goto("bible")
        with qmenu_b:
            render_external_pill("Study Hub", "https://beyondthemessage.org/study-hub/", variant="secondary")
        with qmenu_c:
            if st.button("How this works", use_container_width=True, key="home_quiet_about", type="secondary"):
                goto("about")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RENDER ROUTES
# =========================
if st.session_state.view == "home":
    render_home()
    render_bottom_nav(active="angel")

elif st.session_state.view == "angel":
    render_angel_chat()
    render_bottom_nav(active="angel")

elif st.session_state.view == "bible":
    render_story_reader(
        ["bible-stories", "josiah", "saul", "ahab", "elijah", "jezebel", "david", "bridge", "jesus", "promised-king"],
        "Stories of the Bible",
        "Age-based stories and reflection prompts, anchored in Scripture."
    )
    render_bottom_nav(active="bible")

elif st.session_state.view == "steps":
    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown("<div class='btm-sec-title'>Study Hub</div>", unsafe_allow_html=True)
    st.markdown(
        "Prayer on the Steps now lives inside Study Hub on the Beyond the Message website. "
        "Use the button below to open guided weekly lessons, Daily Compass, Quick Tools, and Journey Map.",
        unsafe_allow_html=False,
    )
    st.link_button(
        "Open Study Hub",
        "https://beyondthemessage.org/study-hub/",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    render_bottom_nav(active="study")

elif st.session_state.view == "about":
    render_how_it_works()
    render_bottom_nav(active="about")

else:
    render_home()
    render_bottom_nav(active="angel")

