"""Shared devotional presentation with escaped message fields.

Email layout uses tables and inline styles; the complete teaching remains text
when the shared, non-personalized brand image is blocked by an email client.
"""

from datetime import date
import html
import re


NAVY = "#1A1B26"
GOLD = "#A68966"
PAPER = "#F9F7F2"
BRAND_MARK_URL = "https://huggingface.co/spaces/lvRJay18950/Prayer-Angel/resolve/main/icon-192.png"
BODY_STYLE = f"font-family:Georgia,'Times New Roman',serif;font-size:18px;line-height:1.8;color:{NAVY};margin:0 0 20px;"
LABEL_STYLE = f"font-family:Arial,sans-serif;font-size:12px;font-weight:bold;letter-spacing:1.6px;line-height:1.6;color:#756047;margin:0 0 12px"


def brand_header_html():
    return (
        f'<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="{NAVY}" '
        f'style="width:100%;border:0;border-collapse:collapse;background:{NAVY};border-radius:14px 14px 0 0">'
        '<tr><td width="92" style="border:0;padding:24px 0 24px 20px;vertical-align:middle">'
        f'<img src="{BRAND_MARK_URL}" width="72" height="72" alt="Beyond the Message" '
        'style="display:block;width:72px;height:72px;border:0;border-radius:8px"></td>'
        '<td style="border:0;padding:24px 20px 24px 16px;vertical-align:middle">'
        '<p style="font-family:Arial,sans-serif;font-size:10px;letter-spacing:1.8px;color:#D5BB93;margin:0 0 6px">BEYOND THE MESSAGE</p>'
        '<p style="font-family:Georgia,serif;font-size:29px;line-height:1.15;font-weight:bold;color:#F9F7F2;margin:0 0 8px">Daily Encouragement</p>'
        '<p style="font-family:Arial,sans-serif;font-size:12px;line-height:1.5;color:#DED8CE;margin:0">Scripture &middot; Reflection &middot; Prayer</p>'
        f'</td></tr><tr><td colspan="2" height="4" bgcolor="{GOLD}" style="height:4px;border:0;padding:0;background:{GOLD};font-size:0"></td></tr></table>'
    )


def _emphasis_parts(message, text):
    phrases = {phrase for phrase in message.get("emphasis", ()) if phrase and phrase in text}
    if not phrases:
        return [(text, False)]
    pattern = "(" + "|".join(re.escape(phrase) for phrase in sorted(phrases, key=len, reverse=True)) + ")"
    return [(part, part in phrases) for part in re.split(pattern, text) if part]


def devotional_markdown(message):
    text = message.get("devotional", message["encouragement"])
    return "".join(f"**{part}**" if emphasized else part for part, emphasized in _emphasis_parts(message, text))


def devotional_html(message):
    paragraphs = []
    for paragraph in message.get("devotional", message["encouragement"]).split("\n\n"):
        content = "".join(
            f'<strong style="font-weight:bold;color:{NAVY}">{html.escape(part)}</strong>' if emphasized else html.escape(part)
            for part, emphasized in _emphasis_parts(message, paragraph)
        )
        paragraphs.append(f'<p style="{BODY_STYLE}">{content}</p>')
    return "".join(paragraphs)


def scripture_anchor_html(message):
    return (
        f'<div style="padding:22px 24px;margin:22px 0;background:{PAPER};border-left:4px solid {GOLD};border-radius:0 10px 10px 0">'
        f'<p style="{LABEL_STYLE}">A WORD TO HOLD ON TO</p>'
        f'<p style="font-family:Georgia,serif;font-size:24px;line-height:1.5;color:{NAVY};margin:0 0 10px">&ldquo;{html.escape(message["verse"])}&rdquo;</p>'
        f'<p style="font-family:Arial,sans-serif;font-size:12px;color:#5C5A5E;margin:0">{html.escape(message["verse_reference"])} &middot; KJV</p></div>'
    )


def reflection_html(message):
    return (
        f'<div style="background:#F1EADF;border:1px solid #D8C9B4;border-radius:12px;padding:24px;margin:24px 0">'
        f'<h3 style="{LABEL_STYLE}">A QUESTION TO CARRY</h3>'
        f'<p style="font-family:Georgia,serif;font-size:21px;line-height:1.6;color:{NAVY};margin:0">{html.escape(message["reflection"])}</p></div>'
        f'<div style="padding:0 4px;margin:24px 0"><h3 style="{LABEL_STYLE}">A PRAYER</h3>'
        f'<p style="{BODY_STYLE}font-style:italic">{html.escape(message["prayer"])}</p></div>'
    )


def email_shell_html(content, footer_html=""):
    footer = (
        f'<tr><td style="border:0;border-top:1px solid #E3DCCF;padding:22px 26px;background:{PAPER};'
        f'font-family:Arial,sans-serif;font-size:12px;line-height:1.7;color:#5C5A5E">{footer_html}</td></tr>'
        if footer_html else ""
    )
    return (
        f'<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="width:100%;border:0;border-collapse:collapse;background:{PAPER}">'
        '<tr><td align="center" style="border:0;padding:12px 0">'
        '<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600" '
        f'style="width:100%;max-width:600px;border:1px solid #E3DCCF;border-collapse:separate;border-spacing:0;background:#FFFFFF;border-radius:14px">'
        f'<tr><td style="border:0;padding:0">{brand_header_html()}</td></tr>'
        f'<tr><td style="border:0;padding:28px 24px">{content}</td></tr>{footer}</table></td></tr></table>'
    )


def action_button_html(label, url, secondary=False):
    background, foreground = ("#FFFFFF", NAVY) if secondary else (NAVY, "#FFFFFF")
    return (
        '<p style="margin:14px 0">'
        f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-block;border:1px solid {GOLD};border-radius:7px;padding:13px 18px;'
        f'background:{background};color:{foreground};font-family:Arial,sans-serif;font-size:14px;'
        f'line-height:1.5;font-weight:bold;text-decoration:none">{html.escape(label)}</a></p>'
    )


def render_devotional_email_html(message, links, footer_html=""):
    day = date.fromisoformat(message["date"]).strftime("%A, %B %d, %Y")
    reading = "".join(
        f'<p style="font-family:Georgia,serif;font-size:17px;line-height:1.8;color:{NAVY};margin:0 0 16px">{html.escape(paragraph).replace(chr(10), "<br>")}</p>'
        for paragraph in message["reading"].split("\n\n")
    )
    buttons = "".join(action_button_html(label, url, index > 0) for index, (label, url) in enumerate(links))
    content = (
        f'<p style="{LABEL_STYLE}">{html.escape(day.upper())}</p>'
        f'<h1 style="font-family:Georgia,serif;font-size:34px;line-height:1.2;color:{NAVY};margin:0 0 16px">{html.escape(message["title"])}</h1>'
        f'<p style="font-family:Arial,sans-serif;font-size:16px;line-height:1.7;color:#5C5A5E;margin:0 0 20px">{html.escape(message["encouragement"])}</p>'
        f'{scripture_anchor_html(message)}'
        f'<h2 style="font-family:Georgia,serif;font-size:22px;color:{NAVY};margin:28px 0 8px">Today\'s reading</h2>'
        f'<p style="{LABEL_STYLE}">{html.escape(message["reference"])} &middot; KJV</p>{reading}'
        f'<div style="height:1px;background:#E3DCCF;margin:28px 0"></div>'
        f'<h2 style="font-family:Georgia,serif;font-size:24px;color:{NAVY};margin:0 0 20px">Today\'s reflection</h2>'
        f'{devotional_html(message)}{reflection_html(message)}'
        f'<div style="border-top:1px solid #E3DCCF;padding-top:22px;margin-top:26px">'
        f'<h2 style="font-family:Georgia,serif;font-size:23px;color:{NAVY};margin:0 0 10px">Go deeper with Angel Chat</h2>'
        '<p style="font-family:Arial,sans-serif;font-size:15px;line-height:1.7;color:#5C5A5E;margin:0 0 14px">Explore this message and ask questions in Angel Chat.</p>'
        f'{buttons}<p style="font-family:Arial,sans-serif;font-size:12px;line-height:1.7;color:#5C5A5E;margin:14px 0 0">Use the browser link on iPhone, iPad, or computer.</p></div>'
    )
    return email_shell_html(content, footer_html)
