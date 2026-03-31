# ============================================================
# FULL app.py — Beyond the Message / Prayer Angel (Single File)
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
    _ICON = "🕯️"

st.set_page_config(
    page_title="Prayer Angel — Beyond the Message",
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
        <meta name="theme-color" content="#1e3a8a">
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
# COLORS / TOKENS
# =========================
NAVY   = "#1e3a8a"
GOLD   = "#facc15"
SLATE  = "#334155"
LIGHT  = "#f8fafc"
MID    = "#475569"
BORDER = "#e5e7eb"
INK    = "#0b1220"

PROD_FOOTER = "BEYOND THE MESSAGE • angel.beyondthemessage.org"

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
    except Exception:
        pass

# =========================
# STYLE (BRAND + BUTTON TYPES)
# FIX: DO NOT USE f""" ... { ... } ... """ with JS/CSS braces
# =========================

def _theme_tokens(theme: str) -> dict:
    if theme == "dark":
        return {
            "bg": "#020617",
            "card": "#0b1220",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "border": "rgba(148,163,184,.20)",
            "card_glow": "rgba(250,204,21,.06)",
            "chip_bg": "rgba(30,58,138,.20)",
            "chip_border": "rgba(148,163,184,.35)",
        }
    return {
        "bg": LIGHT,
        "card": "#ffffff",
        "text": "#0f172a",
        "muted": MID,
        "border": BORDER,
        "card_glow": "rgba(30,58,138,.05)",
        "chip_bg": "rgba(250,204,21,.22)",
        "chip_border": "rgba(30,58,138,.20)",
    }

def inject_css(theme: str):
    tokens = _theme_tokens(theme)
    css = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Playfair+Display:wght@600;700&display=swap');
      /* ========= THEME TOKENS ========= */
      :root{
        --bg: __BG__;
        --card: __CARD__;
        --text: __TEXT__;
        --muted: __MUTED__;
        --navy: __NAVY__;
        --gold: __GOLD__;
        --border: __BORDER__;
        --card-glow: __CARD_GLOW__;
        --chip-bg: __CHIP_BG__;
        --chip-border: __CHIP_BORDER__;
        --success: #16a34a;
        --warning: #ea580c;
        --error: #dc2626;
        --ink: #0f172a;
        --focus: rgba(30,58,138,.35);
      }
      html, body, .stApp{
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      h1, h2, h3, h4, h5 {
        letter-spacing: -0.02em;
      }
      a {
        color: var(--navy);
      }
      :focus-visible {
        outline: 3px solid var(--focus);
        outline-offset: 2px;
        border-radius: 8px;
      }

      /* Layout */
      .block-container {
        padding-top: 2.25rem;
        padding-bottom: 2.25rem;
        max-width: 980px;
      }

      /* Kill Streamlit chrome */
      #MainMenu { visibility: hidden; }
      header { visibility: hidden; }
      footer { visibility: hidden; }

      /* Brand wrapper */
      .btm-wrap {
        max-width: 980px;
        margin: 0 auto;
        color: var(--text);
      }

      /* Hero (matches Study Hub vibe) */
      .btm-hero {
        padding: 22px 22px 18px 22px;
        border-radius: 22px;
        background:
          radial-gradient(1200px 380px at 20% -12%, rgba(250,204,21,.20), transparent),
          linear-gradient(150deg, #0b1220 0%, #0f172a 62%, #0b1220 100%);
        box-shadow: 0 24px 60px rgba(15,23,42,.35);
        margin-bottom: 16px;
        overflow: hidden;
      }
      .btm-hero h1 {
        margin: 0;
        font-size: 44px;
        font-weight: 900;
        letter-spacing: -0.02em;
        color: __LIGHT__;
      }
      .btm-hero h1 span { color: __GOLD__; }

      .btm-hero p {
        margin: 10px 0 0 0;
        color: #cbd5e1;
        font-size: 14px;
        line-height: 1.6;
      }
      .btm-note {
        color: #a8b3c5;
        font-size: 13px;
        margin: 8px 0 0 0;
      }

      .btm-page-title {
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -0.02em;
        margin: 6px 0 2px 0;
        color: __NAVY__;
      }
      .btm-sub {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 12px;
      }

      /* Fortune-500-ish section title underline (subtle) */
      .btm-sec-title{
        font-weight: 950;
        color: __NAVY__;
        letter-spacing: -0.01em;
        margin: 2px 0 12px 0;
        display:inline-block;
        padding-bottom: 6px;
        border-bottom: 3px solid rgba(30,58,138,.18);
      }
      .btm-sec-title.is-serif{
        font-family: "Playfair Display", "Libre Baskerville", serif;
      }

      /* Cards */
      .btm-card {
        background: linear-gradient(180deg, var(--card-glow), transparent 55%), var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 18px 40px rgba(15,23,42,.10);
        margin-bottom: 14px;
      }
      .btm-card-tight {
        background: linear-gradient(180deg, var(--card-glow), transparent 60%), var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 12px 24px rgba(15,23,42,.08);
        margin-bottom: 14px;
      }

      .btm-hr {
        height: 1px;
        border: 0;
        background: var(--border);
        margin: 18px 0;
      }

      .btm-small {
        font-size: 12px;
        color: #64748b;
      }
      .btm-kicker{
        text-transform: uppercase;
        letter-spacing: .16em;
        font-size: 11px;
        font-weight: 800;
        color: rgba(148,163,184,.85);
      }
      .btm-badge{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid var(--border);
        background: rgba(250,204,21,.18);
        color: var(--ink);
      }
      .btm-badge.success{ background: rgba(22,163,74,.15); color: var(--success); }
      .btm-badge.warn{ background: rgba(234,88,12,.15); color: var(--warning); }
      .btm-badge.error{ background: rgba(220,38,38,.15); color: var(--error); }

      /* Scripture box */
      .btm-scripture {
        background: __NAVY__;
        border-radius: 16px;
        padding: 18px 18px 16px 18px;
        color: __LIGHT__;
        box-shadow: 0 18px 36px rgba(15,23,42,.26);
        margin-bottom: 14px;
      }
      .btm-scripture h3 {
        margin: 0 0 10px 0;
        font-size: 16px;
        color: __GOLD__;
        letter-spacing: .01em;
        font-family: "Playfair Display", "Libre Baskerville", serif;
      }
      .btm-scripture a {
        color: __GOLD__;
        font-weight: 800;
        text-decoration: underline;
      }

      /* Rhythm callout */
      .btm-rhythm {
        border: 2px solid rgba(250,204,21,.75);
        background: rgba(250,204,21,.10);
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 12px 28px rgba(15,23,42,.10);
      }
      .btm-rhythm h4 {
        margin: 0 0 6px 0;
        color: __NAVY__;
        font-size: 16px;
        font-weight: 900;
      }
      .btm-rhythm p {
        margin: 0;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.4;
      }
      .btm-rhythm .btm-rhythm-steps {
        margin-top: 10px;
        font-weight: 900;
        color: __NAVY__;
        letter-spacing: .01em;
      }
      .btm-rhythm .dot {
        display:inline-block;
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: rgba(30,58,138,.55);
        margin: 0 10px 1px 10px;
      }

      /* ===== Share Card Preview (Study Notes vibe) ===== */
      .btm-sharecard {
        background: __NAVY__;
        border-radius: 16px;
        padding: 16px;
        color: __LIGHT__;
        box-shadow: 0 18px 40px rgba(15,23,42,.26);
        border: 1px solid rgba(255,255,255,.10);
        overflow:hidden;
        margin-bottom: 10px;
      }
      .btm-sharecard .bar {
        background: rgba(250,204,21,.98);
        color: #0b1220;
        font-weight: 900;
        letter-spacing: .08em;
        font-size: 12px;
        padding: 10px 12px;
        border-radius: 12px;
        display:inline-block;
        margin-bottom: 12px;
        text-transform: uppercase;
      }
      .btm-sharecard .body {
        font-size: 15px;
        line-height: 1.45;
        color: #e2e8f0;
        margin-bottom: 12px;
        white-space: pre-wrap;
      }
      .btm-sharecard .ref {
        font-weight: 900;
        color: __GOLD__;
        margin-top: 6px;
        font-size: 13px;
      }
      .btm-sharecard .foot {
        margin-top: 14px;
        font-size: 11px;
        color: rgba(248,250,252,.75);
        letter-spacing: .08em;
        text-transform: uppercase;
      }

      /* Inputs */
      input, textarea, select {
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        background: var(--card) !important;
        color: var(--text) !important;
        padding: 10px 12px !important;
      }
      input:focus, textarea:focus, select:focus {
        border-color: var(--navy) !important;
        box-shadow: 0 0 0 3px rgba(30,58,138,.18) !important;
      }

      
      /* Hide Streamlit inline input instructions (they can overlap on mobile) */
      div[data-testid="stTextInput"] [data-testid="InputInstructions"],
      div[data-testid="stTextArea"]  [data-testid="InputInstructions"],
      div[data-testid="stTextInput"] div[aria-live="polite"],
      div[data-testid="stTextArea"]  div[aria-live="polite"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
      }

/* ========= BUTTON SYSTEM ========= */
      div[data-testid="stButton"] > button[kind="primary"] {
        background: __NAVY__ !important;
        color: __LIGHT__ !important;
        font-weight: 900 !important;
        border: 1px solid rgba(0,0,0,.06) !important;
        border-radius: 14px !important;
        padding: 12px 18px !important;
        box-shadow: 0 12px 24px rgba(30,58,138,.25) !important;
      }
      div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 32px rgba(30,58,138,.35) !important;
      }
      div[data-testid="stButton"] > button[kind="primary"].gold-cta {
        background: __GOLD__ !important;
        color: __NAVY__ !important;
        box-shadow: 0 12px 24px rgba(250,204,21,.30) !important;
      }

      /* OUTLINED SECONDARY */
      div[data-testid="stButton"] > button[kind="secondary"] {
        background: var(--card) !important;
        color: __NAVY__ !important;
        font-weight: 900 !important;
        border: 2px solid rgba(30,58,138,.55) !important;
        border-radius: 14px !important;
        padding: 12px 18px !important;
        box-shadow: 0 10px 22px rgba(15,23,42,.08) !important;
      }
      div[data-testid="stButton"] > button[kind="secondary"]:hover {
        transform: translateY(-1px);
        background: __NAVY__ !important;
        color: __LIGHT__ !important;
        border-color: rgba(250,204,21,.85) !important;
        box-shadow: 0 14px 28px rgba(15,23,42,.12) !important;
      }

      /* Mail link button (more compatible than st.link_button on some WebViews) */
      .btm-mail {
        display:block;
        width:100%;
        text-align:center;
        text-decoration:none;
        font-weight:900;
        color: __NAVY__;
        background:#fff;
        border:2px solid rgba(30,58,138,.35);
        border-radius:14px;
        padding:12px 18px;
        box-shadow: 0 10px 22px rgba(15,23,42,.08);
      }
      .btm-mail:hover{
        background: __NAVY__;
        color: __LIGHT__;
        border-color: rgba(250,204,21,.85);
      }

      /* Inline Q&A bubble styles */
      .btm-qa-wrap{
        border: 1px solid rgba(15,23,42,.08);
        border-radius: 16px;
        padding: 14px;
        background: rgba(248,250,252,.92);
      }
      .btm-qa-q{
        font-weight: 900;
        color: __NAVY__;
        margin: 0 0 8px 0;
      }
      .btm-qa-a{
        margin: 0;
        color: var(--muted);
        line-height: 1.5;
      }

      /* ===== Pill Controls ===== */
      div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 8px;
      }
      div[data-testid="stRadio"] div[role="radiogroup"] > label {
        border-radius: 999px;
        padding: 6px 16px;
        border: 1px solid var(--chip-border);
        background: var(--chip-bg);
        color: var(--muted);
        font-weight: 800;
        box-shadow: 0 10px 24px rgba(15,23,42,.10);
      }
      div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        border-color: rgba(30,58,138,.6);
        background: rgba(30,58,138,.12);
        color: __NAVY__;
      }
      div[data-testid="stRadio"] div[role="radiogroup"] > label input:checked + div {
        background: __NAVY__;
        color: __LIGHT__;
        border-radius: 999px;
        padding: 6px 16px;
        box-shadow: 0 12px 28px rgba(30,58,138,.32);
      }

      /* Subtle separators for Fortune-500 polish */
      .btm-hr {
        height: 1px;
        border: 0;
        background: linear-gradient(90deg, rgba(226,232,240,0), var(--border), rgba(226,232,240,0));
        margin: 18px 0;
      }

      /* ========= MOBILE BUTTON SIZING ========= */
      @media (max-width: 520px){
        div[data-testid="stButton"] > button{
          padding: 10px 12px !important;
          border-radius: 12px !important;
          font-size: 0.95rem !important;
          line-height: 1.15 !important;
        }
        .btm-card{ padding: 14px !important; }
        .btm-card-tight{ padding: 12px !important; }
      }

      /* ========= PRIVACY REASSURANCE ========= */
      .btm-privacy{
        border: 1px solid rgba(148,163,184,.28);
        background: rgba(30,58,138,.06);
        border-radius: 16px;
        padding: 14px 14px;
        margin: 10px 0 14px 0;
      }
      .btm-privacy .title{
        font-weight: 950;
        color: __NAVY__;
        letter-spacing: -0.01em;
        margin: 0 0 6px 0;
      }
      .btm-privacy .line{
        margin: 0;
        font-size: 13px;
        line-height: 1.45;
        color: var(--muted);
      }
      .btm-privacy .strong{
        color: var(--text);
        font-weight: 900;
      }
      .btm-privacy .bullets{
        margin: 10px 0 0 0;
        padding-left: 18px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
      }
      .btm-privacy-mini{
        margin-top: 10px;
        padding: 10px 12px;
        border-radius: 14px;
        border: 1px dashed rgba(148,163,184,.35);
        background: rgba(250,204,21,.10);
        color: var(--muted);
        font-size: 12.5px;
        line-height: 1.45;
      }

    
      /* ========= BOTTOM NAV ========= */
      .btm-bottom-nav{
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
        background: rgba(0,0,0,0);
        backdrop-filter: blur(10px);
      }
      .btm-nav-item{
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        border: 1px solid rgba(148,163,184,.55);
        background: rgba(255,255,255,.78);
        color: var(--text);
        border-radius: 14px;
        height: 54px;
        box-shadow: 0 10px 30px rgba(2,6,23,.08);
        padding: 0 10px;
      }
      .btm-nav-item .btm-nav-label{
        font-weight: 800;
        font-size: 14px;
        line-height: 1.1;
        text-align: center;
      }
      .btm-nav-item.active{
        background: var(--navy);
        color: #ffffff !important;
        border-color: rgba(250,204,21,.55);
        box-shadow: 0 14px 36px rgba(2,6,23,.18);
      }
      .btm-nav-item.active .btm-nav-label{
        text-decoration: none !important;
      }

      /* Keep content visible above fixed nav */
      section.main > div{
        padding-bottom: 120px !important;
      }

      /* ========= HOW IT WORKS ========= */
      .btm-grid-2{
        display: grid;
        grid-template-columns: 1fr;
        gap: 14px;
      }
      @media (min-width: 900px){
        .btm-grid-2{ grid-template-columns: 1fr 1fr; }
      }
      .btm-section-title{
        font-size: 18px;
        font-weight: 900;
        margin-bottom: 8px;
      }
      .btm-step{
        padding: 12px 0;
        border-top: 1px solid rgba(148,163,184,.35);
      }
      .btm-step:first-of-type{ border-top: none; padding-top: 2px; }
      .btm-step-title{
        font-weight: 900;
        margin-bottom: 4px;
      }
      .btm-step-desc{
        color: var(--muted);
        font-weight: 600;
      }
      .btm-bullets{ display: grid; gap: 10px; }
      .btm-bullet{ display:flex; gap:10px; align-items:flex-start; }
      .btm-bullet .dot{
        width: 10px; height: 10px; border-radius: 999px;
        background: var(--gold);
        margin-top: 6px;
        flex: 0 0 auto;
      }

      .btm-note{ border: 1px solid rgba(250,204,21,.35); }
      .btm-note-text{ font-weight: 650; color: var(--text); }

      /* ===== External CTA pills ===== */
      .btm-pill-link {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 48px;
        width: 100%;
        text-decoration: none !important;
        font-weight: 900;
        border-radius: 14px;
        padding: 12px 18px;
        box-sizing: border-box;
        transition: all .18s ease;
      }
      .btm-pill-link.secondary {
        background: var(--card);
        color: __NAVY__ !important;
        border: 2px solid rgba(30,58,138,.55);
        box-shadow: 0 10px 22px rgba(15,23,42,.08);
      }
      .btm-pill-link.secondary:hover {
        transform: translateY(-1px);
        background: __NAVY__;
        color: __LIGHT__ !important;
        border-color: rgba(250,204,21,.85);
        box-shadow: 0 14px 28px rgba(15,23,42,.12);
      }
      .btm-pill-link.primary {
        background: __NAVY__;
        color: __LIGHT__ !important;
        border: 1px solid rgba(0,0,0,.06);
        box-shadow: 0 12px 24px rgba(30,58,138,.25);
      }
      .btm-voice-wrap {
        border: 1px dashed rgba(30,58,138,.28);
        border-radius: 14px;
        padding: 12px 14px;
        background: rgba(250,204,21,.08);
        margin: 10px 0 12px 0;
      }
      .btm-voice-title {
        font-weight: 900;
        color: __NAVY__;
        margin-bottom: 4px;
      }
      .btm-voice-copy {
        color: var(--muted);
        font-size: 12.5px;
        line-height: 1.4;
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
        ('1 — Start in Study Hub', 'Use Study Hub for structured weekly lessons, Daily Compass prompts, teacher notes, Journey Map, and reflection tools that keep you engaged beyond Sunday.'),
        ('2 — Use Angel Chat for real-life questions', 'Come to Angel Chat when you need prayer help, a practical next step, a deeper dive into Scripture, or guidance for what you are facing right now.'),
        ('3 — Move between them as needed', 'Study Hub gives you the guided path. Angel Chat gives you personal support in the moment. Together they create a steady rhythm for discipleship.'),
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
    st.markdown(f"📖 Read First (tap to read — {v})", unsafe_allow_html=True)
    st.markdown("<ul>", unsafe_allow_html=True)
    for r in refs:
        label = f"{_clean_ref(r)} ({v})"
        url = bg_url(r, v)
        st.markdown(f'<li><a href="{url}">{label}</a></li>', unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SHARE CARD (HTML Preview) — DO NOT CHANGE
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
    m = re.search(r"\(([^)]{3,60}?\d+:\d+(?:[-–]\d+)?[^)]{0,20})\)", text)
    if m:
        return m.group(1).strip()
    return ""

def build_share_card(title: str, story_md: str, refs) -> dict:
    clean_refs = [_clean_ref(r) for r in (refs or []) if _clean_ref(r)]
    kjv_ref = clean_refs[0] if clean_refs else ""
    story_text = _extract_plain_text(story_md)

    client = _openai_client()
    if client is None:
        base = "I’m choosing to seek God early and trust Him in the middle of the noise.\nEven small obedience matters."
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
        base = "I’m choosing to seek God early and trust Him in the middle of the noise.\nEven small obedience matters."
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
            "Angel Q&A is ready — but your OpenAI key isn’t connected in this Space yet.\n\n"
            "Add a Hugging Face Secret named OPENAI_API_KEY, then restart the Space."
        )

    story_text = _extract_plain_text(story_md, max_chars=1400)

    system = (
        "You are Beyond the Message — Story Q&A.\n"
        "Tone: calm, confident, plainspoken. Not cheesy.\n"
        "Audience: families (kids + parents). Keep it safe.\n"
        "Use KJV references (reference-only). Do not invent verses.\n"
        "Do NOT quote long scripture passages. Keep any quote very short.\n"
        "Answer format:\n"
        "1) 2–5 sentence answer.\n"
        "2) 1–2 KJV references (reference-only).\n"
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
    return (s or "").replace("—", "-").replace("–", "-").replace("−", "-")

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

    want = {"6–10": "6-9", "9–13": "10-13", "Adult": "adult"}.get(age_label, "adult")
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

        # ARC 1 — Bridge
        if base.startswith("bridge-") or "bridge-" in base:
            return "ARC 1 Bridge"
        if base.startswith("ahab-") or "ahab-" in base:
            return "King Ahab"
        if base.startswith("elijah-") or "elijah-" in base:
            return "Elijah"
        if base.startswith("jezebel-") or "jezebel-" in base:
            return "Jezebel"

        # ARC 2 — The Promised King (Jesus)
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
        t = t.replace("–", "-")
        if t in ("6-10", "6-9", "6-8", "6–10", "6–9"):
            return "6-9"
        if t in ("9-13", "10-13", "9–13", "10–13"):
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
        # ARC 1 — Kings / Prophets
        "King Saul",
        "King David",
        "King Ahab",
        "Elijah",
        "Jezebel",
        "King Josiah",

        # ARC 2 — The Promised King
        "ARC 1 Bridge",

        # ARC 2 — The Promised King
        "The Promised King",

        # Other
        "Prayer on the Steps",
        "Other Bible Stories",
    ]
    arcs = [a for a in arc_order if (a in arc_map) or (a in ["ARC 1 Bridge", "The Promised King"])]
    arcs += [a for a in sorted(arc_map.keys()) if a not in arcs]
    arcs = sorted(arcs, key=lambda a: (arc_order.index(a) if a in arc_order else 999, a))

    # ✅ Always show the arc selector (even if only one arc) so it never “disappears”
    arc_pick = st.selectbox(
        "Choose an arc",
        options=arcs,
        index=0,
        key=f"arc_{prefix_key}",
    )

    # Age selector (key includes arc so switching arc doesn’t cross-wire)
    age_label = st.radio(
        "Age range",
        ["6–10", "9–13", "Adult"],
        horizontal=True,
        key=f"age_{prefix_key}_{arc_pick}",
    )

    want = {"6–10": "6-9", "9–13": "10-13", "Adult": "adult"}[age_label]

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
        # Adult fallback: if a story has only 6–10 and 9–13 versions, let Adult default to 9–13
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
                st.info("Adult version isn’t available for every story yet — showing the 9–13 version for now.")
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
    # Ask a Question (INLINE — no reroute)
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
            placeholder="Type your question here…",
        )
        cA, cB = st.columns([1, 1])
        with cA:
            ask_inline = st.form_submit_button("Ask About This Story", use_container_width=True)
        with cB:
            send_to_angel = st.form_submit_button("Send to Angel Chat", use_container_width=True)

    if ask_inline:
        q = (user_q or "").strip()
        if q:
            with st.spinner("Answering…"):
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
        base = f"My question is about the story titled '{title}'.\n\nHere’s my question:\n"
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
    # Journal (mailto + download fallback) — PRIVACY SAFE
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

    # ✅ Privacy-safe: do NOT set recipient. User chooses who to send to.
    subject = f"Journal Notes — {picked.get('title','Story')}"
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
            with st.spinner("Generating…"):
                card = build_share_card(picked.get("title", "Story"), story_md, refs)
            st.session_state[share_key] = card

    with cB:
        if st.button("Regenerate", use_container_width=True, key=f"regen_{share_key}", type="secondary"):
            with st.spinner("Regenerating…"):
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
                "Download Share Image (PNG) — optional",
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
        # Busy/lock timestamps (prevents WebView double-fire + stuck states)
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

    def reset_chat():
        st.session_state.chat = []
        st.session_state.mode = None
        st.session_state.last_user_text = ""
        st.session_state.busy = False
        st.session_state.angel_share = {"caption": "", "hashtags": "", "kjv_ref": ""}
        st.session_state.angel_prefill = ""
        st.session_state.angel_message_input = ""
        st.session_state.last_voice_hash = ""
        _save_angel_state()

    def mode_label(mode_key: str) -> str:
        return {
            "prayer": "Prayer",
            "scripture": "Scripture",
            "encouragement": "Encouragement",
            "living": "Living It Out",
        }.get(mode_key, "Angel Chat")

    def build_system_prompt_for_mode(mode_key: str) -> str:
        base = (
            "You are Angel Chat for Beyond the Message, a Christ-centered assistant.\n"
            "Tone: warm, grounded, plainspoken, not cheesy.\n"
            "Primary goal: help the user reflect, pray, and take a practical next step.\n"
            "User prefers KJV; use KJV references.\n"
            "When giving a plan (especially weekly), include:\n"
            "- One KJV anchor reference near the top\n"
            "- AND at least one KJV reference per day (Day 1…Day 7).\n"
            "Do NOT invent verses. Do not output long verbatim scripture passages; keep any quotes short.\n"
            "Always ask 1 gentle follow-up question at the end.\n"
        )

        if mode_key == "prayer":
            return base + (
                "\nMODE: PRAYER\n"
                "1) Acknowledge what they shared.\n"
                "2) Offer a short prayer (3–6 lines).\n"
                "3) Add 1 KJV reference that fits.\n"
                "4) End with ONE follow-up question.\n"
            )

        if mode_key == "scripture":
            return base + (
                "\nMODE: SCRIPTURE\n"
                "1) If their topic is unclear, ask what they need (fear, anxiety, guidance, forgiveness, etc.).\n"
                "2) Provide 2–3 KJV references + a short explanation of each.\n"
                "3) Suggest a simple reading plan for today (3 steps max).\n"
                "4) End with ONE follow-up question.\n"
            )

        if mode_key == "encouragement":
            return base + (
                "\nMODE: ENCOURAGEMENT\n"
                "1) Encourage without minimizing.\n"
                "2) Give one 'truth + action' pair.\n"
                "3) Include 1 KJV reference.\n"
                "4) End with ONE follow-up question.\n"
            )

        return base + (
            "\nMODE: LIVING IT OUT\n"
            "1) Identify the situation and the 'next right step'.\n"
            "2) Provide: (a) one practical step for today, (b) one short prayer, (c) one KJV reference.\n"
            "3) End with ONE follow-up question.\n"
        )

    def safe_model_response(system_prompt: str, user_text: str) -> str:
        if client is None:
            return (
                "Angel Chat is ready — but your OpenAI key isn’t connected in this Space yet.\n\n"
                "Add a Hugging Face Secret named OPENAI_API_KEY, then restart the Space."
            )

        messages = [{"role": "system", "content": system_prompt}]
        history = st.session_state.chat[-12:] if len(st.session_state.chat) > 12 else st.session_state.chat
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_text})

        if not _lock_try("openai_lock", timeout_s=45):
            return "⏳ Still working on your last request… give it a moment, then try again."

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
                return "⏳ Still working on your last request… give it a moment, then try again."
            if "401" in msg or "invalid_api_key" in msg.lower():
                return "⚠️ OpenAI authentication error. Please re-check your OPENAI_API_KEY secret and restart the Space."
            return (
                "I hit an error generating a response.\n\n"
                f"Details: {msg}"
            )
        finally:
            _lock_release("openai_lock")

    def set_mode(mode_key: str):
        st.session_state.mode = mode_key
        if not st.session_state.chat:
            st.session_state.chat.append({
                "role": "assistant",
                "content": "What’s on your heart today? Type below — or use a Quick Start to begin."
            })
        _save_angel_state()

    def run_quick_start(prompt_text: str):
        now = time.time()
        # Auto-release if stuck
        if st.session_state.busy and st.session_state.get("busy_since", 0.0) and (now - st.session_state.get("busy_since", 0.0)) > 45:
            st.session_state.busy = False
            st.session_state.busy_since = 0.0
        if st.session_state.busy:
            st.info("⏳ Still working on your last request… give it a moment, then try again.")
            return
        st.session_state.busy = True
        st.session_state.busy_since = now

        if not st.session_state.mode:
            st.session_state.mode = "living"

        st.session_state.chat.append({"role": "user", "content": prompt_text})
        _save_angel_state()

        try:
            with st.spinner("Angel Chat is writing…"):
                reply = safe_model_response(build_system_prompt_for_mode(st.session_state.mode), prompt_text)
        finally:
            st.session_state.busy = False
            st.session_state.busy_since = 0.0

        st.session_state.chat.append({"role": "assistant", "content": reply})
        _save_angel_state()
        st.rerun()

    def _latest_angel_answer() -> str:
        for m in reversed(st.session_state.chat):
            if m.get("role") == "assistant":
                txt = (m.get("content") or "").strip()
                if txt:
                    return txt
        return ""

    st.markdown('<div class="btm-page-title">Angel Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="btm-sub">A simple space to pause, pray, and reflect with God.</div>', unsafe_allow_html=True)

    # =========================
    # PRIVACY REASSURANCE (TRUST FIRST)
    # =========================
    if not st.session_state.get("privacy_ack", False):
        st.markdown(
            f"""
            <div class="btm-privacy">
              <div class="title">A quick privacy note</div>
              <p class="line"><span class="strong">Your conversation stays here.</span> Angel Chat doesn’t save, remember, or track what you share.</p>
              <ul class="bullets">
                <li>We don’t store conversations</li>
                <li>We don’t build profiles</li>
                <li>We don’t sell or share data</li>
              </ul>
              <div class="btm-privacy-mini">
                If we ever offer features that remember or follow your journey, they’ll be optional and clearly labeled — never assumed.
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        c_ok, c_more = st.columns([1, 1])
        with c_ok:
            if st.button("Got it", use_container_width=True, key="privacy_ack_btn", type="primary"):
                st.session_state.privacy_ack = True
                _save_angel_state()
                st.rerun()
        with c_more:
            st.caption("This is designed as a safe space — not a profile.")
        st.markdown('<div class="btm-hr"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.caption("Choose a mode, then share what’s on your heart.")
    with c2:
        if st.button("New Chat", use_container_width=True, disabled=st.session_state.busy, key="angel_new_chat", type="secondary"):
            reset_chat()
            st.rerun()

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Prayer", use_container_width=True, disabled=st.session_state.busy, key="mode_prayer", type="secondary"):
            set_mode("prayer")
    with b2:
        if st.button("Scripture", use_container_width=True, disabled=st.session_state.busy, key="mode_scripture", type="secondary"):
            set_mode("scripture")
    with b3:
        if st.button("Encouragement", use_container_width=True, disabled=st.session_state.busy, key="mode_encouragement", type="secondary"):
            set_mode("encouragement")
    with b4:
        if st.button("Living It Out", use_container_width=True, disabled=st.session_state.busy, key="mode_living", type="secondary"):
            set_mode("living")

    st.markdown(f"**Mode:** {mode_label(st.session_state.mode) if st.session_state.mode else '(choose one above)'}")

    if st.session_state.angel_prefill:
        st.info("Story context loaded. You can edit it before sending.")
        
    if st.session_state.mode:
        st.caption("Quick Start")
        q1, q2, q3 = st.columns(3)

        if st.session_state.mode == "prayer":
            with q1:
                if st.button("Pray for peace", use_container_width=True, disabled=st.session_state.busy, key="qs_pray_peace", type="secondary"):
                    run_quick_start("Please pray with me for peace and calm in my mind and heart.")
            with q2:
                if st.button("Pray for direction", use_container_width=True, disabled=st.session_state.busy, key="qs_pray_direction", type="secondary"):
                    run_quick_start("Please pray for God’s direction and wisdom for a decision I’m facing.")
            with q3:
                if st.button("Pray for family", use_container_width=True, disabled=st.session_state.busy, key="qs_pray_family", type="secondary"):
                    run_quick_start("Please pray for my family — that we would be drawn closer to Jesus and have unity.")

        elif st.session_state.mode == "scripture":
            with q1:
                if st.button("Anxiety & fear", use_container_width=True, disabled=st.session_state.busy, key="qs_scripture_anxiety", type="secondary"):
                    run_quick_start("Give me 3 KJV scriptures for anxiety and fear, and explain how to apply them today.")
            with q2:
                if st.button("Guidance", use_container_width=True, disabled=st.session_state.busy, key="qs_scripture_guidance", type="secondary"):
                    run_quick_start("Give me 3 KJV scriptures for guidance and making wise decisions, with a simple plan for today.")
            with q3:
                if st.button("Forgiveness", use_container_width=True, disabled=st.session_state.busy, key="qs_scripture_forgiveness", type="secondary"):
                    run_quick_start("Give me 3 KJV scriptures on forgiveness, and help me take one step today.")

        elif st.session_state.mode == "encouragement":
            with q1:
                if st.button("I feel worn out", use_container_width=True, disabled=st.session_state.busy, key="qs_enc_worn", type="secondary"):
                    run_quick_start("I feel worn out and discouraged. Encourage me biblically and give me one action step for today.")
            with q2:
                if st.button("I feel behind", use_container_width=True, disabled=st.session_state.busy, key="qs_enc_behind", type="secondary"):
                    run_quick_start("I feel behind in life. Encourage me with KJV scripture and a practical next step.")
            with q3:
                if st.button("I need hope", use_container_width=True, disabled=st.session_state.busy, key="qs_enc_hope", type="secondary"):
                    run_quick_start("I need hope right now. Encourage me and give me a short prayer and one KJV reference.")

        else:
            with q1:
                if st.button("Next right step", use_container_width=True, disabled=st.session_state.busy, key="qs_living_next", type="secondary"):
                    run_quick_start("Help me identify the next right step of obedience for today, with a short prayer and KJV reference.")
            with q2:
                if st.button("Hard conversation", use_container_width=True, disabled=st.session_state.busy, key="qs_living_hard", type="secondary"):
                    run_quick_start("I need to have a hard conversation. Help me respond with wisdom, humility, and courage (KJV).")
            with q3:
                if st.button("Build a habit", use_container_width=True, disabled=st.session_state.busy, key="qs_living_habit", type="secondary"):
                    run_quick_start("Help me build a daily habit of prayer and scripture. Give me a simple plan for today (KJV).")

    st.markdown('<div class="btm-hr"></div>', unsafe_allow_html=True)

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    def _send_user_message(text: str):
        text = (text or "").strip()
        if not text or st.session_state.busy:
            return

        st.session_state.busy = True

        if not st.session_state.mode:
            st.session_state.mode = "living"
            if not st.session_state.chat:
                st.session_state.chat.append({
                    "role": "assistant",
                    "content": "I’ll start you in Living It Out — you can switch modes anytime above."
                })

        if st.session_state.angel_prefill:
            st.session_state.angel_prefill = ""

        st.session_state.last_user_text = text
        st.session_state.chat.append({"role": "user", "content": text})
        _save_angel_state()

        try:
            with st.spinner("Angel Chat is writing…"):
                system_prompt = build_system_prompt_for_mode(st.session_state.mode)
                reply = safe_model_response(system_prompt, text)
        finally:
            st.session_state.busy = False

        st.session_state.chat.append({"role": "assistant", "content": reply})
        _save_angel_state()
        st.rerun()

    st.markdown('<div class="btm-card">', unsafe_allow_html=True)
    st.markdown("<div class='btm-sec-title'>Send a Message</div>", unsafe_allow_html=True)

    with st.form("angel_composer_form", clear_on_submit=True):
        # NOTE: We intentionally use a single-line input here so mobile users can simply hit Enter.
        # The default Streamlit “Press Enter…” hint can overlap on small screens, so we hide it via CSS.
        default_msg = (st.session_state.get("angel_prefill") or "").strip()
        msg = st.text_input(
            "Message",
            value=default_msg,
            label_visibility="collapsed",
            placeholder="Type what’s on your heart…",
            disabled=st.session_state.busy,
        )

        # Keep guidance *below* the field (not inside it) so it never collides with typed text.
        st.markdown(
            '<div class="btm-small" style="margin-top:-6px;">Tip: Tap <b>Send</b> (or press Enter) when you’re ready.</div>',
            unsafe_allow_html=True
        )

        # Keep privacy reassurance compact here to avoid pushing the chat off-screen on mobile.
        st.markdown(
            '<div class="btm-small" style="margin-top:8px;">🔒 <b>Your conversation stays here.</b> Not saved. Not tracked.</div>',
            unsafe_allow_html=True
        )

        sent = st.form_submit_button("Send", use_container_width=True, disabled=st.session_state.busy)
        if sent:
            _send_user_message(msg)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="btm-hr"></div>', unsafe_allow_html=True)
    st.markdown("### Share Card")
    st.markdown("<div class='btm-small'>Tap Create — then screenshot the card.</div>", unsafe_allow_html=True)

    latest = _latest_angel_answer()

    cA, cB = st.columns([1, 1])
    with cA:
        if st.button("Create Share Card", use_container_width=True, disabled=st.session_state.busy or (not latest), key="angel_make_share", type="primary"):
            with st.spinner("Creating…"):
                st.session_state.angel_share = build_angel_share_card_from_text(latest)
            _save_angel_state()
    with cB:
        if st.button("Regenerate", use_container_width=True, disabled=st.session_state.busy or (not latest), key="angel_regen_share", type="secondary"):
            with st.spinner("Regenerating…"):
                st.session_state.angel_share = build_angel_share_card_from_text(latest)
            _save_angel_state()

    a = st.session_state.angel_share
    a_caption = (a.get("caption") or "").strip()
    a_tags = (a.get("hashtags") or "").strip()
    a_ref = (a.get("kjv_ref") or "").strip()

    if a_caption:
        render_share_card_preview(a_caption, kjv_ref=a_ref, footer=PROD_FOOTER)
        if a_tags:
            st.caption(a_tags)

        png_bytes = build_share_image_png(
            title="Share This Encouragement",
            caption=a_caption,
            kjv_ref=(a_ref if a_ref else ""),
            hashtags=a_tags
        )
        if png_bytes:
            st.download_button(
                "Download Share Image (PNG) — optional",
                data=png_bytes,
                file_name="angel.share.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.caption("PNG export needs a system font (DejaVu/Liberation). Screenshot the card above instead.")

    st.markdown('<div class="btm-hr"></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    with left:
        st.caption("Please verify with Scripture (KJV).")
    with right:
        st.caption("Key detected" if OPENAI_API_KEY else "Add Secret: OPENAI_API_KEY")

    st.caption("© 2025 Beyond the Message — Angel Chat")

# =========================
# HOME
# =========================
def render_home():
    st.markdown('<div class="btm-wrap">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="btm-hero">
          <h1>Beyond the <span>Message</span></h1>
          <p>A trusted place for families to learn, pray, and grow.</p>
          <p class="btm-note">Study Hub for guided lessons. Angel Chat for real-time prayer, questions, and deeper guidance.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Angel Chat", use_container_width=True, key="home_btn_angel", type="primary"):
            goto("angel")
    with c2:
        if st.button("Bible Stories", use_container_width=True, key="home_btn_bible", type="secondary"):
            goto("bible")
    with c3:
        render_external_pill("Study Hub", "https://beyondthemessage.org/study-hub/", variant="secondary")

    st.caption("Tip: Use Study Hub for guided lessons and Angel Chat for real-time prayer, questions, and deeper guidance.")
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
        # ✅ Include jezebel so root files like jezebel-01-*.meta.json load automatically
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