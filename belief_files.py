"""The Belief Files library and a source-linked reader for approved case files."""

from html import escape
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from home_hub import belief_files_url
from belief_islam import ISLAM_CASE_FILES, RESEARCH_PDF


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

ABRAHAM_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The surviving papyri", "Exhibit two The Egyptian working papers", "Exhibit three The facsimiles")),
    ("witnesses", "Witnesses", ("Assessing the principal accounts",)),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

EXALTATION_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The early revelations", "Exhibit two The King Follett discourse", "Exhibit three The ancient Christian comparison")),
    ("witnesses", "Witnesses", ("Assessing the principal accounts",)),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

DNA_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The ancestry claim", "Exhibit two The genetic findings", "Exhibit three What can remain undetected")),
    ("witnesses", "Evidence quality", ("Assessing the principal evidence",)),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

PRIESTHOOD_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The Relief Society records", "Exhibit two Healing and changing practice", "Exhibit three The temple connection")),
    ("witnesses", "Witnesses", ("Assessing the principal accounts",)),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

MOTHER_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The early publications", "Exhibit two Recollections about Joseph Smith", "Exhibit three Institutional teaching and prayer")),
    ("witnesses", "Witnesses", ("Assessing the principal accounts",)),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

VIOLENCE_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one Persecution and retaliation", "Exhibit two Native neighbors and violent preaching", "Exhibit three Mountain Meadows and responsibility", "Exhibit four Paiute testimony and later acknowledgment")),
    ("witnesses", "Witnesses", ("Assessing the principal accounts",)),
    ("explanations", "Explanations", ("The strongest LDS argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

NAUVOO_CHAPTERS = (
    ('overview', 'Overview', ('Investigation summary', 'The claim under investigation', 'How this investigation weighs evidence')),
    ('evidence', 'Evidence', ('The historical timeline', 'Exhibit one The Kirtland record', 'Exhibit two The Nauvoo documents', 'Exhibit three Women consent and differing relationships')),
    ('witnesses', 'Witnesses', ('Exhibit four The angel and spiritual testimony', 'Assessing the principal accounts')),
    ('explanations', 'Explanations', ('The strongest LDS argument', 'Competing explanations', 'Motives benefits and costs')),
    ('scripture', 'Scripture', ('A biblical assessment',)),
    ('assessment', 'Assessment', ('Findings and confidence', 'Overall assessment')),
    ('discuss', 'Discuss', ('Read compare and discuss', 'Accuracy notes and further research')),
    ('sources', 'Sources', ('Sources and reading',)),
)

UTAH_FAMILIES_CHAPTERS = (
    ('overview', 'Overview', ('Investigation summary', 'The claim under investigation', 'How this investigation weighs evidence')),
    ('evidence', 'Evidence', ('The historical timeline', 'Exhibit one Counting plural households', 'Exhibit two Women speaking in public and private', 'Exhibit three Consent provision and family responsibility')),
    ('witnesses', 'Witnesses', ('Assessing the principal accounts',)),
    ('explanations', 'Explanations', ('The strongest LDS argument', 'Competing explanations', 'Motives benefits and costs')),
    ('scripture', 'Scripture', ('A biblical assessment',)),
    ('assessment', 'Assessment', ('Findings and confidence', 'Overall assessment')),
    ('discuss', 'Discuss', ('Read compare and discuss', 'Accuracy notes and further research')),
    ('sources', 'Sources', ('Sources and reading',)),
)

MANIFESTO_CHAPTERS = (
    ('overview', 'Overview', ('Investigation summary', 'The claim under investigation', 'How this investigation weighs evidence')),
    ('evidence', 'Evidence', ('The historical timeline', "Exhibit one The pressure and Woodruff's response", 'Exhibit two What the first Manifesto said', 'Exhibit three What continued after 1890', 'Exhibit four The Second Manifesto')),
    ('witnesses', 'Witnesses', ('Assessing the principal accounts',)),
    ('explanations', 'Explanations', ('The strongest LDS argument', 'Competing explanations', 'Motives benefits and costs')),
    ('scripture', 'Scripture', ('A biblical assessment',)),
    ('assessment', 'Assessment', ('Findings and confidence', 'Overall assessment')),
    ('discuss', 'Discuss', ('Read compare and discuss', 'Accuracy notes and further research')),
    ('sources', 'Sources', ('Sources and reading',)),
)

RACE_CHAPTERS = (
    ('overview', 'Overview', ('Investigation summary', 'The claim under investigation', 'How this investigation weighs evidence')),
    ('evidence', 'Evidence', ('The historical timeline', 'Exhibit one An early elder and a later restriction', "Exhibit two Jane Manning James's request", 'Exhibit three The authority of the explanations', 'Exhibit four The 1978 change')),
    ('witnesses', 'Witnesses', ('Assessing the principal accounts',)),
    ('explanations', 'Explanations', ('The strongest LDS argument', 'Competing explanations', 'Motives benefits and costs')),
    ('scripture', 'Scripture', ('A biblical assessment',)),
    ('assessment', 'Assessment', ('Findings and confidence', 'Overall assessment')),
    ('discuss', 'Discuss', ('Read compare and discuss', 'Accuracy notes and further research')),
    ('sources', 'Sources', ('Sources and reading',)),
)

GUIDE_CHAPTERS = (
    ("overview", "Start Here", ("The purpose of this guide", "A simple first conversation")),
    ("listen", "Listen", ("Begin with the person", "Listen and reflect before answering")),
    ("clarify", "Clarify", ("Clarify the words you share", "Explain the differences carefully")),
    ("gospel", "The Gospel", ("Share the gospel plainly", "Read a passage rather than trade slogans")),
    ("questions", "Hard Questions", ("Work through common questions",)),
    ("evidence", "Use the Cases", ("Use the investigations when they answer a real question", "Keep evidence and conclusions distinct")),
    ("practice", "Practice and Follow Up", ("Practice the conversation", "Invite a response and follow through")),
    ("sources", "Sources", ("Sources and reading",)),
)

# Publication order is independent of the source packet count. The final guide
# closes the collection separately and does not consume a numbered case slot.
COLLECTION_PLAN = (
    ("00", "LDS & biblical Christianity"),
    ("001", "The First Vision"),
    ("002", "The Book of Mormon Translation"),
    ("003", "The Book of Abraham"),
    ("004", "Becoming Like God"),
    ("005", "The Book of Mormon and DNA"),
    ("006", "Priesthood Temples and Women"),
    ("007", "Mother in Heaven"),
    ("008", "Peace and Violence in the Nineteenth Century"),
    ("009", "Plural Marriage in Kirtland and Nauvoo"),
    ("010", "Plural Marriage and Families in Early Utah"),
    ("011", "The Manifesto and the End of Plural Marriage"),
    ("012", "Race and the Priesthood"),
)

CASE_FILES = {
    "002": {
        "title": CASE_TITLE, "markdown": CASE_MARKDOWN, "pdf": CASE_PDF,
        "chapters": CHAPTERS, "sources": 22,
        "download_name": "Case_File_002_Book_of_Mormon_Translation.pdf",
    },
    "003": {
        "title": "The Book of Abraham",
        "markdown": Path(__file__).with_name("belief_case_003.md"),
        "pdf": Path(__file__).with_name("belief_case_003.pdf"),
        "chapters": ABRAHAM_CHAPTERS, "sources": 22,
        "download_name": "Case_File_003_Book_of_Abraham.pdf",
    },
    "004": {
        "title": "Becoming Like God",
        "markdown": Path(__file__).with_name("belief_case_004.md"),
        "pdf": Path(__file__).with_name("belief_case_004.pdf"),
        "chapters": EXALTATION_CHAPTERS, "sources": 22,
        "download_name": "Case_File_004_Becoming_Like_God.pdf",
    },
    "005": {
        "title": "The Book of Mormon and DNA",
        "markdown": Path(__file__).with_name("belief_case_005.md"),
        "pdf": Path(__file__).with_name("belief_case_005.pdf"),
        "chapters": DNA_CHAPTERS, "sources": 20,
        "download_name": "Case_File_005_The_Book_of_Mormon_and_DNA.pdf",
    },
    "006": {
        "title": "Priesthood Temples and Women",
        "markdown": Path(__file__).with_name("belief_case_006.md"),
        "pdf": Path(__file__).with_name("belief_case_006.pdf"),
        "chapters": PRIESTHOOD_CHAPTERS, "sources": 21,
        "download_name": "Case_File_006_Priesthood_Temples_and_Women.pdf",
    },
    "007": {
        "title": "Mother in Heaven",
        "markdown": Path(__file__).with_name("belief_case_007.md"),
        "pdf": Path(__file__).with_name("belief_case_007.pdf"),
        "chapters": MOTHER_CHAPTERS, "sources": 19,
        "download_name": "Case_File_007_Mother_in_Heaven.pdf",
    },
    "008": {
        "title": "Peace and Violence in the Nineteenth Century",
        "markdown": Path(__file__).with_name("belief_case_008.md"),
        "pdf": Path(__file__).with_name("belief_case_008.pdf"),
        "chapters": VIOLENCE_CHAPTERS, "sources": 22,
        "download_name": "Case_File_008_Peace_and_Violence_in_the_Nineteenth_Century.pdf",
    },
    "009": {
        "title": "Plural Marriage in Kirtland and Nauvoo",
        "markdown": Path(__file__).with_name("belief_case_009.md"),
        "pdf": Path(__file__).with_name("belief_case_009.pdf"),
        "chapters": NAUVOO_CHAPTERS, "sources": 22,
        "download_name": "Case_File_009_Plural_Marriage_in_Kirtland_and_Nauvoo.pdf",
    },
    "010": {
        "title": "Plural Marriage and Families in Early Utah",
        "markdown": Path(__file__).with_name("belief_case_010.md"),
        "pdf": Path(__file__).with_name("belief_case_010.pdf"),
        "chapters": UTAH_FAMILIES_CHAPTERS, "sources": 20,
        "download_name": "Case_File_010_Plural_Marriage_and_Families_in_Early_Utah.pdf",
    },
    "011": {
        "title": "The Manifesto and the End of Plural Marriage",
        "markdown": Path(__file__).with_name("belief_case_011.md"),
        "pdf": Path(__file__).with_name("belief_case_011.pdf"),
        "chapters": MANIFESTO_CHAPTERS, "sources": 15,
        "download_name": "Case_File_011_The_Manifesto_and_the_End_of_Plural_Marriage.pdf",
    },
    "012": {
        "title": "Race and the Priesthood",
        "markdown": Path(__file__).with_name("belief_case_012.md"),
        "pdf": Path(__file__).with_name("belief_case_012.pdf"),
        "chapters": RACE_CHAPTERS, "sources": 23,
        "download_name": "Case_File_012_Race_and_the_Priesthood.pdf",
    },
    "conversation": {
        "title": "A Christian Conversation Guide for LDS Friends",
        "markdown": Path(__file__).with_name("belief_conversation_lds.md"),
        "pdf": Path(__file__).with_name("belief_conversation_lds.pdf"),
        "chapters": GUIDE_CHAPTERS, "sources": 15,
        "label": "Christian conversation guide",
        "topic": "LDS faith and Christian witness",
        "description": "Sharing the gospel with clarity and respect",
        "download_name": "LDS_Christian_Conversation_Guide.pdf",
        "download_label": "Download the conversation guide PDF",
        "perspective": "Practical guidance from an evangelical and Trinitarian Christian perspective.",
    },
}


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
#belief-files .bf-new{display:inline-block;border:1px solid #b09a78;border-radius:20px;padding:1px 7px;margin-left:7px;font-size:10px;letter-spacing:.04em;vertical-align:1px;}
#belief-files .bf-library-note{padding:20px 0;border-top:1px solid var(--bf-line);font-size:14px;line-height:1.75;color:var(--bf-muted);}
#belief-files .bf-library-note a{display:inline-flex;align-items:center;min-height:44px;}
#belief-files .bf-plan{list-style:none;padding:0;margin:0 0 16px;}
#belief-files .bf-plan li{font-size:14px;line-height:1.7;padding:9px 0;border-bottom:1px solid var(--bf-line);}
#belief-files .bf-plan strong{display:inline-block;color:var(--bf-gold);min-width:36px;font-size:12px;}
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
#belief-files .bf-source-focus{padding:20px;border:1px solid #b09a78;border-radius:12px;background:#f4efe3;margin:20px 0;}
#belief-files .bf-source-focus p{font-size:15px;line-height:1.8;}
#belief-files .bf-source-focus .bf-eyebrow{font-size:11px;}
#belief-files .bf-source-focus > a{display:inline-flex;align-items:center;min-height:44px;font-size:13px;font-weight:600;}
#belief-files .bf-register{margin:20px 0;border:1px solid var(--bf-line);border-radius:12px;padding:0 17px;background:var(--bf-paper);}
#belief-files .bf-register summary{cursor:pointer;min-height:52px;padding:14px 0;font-size:14px;font-weight:650;}
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


def _cases(collection):
    return ISLAM_CASE_FILES if collection == "islam" else CASE_FILES


def _source_ids(case):
    return case.get("source_ids", tuple(str(i) for i in range(1, case["sources"] + 1)))


def collection_href(href, collection=None):
    """An explicit collection or the chooser; never carry a stale case."""
    return case_href(href, case_id=None, collection=collection)


def case_href(href, section=None, *, case_id=CASE_ID, source=None, collection="lds"):
    """Use normal app navigation without forwarding email actions or old cases."""
    base = urlsplit(href("belief"))
    query = dict(parse_qsl(base.query, keep_blank_values=True))
    for name in ("token", "action", "message", "collection", "case", "section", "source"):
        query.pop(name, None)
    query["v"] = "belief"
    # Old LDS case URLs remain valid. Only Islam needs a scope on every link.
    if collection == "islam" or collection == "lds" and case_id is None:
        query["collection"] = collection
    cases = _cases(collection)
    if collection in ("lds", "islam") and case_id in cases:
        case = cases[case_id]
        query["case"] = case_id
        if section and section != "overview" and section in {chapter[0] for chapter in case["chapters"]}:
            query["section"] = section
        if section == "sources" and str(source) in _source_ids(case):
            query["source"] = str(source)
    return urlunsplit((base.scheme, base.netloc, base.path, urlencode(query), ""))


def manuscript_sections(case_id=CASE_ID, *, collection="lds"):
    parts = re.split(r"^## (.+)$", _cases(collection)[case_id]["markdown"].read_text(encoding="utf-8"), flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


_INLINE = re.compile(
    r"\[([^\]]+)\]\((https://[^\s)]+)\)|\*\*([^*]+)\*\*|(?<!\*)\*([^*]+)\*(?!\*)|\[((?:\d[\d, -]*)|(?:[A-Z]+\d+(?:[;,] *[A-Z]+\d+)*))\]"
)


def inline_html(text, href=None, *, case_id=CASE_ID, collection="lds"):
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
            output.append("<strong>" + inline_html(bold, href, case_id=case_id, collection=collection) + "</strong>")
        elif italic:
            output.append("<em>" + inline_html(italic, href, case_id=case_id, collection=collection) + "</em>")
        elif href:
            if re.match(r"[A-Z]", citation):
                # Each named source can be opened directly, including a group.
                # Individual links also wrap cleanly on a narrow phone screen.
                links = []
                for code in re.split(r"[;,] *", citation):
                    target = case_href(href, "sources", case_id=case_id, source=code, collection=collection)
                    links.append(f'<a class="bf-citation" href="{escape(target, quote=True)}" target="_self" aria-label="Open source notes {code}">{code}</a>')
                output.append('[' + '; '.join(links) + ']')
                cursor = match.end()
                continue
            first = re.match(r"(?:[A-Z]+)?\d+", citation)[0]
            target = case_href(href, "sources", case_id=case_id, source=first, collection=collection)
            output.append(f'<a class="bf-citation" href="{escape(target, quote=True)}" target="_self" aria-label="Open source notes {escape(citation)}">[{escape(citation)}]</a>')
        else:
            output.append("[" + escape(citation) + "]")
        cursor = match.end()
    output.append(escape(text[cursor:]))
    return "".join(output)


def markdown_html(markdown, href=None, *, sources=False, case_id=CASE_ID, collection="lds"):
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
            output.append("<h3>" + inline_html(line[4:], href, case_id=case_id, collection=collection) + "</h3>")
        elif line.startswith("## "):
            output.append("<h2>" + inline_html(line[3:], href, case_id=case_id, collection=collection) + "</h2>")
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            headers = rows[0]
            output.append('<table class="bf-table"><thead><tr>' + "".join('<th scope="col">' + inline_html(x, href, case_id=case_id, collection=collection) + '</th>' for x in headers) + '</tr></thead><tbody>')
            for row in rows[1:]:
                output.append('<tr>')
                for col, value in enumerate(row):
                    if col == 0:
                        output.append('<th scope="row">' + inline_html(value, href, case_id=case_id, collection=collection) + '</th>')
                    else:
                        output.append(f'<td data-label="{escape(headers[col], quote=True)}">' + inline_html(value, href, case_id=case_id, collection=collection) + '</td>')
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
                output.append("<li>" + inline_html(value, href, case_id=case_id, collection=collection) + "</li>")
                i += 1
            output.append("</" + tag + ">")
            continue
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||- |\d+\. )", lines[i + 1].strip()):
                i += 1
                paragraph.append(lines[i].strip())
            text = " ".join(paragraph)
            source = re.match(r"\*\*(?:\[(\d+)\]|([A-Z]+\d+)\*\*)", text) if sources else None
            if source:
                output.append('<div class="bf-source" id="source-' + (source[1] or source[2]) + '"><p>' + inline_html(text) + '</p></div>')
            else:
                output.append('<p>' + inline_html(text, href, case_id=case_id, collection=collection) + '</p>')
        i += 1
    return "".join(output)


def library_html(href, published_url=""):
    public = belief_files_url(published_url)
    parsed = urlsplit(public)
    first_vision = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, "tbf-first-vision"))
    introduction = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, "tbf-intro"))
    return f'''<main id="belief-files" aria-labelledby="bf-title">
<a class="bf-back" href="{escape(collection_href(href), quote=True)}" target="_self">← All collections</a>
<p class="bf-eyebrow">The Belief Files · LDS collection</p><h1 id="bf-title">LDS &amp; biblical Christianity</h1>
<p class="bf-lead">Examine the claims of restoration through Scripture, historical records, and the people who witnessed the beginnings.</p>
<div class="bf-meta"><span>LDS origins and authority</span><span>Beyond the Message</span></div>
<div class="bf-library-grid">
<a class="bf-case bf-featured" href="{escape(introduction, quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="Read 00 Start Here LDS and biblical Christianity on Beyond the Message (opens in a new tab)"><span class="bf-eyebrow">00 · Start Here</span><h2>LDS &amp; biblical Christianity</h2><p>God, grace, Scripture, and restoration. Begin with the foundational comparison before opening the historical cases.</p><span class="bf-case-link">Read on Beyond the Message →</span></a>
<a class="bf-case" href="{escape(first_vision, quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="Read Case File 001 The First Vision on Beyond the Message (opens in a new tab)"><span class="bf-eyebrow">Case File 001</span><h2>The First Vision</h2><p>One reported experience. Four surviving accounts. Examine what the documents establish and what remains a judgment.</p><span class="bf-case-link">Read on Beyond the Message →</span></a>
<a class="bf-case" href="{escape(case_href(href), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 002 · Read in the app</span><h2>{CASE_TITLE}</h2><p>The English manuscripts, the reported translation process, and the testimony behind the ancient-record claim.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='003'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 003 · Read in the app</span><h2>The Book of Abraham</h2><p>The surviving Egyptian papyri, the facsimiles, and the question of translation and revelation.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='004'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 004 · Read in the app</span><h2>Becoming Like God</h2><p>The development of exaltation teaching, the King Follett discourse, and the comparison with ancient Christian deification.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='005'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 005 · Read in the app</span><h2>The Book of Mormon and DNA</h2><p>Ancient genomes, ancestry claims, and what genetic evidence can establish about the reported migrations.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='006'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 006 · Read in the app</span><h2>Priesthood Temples and Women</h2><p>The Relief Society records, healing blessings, temple participation, and the question of restored authority.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='007'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 007 · Read in the app</span><h2>Mother in Heaven</h2><p>The early publications, later recollections, and the biblical questions behind the doctrine of heavenly parents.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='008'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 008 · Read in the app</span><h2>Peace and Violence in the Nineteenth Century</h2><p>Persecution, violent preaching, Mountain Meadows, and the evidence for responsibility and accountability.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='009'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 009 · Read in the app</span><h2>Plural Marriage in Kirtland and Nauvoo</h2><p>The surviving documents, women's accounts, and the claim that God commanded Joseph Smith's plural marriages.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='010'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 010 · Read in the app</span><h2>Plural Marriage and Families in Early Utah</h2><p>Women's public and private accounts, family responsibilities, demographic claims, and the costs of the practice.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='011'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 011 · Read in the app</span><h2>The Manifesto and the End of Plural Marriage</h2><p>The 1890 declaration, continued relationships and new unions, Senate testimony, and the 1904 prohibition.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='012'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 012</span><h2>Race and the Priesthood</h2><p>Early Black priesthood holders, temple restrictions, members' petitions, and the change announced in 1978.</p><span class="bf-case-link">Open the case →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='conversation'), quote=True)}" target="_self"><span class="bf-eyebrow">Closing conversation guide <span class="bf-new">New</span></span><h2>A Christian Conversation Guide for LDS Friends</h2><p>How to begin, explain the gospel, discuss real differences, and follow up with clarity and respect.</p><span class="bf-case-link">Open the guide →</span></a>
</div>
<div class="bf-library-note">The LDS collection: 00 introduction, 12 case files, and a separate closing Christian conversation guide. Follow the collection in order, or open the case you want to examine.</div>
<div class="bf-library-note">The Christian conversation guide follows Case 012 as the closing resource. All fourteen resources are now available: the introduction, twelve numbered investigations, and the guide.</div>
<div class="bf-library-note"><a href="{escape(public, quote=True)}" target="_blank" rel="noopener noreferrer">Explore the collection on our website →</a></div>
<p class="bf-perspective">Historical findings and theological judgments are distinguished. Beyond the Message writes from an evangelical and Trinitarian Christian perspective.</p>
</main>'''


def collections_html(href):
    return f'''<main id="belief-files" aria-labelledby="bf-title">
<p class="bf-eyebrow">Faith. History. Evidence.</p><h1 id="bf-title">The Belief Files</h1>
<p class="bf-lead">Know the claim. Examine the evidence. Explore religious beliefs through historical records and Scripture, with care for the people who hold them.</p>
<div class="bf-meta"><span>Choose a collection</span><span>Beyond the Message</span></div>
<div class="bf-library-grid">
<a class="bf-case bf-featured" href="{escape(collection_href(href, 'lds'), quote=True)}" target="_self"><span class="bf-eyebrow">LDS collection</span><h2>LDS &amp; biblical Christianity</h2><p>God, grace, Scripture, and restoration. Explore the foundational comparison, twelve historical cases, and a closing conversation guide.</p><span class="bf-case-link">Explore the LDS collection →</span></a>
<a class="bf-case" href="{escape(collection_href(href, 'islam'), quote=True)}" target="_self"><span class="bf-eyebrow">Islam collection <span class="bf-new">New</span></span><h2>Islam &amp; biblical Christianity</h2><p>God, Jesus, Scripture, and prophetic authority. Begin with the foundational comparison, then examine Muhammad and the prophetic claim.</p><span class="bf-case-link">Explore the Islam collection →</span></a>
</div>
<div class="bf-library-note"><strong>A clear path through each collection.</strong><br>Begin with 00 · Start Here. Examine the historical cases and their sources. Use the readings and discussion questions to continue the conversation.</div>
<p class="bf-perspective">Historical findings and theological judgments are distinguished. Beyond the Message writes from an evangelical and Trinitarian Christian perspective.</p>
</main>'''


def islam_library_html(href):
    return f'''<main id="belief-files" aria-labelledby="bf-title">
<a class="bf-back" href="{escape(collection_href(href), quote=True)}" target="_self">← All collections</a>
<p class="bf-eyebrow">The Belief Files · Islam collection</p><h1 id="bf-title">Islam &amp; biblical Christianity</h1>
<p class="bf-lead">What is the claim? What does the evidence establish? Explore God, Jesus, revelation, and authority through Islamic sources, historical records, and Scripture.</p>
<div class="bf-meta"><span>Origins, revelation, and the gospel</span><span>Beyond the Message</span></div>
<div class="bf-library-grid">
<a class="bf-case bf-featured" href="{escape(case_href(href, case_id='00', collection='islam'), quote=True)}" target="_self"><span class="bf-eyebrow">00 · Start Here</span><h2>Islam &amp; biblical Christianity</h2><p>God, the identity of Jesus, salvation, Scripture, and authority. Begin with the foundational comparison before opening the historical cases.</p><span class="bf-case-link">Read the introduction →</span></a>
<a class="bf-case" href="{escape(case_href(href, case_id='001', collection='islam'), quote=True)}" target="_self"><span class="bf-eyebrow">Case File 001 · Read in the app</span><h2>Muhammad and the Prophetic Claim</h2><p>The reported calling, the witnesses and their transmission, the strongest Muslim argument, and the evidence for prophetic authority.</p><span class="bf-case-link">Open the case →</span></a>
</div>
<div class="bf-library-note"><strong>The collection is growing.</strong><br>The foundational comparison and Case File 001 are available now. Further historical cases and a closing conversation guide will be added as they are completed.</div>
<div class="bf-library-note"><strong>Go deeper in the research.</strong><br>The reader includes linked source notes and a complete PDF for each published study. Research Packet 001 adds claim cards, lessons, discussion questions, and contextual KJV readings. Research packets and historical case files are separate resources.</div>
<p class="bf-perspective">Historical findings and theological judgments are distinguished. The Christian assessment is evangelical and Trinitarian; Muslim beliefs are attributed to the sources and traditions being examined.</p>
</main>'''


def reader_html(href, section="overview", *, source="", case_id=CASE_ID, collection="lds"):
    case = _cases(collection)[case_id]
    reader_label = case.get("label", "Case File " + case_id)
    topic = case.get("topic", "LDS origins and authority")
    description = case.get("description", "Historical investigation and biblical assessment")
    perspective = case.get("perspective", "Evidence is weighed separately from the project's Christian theological assessment.")
    chapters = case["chapters"]
    source_count = case["sources"]
    index = next((i for i, chapter in enumerate(chapters) if chapter[0] == section), 0)
    key, label, headings = chapters[index]
    sections = manuscript_sections(case_id, collection=collection)
    back_label = "Islam collection" if collection == "islam" else "All case files"
    back_url = collection_href(href, collection)
    chapter_links = []
    for number, (chapter_key, chapter_label, _) in enumerate(chapters, 1):
        current = ' aria-current="page"' if chapter_key == key else ''
        target = escape(case_href(href, chapter_key, case_id=case_id, collection=collection), quote=True)
        chapter_links.append(f'<a href="{target}" target="_self"{current}><span>{number:02}</span>{chapter_label}</a>')
    body = "\n\n".join("## " + heading + "\n\n" + sections[heading] for heading in headings)
    article = markdown_html(body, href, sources=key == "sources", case_id=case_id, collection=collection)
    if key == "sources" and str(source) in _source_ids(case):
        paragraphs = sections["Sources and reading"].split("\n\n")
        selected = next(p for p in paragraphs if p.startswith(("**[" + str(source) + "]", "**" + str(source) + "**")))
        article = ('<h2>Sources and reading</h2>' + markdown_html(paragraphs[0])
                   + '<section class="bf-source-focus" aria-label="Referenced source ' + str(source) + '">'
                   + '<p class="bf-eyebrow">Referenced source ' + str(source) + '</p><p>' + inline_html(selected) + '</p>'
                   + '<a href="' + escape(case_href(href, "sources", case_id=case_id, collection=collection), quote=True) + '" target="_self">View all ' + str(source_count) + ' sources →</a></section>'
                   + '<details class="bf-register"><summary>All ' + str(source_count) + ' sources</summary>'
                   + markdown_html("\n\n".join(paragraphs[1:]), sources=True) + '</details>')
    if index:
        previous_key, previous_label, _ = chapters[index - 1]
        previous_url = case_href(href, previous_key, case_id=case_id, collection=collection)
    else:
        previous_label = back_label
        previous_url = back_url
    if index + 1 < len(chapters):
        next_key, next_label, _ = chapters[index + 1]
        next_url = case_href(href, next_key, case_id=case_id, collection=collection)
        next_direction = "Next section"
    else:
        next_label = back_label
        next_url = back_url
        next_direction = "Explore"
        if collection == "islam" and case_id == "00":
            next_label = "Case File 001"
            next_url = case_href(href, case_id="001", collection="islam")
            next_direction = "Continue the investigation"
    return f'''<main id="belief-files" aria-labelledby="bf-title">
<a class="bf-back" href="{escape(back_url, quote=True)}" target="_self">← {back_label}</a>
<p class="bf-eyebrow">{escape(reader_label)} · {escape(topic)}</p><h1 id="bf-title">{escape(case['title'])}</h1>
<div class="bf-meta"><span>{escape(description)}</span><span>{escape(case.get('reading_time', 'About 25 minutes in full'))}</span></div>
<details class="bf-contents"><summary>Contents <span>Section {index + 1} of {len(chapters)} · {label}</span></summary><nav class="bf-chapters" aria-label="{escape(reader_label, quote=True)} sections">{''.join(chapter_links)}</nav></details>
<article class="bf-article" aria-label="{label}">{article}</article>
<nav class="bf-reader-nav" aria-label="Continue reading"><a href="{escape(previous_url, quote=True)}" target="_self"><span>Back</span>{previous_label}</a><a href="{escape(next_url, quote=True)}" target="_self"><span>{next_direction}</span>{next_label} →</a></nav>
<p class="bf-perspective">The Belief Files · Beyond the Message<br>{escape(perspective)}</p>
</main>'''


def render_belief_files(href, query, published_url=""):
    import streamlit as st

    case = _value(query.get("case"))
    collection = _value(query.get("collection"))
    if not collection and case in CASE_FILES:
        collection = "lds"  # Existing bookmarked LDS cases keep their meaning.
    if collection not in ("lds", "islam"):
        st.html(BELIEF_CSS + collections_html(href))
        return
    cases = _cases(collection)
    if case not in cases:
        st.html(BELIEF_CSS + (islam_library_html(href) if collection == "islam" else library_html(href, published_url)))
        if collection == "islam":
            st.download_button("Download Research Packet 001 (PDF)", data=RESEARCH_PDF.read_bytes(),
                               file_name="Islam_001_Research_and_Reading_Packet.pdf", mime="application/pdf",
                               key="belief_islam_research_001_pdf", use_container_width=True)
        return
    selected = cases[case]
    st.html(BELIEF_CSS + reader_html(href, _value(query.get("section")), source=_value(query.get("source")), case_id=case, collection=collection))
    st.download_button(
        selected.get("download_label", "Download the complete case PDF"),
        data=selected["pdf"].read_bytes(),
        file_name=selected["download_name"],
        mime="application/pdf",
        key="belief_" + collection + "_case_" + case + "_pdf",
        use_container_width=True,
    )
