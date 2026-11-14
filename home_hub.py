"""Home and navigation markup for the Angel Chat resource hub."""

from html import escape
from urllib.parse import quote, urlsplit


DEFAULT_BELIEF_FILES_URL = "https://beyondthemessage.org/the-belief-files/"
COUNSEL_URL = "https://king-s-counsel-leadership-app.vercel.app/"
STUDY_URL = "https://beyondthemessage.org/study-hub/"


def belief_files_url(configured=""):
    """Use the published resource unless a valid HTTPS override is supplied."""
    value = str(configured or "").strip()
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
            return value
    except ValueError:
        pass
    return DEFAULT_BELIEF_FILES_URL


def icon(name):
    paths = {
        "angel": '<path d="M4 4h16v12H9l-5 4V4Z"/><path d="M8 8h8M8 12h5"/>',
        "counsel": '<path d="m3 7 4 3 5-6 5 6 4-3-2 12H5L3 7Z"/><path d="M7 15h10"/>',
        "bible": '<path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1Z"/><path d="M12 5v15M6 8h2M16 8h2M6 12h2M16 12h2"/>',
        "study": '<path d="m12 3 10 5-10 5L2 8l10-5Z"/><path d="m5 10 7 4 7-4v7l-7 4-7-4v-7ZM22 8v7"/>',
        "belief": '<path d="M3 7h7l2 2h9v11H3V7Z"/><path d="M3 7V4h7l2 3M7 13h10M7 16h7"/>',
        "arrow": '<path d="M5 12h14m-5-5 5 5-5 5"/>',
        "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
    }
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' + paths[name] + '</svg>'
    uri = 'data:image/svg+xml,' + quote(svg, safe='')
    return f'<span class="hub-icon" style="-webkit-mask-image:url({uri});mask-image:url({uri});" aria-hidden="true"></span>'


HOME_CSS = """<style>
.block-container:has(#angel-home-hub){padding-top:1.15rem;padding-bottom:110px;}
.hub-icon{display:block;width:22px;height:22px;flex-shrink:0;background:currentColor;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:contain;mask-size:contain;-webkit-mask-position:center;mask-position:center;}
#angel-home-hub{--hub-ink:#17283b;--hub-gold:#8b693d;--hub-line:#dedbd3;--hub-muted:#5c636b;max-width:780px;margin:0 auto 20px;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--hub-ink);text-align:left;}
#angel-home-hub *{box-sizing:border-box;}
#angel-home-hub a{color:inherit;text-decoration:none;}
#angel-home-hub a:focus-visible{outline:3px solid #a18050;outline-offset:5px;border-radius:9px;}
#angel-home-hub .hub-icon{display:block;width:22px;height:22px;flex-shrink:0;}
#angel-home-hub .hub-brandbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 0 25px;border-bottom:1px solid var(--hub-line);}
#angel-home-hub .hub-brand{display:flex;align-items:center;gap:10px;}
#angel-home-hub .hub-mark{display:grid;place-items:center;width:34px;height:38px;border:1px solid #b39b77;border-radius:14px 14px 6px 6px;color:var(--hub-gold);}
#angel-home-hub .hub-brand-name{display:block;font-size:15px;line-height:1.3;letter-spacing:-.02em;font-weight:650;}
#angel-home-hub .hub-brand-note{display:block;font-size:8px;font-weight:600;line-height:1.8;text-transform:uppercase;letter-spacing:.16em;color:var(--hub-muted);}
#angel-home-hub a.hub-help{font-size:11px;color:var(--hub-muted);text-decoration:underline;text-underline-offset:4px;white-space:nowrap;}
#angel-home-hub .hub-hero{padding:32px 0 25px;}
#angel-home-hub .hub-eyebrow{margin:0 0 12px;color:var(--hub-gold);font-size:9px;font-weight:650;letter-spacing:.16em;line-height:1.6;text-transform:uppercase;}
#angel-home-hub h1{font-family:"Cormorant Garamond",Georgia,serif;font-size:clamp(39px,6vw,59px);font-weight:500;color:var(--hub-ink);line-height:1.03;letter-spacing:-.035em;margin:0 0 14px;padding:0;text-wrap:balance;}
#angel-home-hub h1 em{color:var(--hub-gold);font-weight:500;}
#angel-home-hub .hub-hero-copy{font-size:13px;line-height:1.75;color:var(--hub-muted);max-width:450px;margin:0 0 20px;}
#angel-home-hub a.hub-primary{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:53px;padding:14px 19px;border:1px solid var(--hub-ink);border-radius:10px;background:var(--hub-ink);color:#faf8f3;font-size:14px;font-weight:600;transition:background .15s ease;}
#angel-home-hub a.hub-primary:hover{background:#253c52;}
#angel-home-hub a.hub-daily{display:grid;grid-template-columns:34px minmax(0,1fr) 18px;align-items:center;gap:13px;background:#fffefa;border:1px solid var(--hub-line);border-radius:12px;padding:17px;margin:0 0 26px;}
#angel-home-hub .hub-daily-icon{color:var(--hub-gold);}
#angel-home-hub .hub-daily-label{display:block;color:var(--hub-gold);font-size:8px;font-weight:650;text-transform:uppercase;letter-spacing:.14em;line-height:1.5;margin:0 0 4px;}
#angel-home-hub .hub-daily-title{display:block;color:var(--hub-ink);font-size:14px;font-weight:600;line-height:1.4;}
#angel-home-hub .hub-daily-note{display:block;color:var(--hub-muted);font-size:12px;line-height:1.5;margin-top:4px;}
#angel-home-hub .hub-section-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 0 12px;}
#angel-home-hub .hub-section-head h2{font-family:"Cormorant Garamond",Georgia,serif;font-size:26px;font-weight:500;color:var(--hub-ink);line-height:1.2;margin:0;padding:0;letter-spacing:-.025em;}
#angel-home-hub .hub-section-head > span{font-size:8px;color:var(--hub-muted);letter-spacing:.12em;white-space:nowrap;text-transform:uppercase;}
#angel-home-hub .hub-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;}
#angel-home-hub a.hub-resource{display:flex;flex-direction:column;align-items:flex-start;gap:0;min-width:0;min-height:164px;padding:20px;background:#fffefa;border:1px solid var(--hub-line);border-radius:12px;transition:border-color .15s ease,background .15s ease;}
#angel-home-hub a.hub-resource:hover{border-color:#a18050;background:#f4f0e7;}
#angel-home-hub .hub-card-top{display:flex;align-items:center;justify-content:space-between;width:100%;color:var(--hub-gold);margin:0 0 15px;}
#angel-home-hub .hub-card-top .hub-tag{font-size:8px;letter-spacing:.12em;text-transform:uppercase;font-weight:650;}
#angel-home-hub .hub-resource h3{font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;font-weight:650;color:var(--hub-ink);line-height:1.4;margin:0 0 6px;padding:0;letter-spacing:-.025em;}
#angel-home-hub .hub-resource p{font-size:11px;font-weight:400;line-height:1.65;color:var(--hub-muted);margin:0 0 14px;padding:0;}
#angel-home-hub .hub-card-link{display:flex;align-items:center;justify-content:space-between;gap:8px;width:100%;margin-top:auto;padding-top:12px;border-top:1px solid var(--hub-line);font-size:11px;font-weight:600;color:var(--hub-ink);}
#angel-home-hub .hub-card-link .hub-icon{width:15px;height:15px;}
#angel-home-hub a.hub-resource.hub-featured{background:var(--hub-ink);border-color:var(--hub-ink);}
#angel-home-hub a.hub-resource.hub-featured:hover{background:#253c52;}
#angel-home-hub .hub-featured h3,#angel-home-hub .hub-featured .hub-card-link{color:#faf8f3;}
#angel-home-hub .hub-featured p{color:#cbd5de;}
#angel-home-hub .hub-featured .hub-card-top{color:#d6b884;}
#angel-home-hub .hub-featured .hub-card-link{border-color:#405064;}
#angel-home-hub .hub-signup{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:19px 0 6px;}
#angel-home-hub .hub-signup p{margin:0;font-size:11px;line-height:1.6;color:var(--hub-muted);}
#angel-home-hub .hub-signup a{font-size:11px;font-weight:600;color:var(--hub-ink);text-decoration:underline;text-underline-offset:4px;white-space:nowrap;}
#angel-home-hub .hub-footnote{margin:24px 0 0;padding-top:17px;border-top:1px solid var(--hub-line);color:var(--hub-muted);font-size:9px;text-align:center;line-height:1.7;}
@media(min-width:680px){#angel-home-hub .hub-hero{padding-top:38px;}#angel-home-hub a.hub-primary{max-width:330px;}#angel-home-hub .hub-grid{gap:15px;}#angel-home-hub a.hub-resource{padding:24px;}}
@media(max-width:420px){#angel-home-hub .hub-brandbar{padding-bottom:19px;}#angel-home-hub .hub-hero{padding-top:25px;}#angel-home-hub a.hub-resource{padding:16px;min-height:176px;}#angel-home-hub .hub-section-head h2{font-size:24px;}#angel-home-hub .hub-resource h3{font-size:13px;}#angel-home-hub .hub-resource p{font-size:12px;}#angel-home-hub .hub-signup{align-items:flex-start;}}
@media(prefers-reduced-motion:reduce){#angel-home-hub a{transition:none;}}
</style>"""

NAV_CSS = """<style>
.hub-icon{display:block;width:22px;height:22px;flex-shrink:0;background:currentColor;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:contain;mask-size:contain;-webkit-mask-position:center;mask-position:center;}
.btm-bottom-nav{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:2px;padding:8px max(6px,calc((100vw - 800px)/2)) calc(8px + env(safe-area-inset-bottom));background:rgba(250,248,243,.97);border-top:1px solid #dedbd3;box-shadow:0 -4px 20px rgba(23,40,59,.04);backdrop-filter:blur(16px);}
.btm-bottom-nav .btm-nav-item{display:flex;flex-direction:column;gap:5px;justify-content:center;align-items:center;min-width:0;height:58px;padding:4px 2px;border:0;border-radius:8px;background:transparent;color:#58616a!important;box-shadow:none;transition:background .15s ease;}
.btm-bottom-nav .btm-nav-item:hover{background:#eee9df;transform:none;}
.btm-bottom-nav .btm-nav-item .hub-icon{display:block;width:21px;height:21px;color:#7e858b;}
.btm-bottom-nav .btm-nav-label{font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:10px;font-weight:600;letter-spacing:0;line-height:1.25;white-space:normal;text-align:center;}
.btm-bottom-nav .btm-nav-item.active{background:#ede8dd;border:0;color:#17283b!important;box-shadow:none;}
.btm-bottom-nav .btm-nav-item.active .hub-icon{color:#8b693d;}
.btm-bottom-nav .btm-nav-item:focus-visible{outline:3px solid #a18050;outline-offset:0;}
@media(min-width:520px){.btm-bottom-nav .btm-nav-label{font-size:10px;}}
@media(prefers-reduced-motion:reduce){.btm-bottom-nav .btm-nav-item{transition:none;}}
</style>"""


def bottom_nav_html(active, href):
    items = (
        ("angel", "Angel Chat", href("angel"), False),
        ("counsel", "King’s Counsel", COUNSEL_URL, True),
        ("bible", "Bible Stories", href("bible"), False),
        ("study", "Study Hub", STUDY_URL, True),
        ("belief", "Belief Files", href("belief"), False),
    )
    links = []
    for key, label, url, external in items:
        selected = ' active' if key == active else ''
        current = ' aria-current="page"' if key == active else ''
        target = ' target="_blank" rel="noopener noreferrer"' if external else ' target="_self"'
        extra = ' (opens in a new tab)' if external else ''
        links.append(f'<a class="btm-nav-item{selected}" href="{escape(url, quote=True)}" aria-label="{escape(label + extra)}"{current}{target}>{icon(key)}<span class="btm-nav-label">{label}</span></a>')
    return '<nav class="btm-bottom-nav" aria-label="Main navigation">' + ''.join(links) + '</nav>'


def utility_bar_html(href):
    home = escape(href('home'), quote=True)
    about = escape(href('about'), quote=True)
    return f'''<style>#angel-hub-utility{{display:flex;justify-content:space-between;align-items:center;gap:15px;max-width:780px;margin:0 auto 24px;padding:0 0 14px;border-bottom:1px solid #dedbd3;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:12px;}}#angel-hub-utility a{{color:#455567;text-decoration:none;}}#angel-hub-utility a:hover{{text-decoration:underline;}}#angel-hub-utility a:focus-visible{{outline:3px solid #a18050;outline-offset:4px;}}</style><nav id="angel-hub-utility" aria-label="Home and help"><a href="{home}" target="_self">← Home</a><a href="{about}" target="_self">How it works</a></nav>'''


def home_html(href, *, show_signup=False):
    def destination(view):
        return escape(href(view), quote=True)

    cards = (
        ("belief", "The Belief Files", "Explore religious claims through history, evidence, and Scripture.", "Explore the files", href("belief"), False, True),
        ("counsel", "King’s Counsel", "Biblical wisdom for the way you lead and the decisions you make.", "Find counsel", COUNSEL_URL, True, False),
        ("bible", "Bible Stories", "Step into Scripture with stories and questions for every age.", "Read a story", href("bible"), False, False),
        ("study", "Study Hub", "Go deeper with guided lessons, study notes, and daily readings.", "Open Study Hub", STUDY_URL, True, False),
    )
    resources = []
    for key, title, copy, action, url, external, featured in cards:
        target = ' target="_blank" rel="noopener noreferrer"' if external else ' target="_self"'
        label = title + (' (opens in a new tab)' if external else '')
        tag = '<span class="hub-tag">Explore</span>' if featured else ''
        resources.append(f'<a class="hub-resource{" hub-featured" if featured else ""}" href="{escape(url, quote=True)}" aria-label="{escape(label)}"{target}><div class="hub-card-top">{icon(key)}{tag}</div><h3>{title}</h3><p>{copy}</p><span class="hub-card-link">{action}{icon("arrow")}</span></a>')
    signup = f'<div class="hub-signup"><p>A little encouragement in your inbox.</p><a href="{destination("email")}" target="_self">Sign up for daily emails</a></div>' if show_signup else ''
    return f'''<main id="angel-home-hub" aria-labelledby="hub-title">
<div class="hub-brandbar"><a class="hub-brand" href="{destination("home")}" target="_self" aria-label="Angel Chat home"><span class="hub-mark">{icon("angel")}</span><span><span class="hub-brand-name">Angel Chat</span><span class="hub-brand-note">Beyond the Message</span></span></a><a class="hub-help" href="{destination("about")}" target="_self">How it works</a></div>
<section class="hub-hero" aria-labelledby="hub-title"><p class="hub-eyebrow">A quiet place in Scripture</p><h1 id="hub-title">Bring what’s<br>on your <em>heart.</em></h1><p class="hub-hero-copy">Make room for prayer, explore God’s Word, and take your next faithful step.</p><a class="hub-primary" href="{destination("angel")}" target="_self">Enter Angel Chat {icon("arrow")}</a></section>
<a class="hub-daily" href="{destination("daily")}" target="_self" aria-label="Read Daily Encouragement"><span class="hub-daily-icon">{icon("sun")}</span><span><span class="hub-daily-label">A word for today</span><span class="hub-daily-title">Daily Encouragement</span><span class="hub-daily-note">Scripture, reflection, and a moment to pray.</span></span>{icon("arrow")}</a>
<section aria-labelledby="hub-resources-title"><div class="hub-section-head"><h2 id="hub-resources-title">Go a little deeper.</h2><span>Faith for everyday life</span></div><div class="hub-grid">{''.join(resources)}</div></section>
{signup}<p class="hub-footnote">Rooted in Scripture. Centered on Jesus Christ.</p></main>'''
