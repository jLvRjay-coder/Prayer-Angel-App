"""The Belief Files library and a source-linked reader for approved case files."""

from html import escape
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from home_hub import belief_files_url


CASE_ID = "002"
CASE_TITLE = "The Book of Mormon Translation"
CASE_MARKDOWN = Path(__file__).with_name("belief_case_002.md")
CASE_PDF = Path(__file__).with_name("belief_case_002.pdf")

# Every substantive section of the approved manuscript belongs to one chapter.
# Publication metadata stays in the manuscript rather than in the reading flow.
CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The English manuscripts", "Exhibit two The instruments and the hat", "Exhibit three The lost 116 pages", "Exhibit four The disputed expert endorsement")),
    ("witnesses", "Witnesses", ("Exhibit five The plate witnesses", "Assessing the principal accounts")),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)


BELIEF_CSS = """<style>
.block-container:has(#belief-files){padding-top:1rem;padding-bottom:115px;}
#belief-files{--bf-ink:#17283b;--bf-muted:#555f68;--bf-gold:#846239;--bf-line:#dedbd3;--bf-paper:#fffdf8;max-width:780px;margin:0 auto 24px;color:var(--bf-ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;text-align:left;}
#belief-files *{box-sizing:border-box;}
#belief-files a{color:var(--bf-ink);text-underline-offset:3px;}
#belief-files a:focus-visible,#belief-files summary:focus-visible{outline:3px solid #a18050;outline-offset:4px;border-radius:6px;}
#belief-files .bf-back{display:inline-flex;align-items:center;min-height:44px;font-size:13px;text-decoration:none;margin-bottom:12px;}
#belief-files .bf-eyebrow{font-size:11px;font-weight:650;letter-spacing:.14em;text-transform:uppercase;color:var(--bf-gold);margin:0 0 12px;line-height:1.5;}
#belief-files h1{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:clamp(32px,5.5vw,48px);line-height:1.12;letter-spacing:-.03em;margin:0 0 16px;padding:0;color:var(--bf-ink);text-wrap:balance;}
#belief-files .bf-lead{font-size:16px;line-height:1.75;color:var(--bf-muted);margin:0 0 20px;max-width:650px;}
#belief-files .bf-meta{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--bf-muted);font-size:12px;line-height:1.6;margin:0 0 24px;}
#belief-files .bf-library-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:25px 0;}
#belief-files .bf-case{display:flex;flex-direction:column;align-items:flex-start;min-width:0;padding:25px;border:1px solid var(--bf-line);border-radius:14px;background:var(--bf-paper);text-decoration:none;}
#belief-files .bf-case h2{font-family:Georgia,"Times New Roman",serif;font-size:27px;line-height:1.2;letter-spacing:-.02em;font-weight:500;padding:0;margin:0 0 12px;color:inherit;}
#belief-files .bf-case p{font-size:14px;line-height:1.7;margin:0 0 23px;color:var(--bf-muted);}
#belief-files .bf-case .bf-case-link{display:block;margin-top:auto;min-height:36px;padding-top:12px;border-top:1px solid var(--bf-line);width:100%;font-size:13px;font-weight:650;}
#belief-files .bf-case.bf-featured{background:var(--bf-ink);border-color:var(--bf-ink);color:#fffdf8;}
#belief-files .bf-featured .bf-eyebrow{color:#e0c28f;}
#belief-files .bf-featured p{color:#d5dee5;}
#belief-files .bf-featured .bf-case-link{border-color:#47586a;}
#belief-files .bf-library-note{padding:20px 0;border-top:1px solid var(--bf-line);font-size:14px;line-height:1.75;color:var(--bf-muted);}
#belief-files .bf-library-note a{display:inline-flex;align-items:center;min-height:44px;}
#belief-files .bf-contents{border:1px solid var(--bf-line);border-radius:12px;background:var(--bf-paper);margin:0 0 25px;padding:0 17px;}
#belief-files .bf-contents summary{cursor:pointer;min-height:52px;padding:15px 0;font-size:14px;font-weight:650;line-height:1.6;}
#belief-files .bf-contents summary span{float:right;font-size:12px;font-weight:400;color:var(--bf-muted);margin-left:8px;}
#belief-files .bf-chapters{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;padding:0 0 16px;}
#belief-files .bf-chapters a{display:flex;gap:10px;align-items:center;min-height:47px;padding:10px 12px;border:1px solid var(--bf-line);border-radius:8px;font-size:13px;line-height:1.4;text-decoration:none;}
#belief-files .bf-chapters a span{font-size:11px;color:var(--bf-gold);}
#belief-files .bf-chapters a[aria-current=page]{background:#eee8dc;border-color:#b09a78;font-weight:650;}
#belief-files .bf-article{font-size:16px;line-height:1.8;overflow-wrap:anywhere;}
#belief-files .bf-article h2{font-family:Georgia,"Times New Roman",serif;font-size:28px;font-weight:500;line-height:1.25;letter-spacing:-.025em;padding:0;margin:32px 0 15px;color:var(--bf-ink);}
#belief-files .bf-article h2:first-child{margin-top:0;}
#belief-files .bf-article h3{font-size:18px;font-weight:650;line-height:1.4;padding:0;margin:26px 0 12px;color:var(--bf-ink);}
#belief-files .bf-article p{margin:0 0 18px;font-size:inherit;line-height:inherit;}
#belief-files .bf-article li{padding-left:3px;margin:0 0 11px;font-size:inherit;line-height:inherit;}
#belief-files .bf-article ul,#belief-files .bf-article ol{padding-left:24px;margin:0 0 20px;}
#belief-files .bf-article .bf-citation{font-size:.8em;white-space:nowrap;text-decoration:underline;color:var(--bf-gold);}
#belief-files .bf-table{border-collapse:collapse;table-layout:fixed;width:100%;margin:20px 0 25px;font-size:14px;line-height:1.6;}
#belief-files .bf-table th,#belief-files .bf-table td{border:1px solid var(--bf-line);padding:13px;vertical-align:top;text-align:left;overflow-wrap:anywhere;}
#belief-files .bf-table thead th{background:var(--bf-ink);color:#fffdf8;font-size:13px;font-weight:650;}
#belief-files .bf-table tbody th{font-weight:600;background:#f4f0e7;}
#belief-files .bf-source{padding:16px 0;border-bottom:1px solid var(--bf-line);scroll-margin-top:25px;}
#belief-files .bf-source:target{background:#f1eadb;border-radius:8px;outline:2px solid #b09a78;outline-offset:5px;}
#belief-files .bf-source p{font-size:14px;line-height:1.8;margin:0;}
#belief-files .bf-reader-nav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;border-top:1px solid var(--bf-line);margin-top:30px;padding-top:20px;}
#belief-files .bf-reader-nav a{display:flex;flex-direction:column;justify-content:center;min-height:65px;padding:12px 15px;border:1px solid var(--bf-line);border-radius:10px;background:var(--bf-paper);font-size:14px;font-weight:600;text-decoration:none;line-height:1.5;}
#belief-files .bf-reader-nav a:last-child{background:var(--bf-ink);color:#fffdf8;border-color:var(--bf-ink);}
#belief-files .bf-reader-nav a span{font-size:11px;font-weight:400;opacity:.8;margin-bottom:2px;}
#belief-files .bf-perspective{margin:25px 0 0;padding-top:18px;color:var(--bf-muted);font-size:12px;line-height:1.8;}
@media(max-width:600px){
 #belief-files .bf-library-grid{grid-template-columns:1fr;gap:14px;}
 #belief-files .bf-case{padding:22px;}
 #belief-files .bf-table,#belief-files .bf-table tbody{display:block;}
 #belief-files .bf-table thead{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}
 #belief-files .bf-table tr{display:block;margin:0 0 14px;border:1px solid var(--bf-line);border-radius:10px;overflow:hidden;background:var(--bf-paper);}
 #belief-files .bf-table tbody th,#belief-files .bf-table td{display:block;width:100%;border:0;padding:12px 15px;}
 #belief-files .bf-table td{border-top:1px solid var(--bf-line);}
 #belief-files .bf-table td::before{content:attr(data-label);display:block;font-size:11px;font-weight:650;color:var(--bf-gold);margin-bottom:4px;}
 #belief-files .bf-article h2{font-size:26px;}
}
@media(prefers-reduced-motion:reduce){#belief-files{scroll-behavior:auto;}}
</style>"""


def _value(value):
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value or "")


def case_href(href, section=None, *, case_id=CASE_ID, fragment=""):
    """Use normal app navigation without forwarding email actions or old cases."""
    base = urlsplit(href("belief"))
    query = dict(parse_qsl(base.query, keep_blank_values=True))
    for name in ("token", "action", "message", "case", "section"):
        query.pop(name, None)
    query["v"] = "belief"
    if case_id == CASE_ID:
        query["case"] = CASE_ID
        if section and section != "overview":
            query["section"] = section
    return urlunsplit((base.scheme, base.netloc, base.path, urlencode(query), fragment))


def manuscript_sections():
    parts = re.split(r"^## (.+)$", CASE_MARKDOWN.read_text(encoding="utf-8"), flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


_INLINE = re.compile(
    r"\[([^\]]+)\]\((https://[^\s)]+)\)|\*\*([^*]+)\*\*|(?<!\*)\*([^*]+)\*(?!\*)|\[(\d[\d, -]*)\]"
)


def inline_html(text, href=None):
    """Render the manuscript's small Markdown vocabulary with escaped text."""
    output = []
    cursor = 0
    for match in _INLINE.finditer(text):
        output.append(escape(text[cursor:match.start()]))
        label, url, bold, italic, citation = match.groups()
        if url:
            parsed = urlsplit(url)
            if parsed.hostname and not parsed.username and not parsed.password:
                output.append(f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>')
            else:
                output.append(escape(label))
        elif bold:
            output.append("<strong>" + inline_html(bold, href) + "</strong>")
        elif italic:
            output.append("<em>" + inline_html(italic, href) + "</em>")
        elif href:
            first = re.match(r"\d+", citation)[0]
            target = case_href(href, "sources", fragment="source-" + first)
            output.append(f'<a class="bf-citation" href="{escape(target, quote=True)}" target="_self" aria-label="Open source notes {escape(citation)}">[{escape(citation)}]</a>')
        else:
            output.append("[" + escape(citation) + "]")
        cursor = match.end()
    output.append(escape(text[cursor:]))
    return "".join(output)


def markdown_html(markdown, href=None, *, sources=False):
    """Keep tables semantic on desktop and label their cells for phone cards."""
    lines = markdown.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("### "):
            output.append("<h3>" + inline_html(line[4:], href) + "</h3>")
        elif line.startswith("## "):
            output.append("<h2>" + inline_html(line[3:], href) + "</h2>")
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            headers = rows[0]
            output.append('<table class="bf-table"><thead><tr>' + "".join('<th scope="col">' + inline_html(x, href) + '</th>' for x in headers) + '</tr></thead><tbody>')
            for row in rows[1:]:
                output.append('<tr>')
                for col, value in enumerate(row):
                    if col == 0:
                        output.append('<th scope="row">' + inline_html(value, href) + '</th>')
                    else:
                        output.append(f'<td data-label="{escape(headers[col], quote=True)}">' + inline_html(value, href) + '</td>')
                output.append('</tr>')
            output.append('</tbody></table>')
            continue
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            ordered = not line.startswith("- ")
            tag = "ol" if ordered else "ul"
            output.append("<" + tag + ">")
            pattern = r"^\d+\. " if ordered else r"^- "
            while i < len(lines) and re.match(pattern, lines[i].strip()):
                value = re.sub(pattern, "", lines[i].strip(), count=1)
                output.append("<li>" + inline_html(value, href) + "</li>")
                i += 1
            output.append("</" + tag + ">")
            continue
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||- |\d+\. )", lines[i + 1].strip()):
                i += 1
                paragraph.append(lines[i].strip())
            text = " ".join(paragraph)
            source = re.match(r"\*\*\[(\d+)\]", text) if sources else None
            if source:
                output.append('<div class="bf-source" id="source-' + source[1] + '"><p>' + inline_html(text) + '</p></div>')
            else:
                output.append('<p>' + inline_html(text, href) + '</p>')
        i += 1
    return "".join(output)


def library_html(href, published_url=""):
    public = belief_files_url(published_url)
    parsed = urlsplit(public)
    first_vision = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, "tbf-first-vision"))
    introduction = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, "tbf-intro"))
    return f'''<main id="belief-files" aria-labelledby="bf-title">
<p class="bf-eyebrow">Faith. History. Evidence.</p><h1 id="bf-title">The Belief Files</h1>
<p class="bf-lead">Know the claim. Examine the evidence. Explore religious beliefs through historical records and Scripture, with care for the people who hold them.</p>
<div class="bf-meta"><span>LDS origins and authority</span><span>Beyond the Message</span></div>
<div class="bf-library-grid">
<a class="bf-case bf-featured" href="{escape(case_href(href), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 002 · Read in the app</span><h2>{CASE_TITLE}</h2><p>The English manuscripts, the reported translation process, and the testimony behind the ancient-record claim.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(first_vision, quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="Read Case File 001 The First Vision on Beyond the Message (opens in a new tab)"><span class="bf-eyebrow">Case File 001</span><h2>The First Vision</h2><p>One reported experience. Four surviving accounts. Examine what the documents establish and what remains a judgment.</p><span class="bf-case-link">Read on Beyond the Message ↗</span></a>
</div>
<div class="bf-library-note">New to the comparison?<br><a href="{escape(introduction, quote=True)}" target="_blank" rel="noopener noreferrer">Begin with LDS &amp; biblical Christianity ↗</a><br><a href="{escape(public, quote=True)}" target="_blank" rel="noopener noreferrer">Explore the full collection on our website ↗</a></div>
<p class="bf-perspective">Historical findings and theological judgments are distinguished. Beyond the Message writes from an evangelical and Trinitarian Christian perspective.</p>
</main>'''


def reader_html(href, section="overview"):
    index = next((i for i, chapter in enumerate(CHAPTERS) if chapter[0] == section), 0)
    key, label, headings = CHAPTERS[index]
    sections = manuscript_sections()
    chapter_links = []
    for number, (chapter_key, chapter_label, _) in enumerate(CHAPTERS, 1):
        current = ' aria-current="page"' if chapter_key == key else ''
        target = escape(case_href(href, chapter_key), quote=True)
        chapter_links.append(f'<a href="{target}" target="_self"{current}><span>{number:02}</span>{chapter_label}</a>')
    body = "\n\n".join("## " + heading + "\n\n" + sections[heading] for heading in headings)
    if index:
        previous_key, previous_label, _ = CHAPTERS[index - 1]
        previous_url = case_href(href, previous_key)
    else:
        previous_label = "All case files"
        previous_url = case_href(href, case_id=None)
    if index + 1 < len(CHAPTERS):
        next_key, next_label, _ = CHAPTERS[index + 1]
        next_url = case_href(href, next_key)
        next_direction = "Next section"
    else:
        next_label = "All case files"
        next_url = case_href(href, case_id=None)
        next_direction = "Explore"
    return f'''<main id="belief-files" aria-labelledby="bf-title">
<a class="bf-back" href="{escape(case_href(href, case_id=None), quote=True)}" target="_self">← All case files</a>
<p class="bf-eyebrow">Case File 002 · LDS origins and authority</p><h1 id="bf-title">{CASE_TITLE}</h1>
<div class="bf-meta"><span>Historical investigation and biblical assessment</span><span>About 25 minutes in full</span></div>
<details class="bf-contents"><summary>Contents <span>Section {index + 1} of {len(CHAPTERS)} · {label}</span></summary><nav class="bf-chapters" aria-label="Case File 002 sections">{''.join(chapter_links)}</nav></details>
<article class="bf-article" aria-label="{label}">{markdown_html(body, href, sources=key == 'sources')}</article>
<nav class="bf-reader-nav" aria-label="Continue reading"><a href="{escape(previous_url, quote=True)}" target="_self"><span>Back</span>{previous_label}</a><a href="{escape(next_url, quote=True)}" target="_self"><span>{next_direction}</span>{next_label} →</a></nav>
<p class="bf-perspective">The Belief Files · Beyond the Message<br>Evidence is weighed separately from the project's Christian theological assessment.</p>
</main>'''


def render_belief_files(href, query, published_url=""):
    import streamlit as st

    case = _value(query.get("case"))
    if case != CASE_ID:
        st.html(BELIEF_CSS + library_html(href, published_url))
        return
    st.html(BELIEF_CSS + reader_html(href, _value(query.get("section"))))
    st.download_button(
        "Download the complete case PDF · 22 pages",
        data=CASE_PDF.read_bytes(),
        file_name="Case_File_002_Book_of_Mormon_Translation.pdf",
        mime="application/pdf",
        key="belief_case_002_pdf",
        use_container_width=True,
    )
