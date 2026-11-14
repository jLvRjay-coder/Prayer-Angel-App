"""Published Islam collection metadata; research packets are a separate layer."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH_PDF = ROOT / "belief_case_islam_001_research.pdf"
RESEARCH_URL = (
    "https://raw.githubusercontent.com/jLvRjay-coder/Prayer-Angel-App/"
    "main/belief_case_islam_001_research.pdf"
)

INTRO_CHAPTERS = (
    ("overview", "Start Here", ("Begin with the central question", "How to use this collection")),
    ("identity", "God and Jesus", ("God and the identity of Jesus",)),
    ("salvation", "Cross and grace", ("The cross resurrection and salvation",)),
    ("authority", "Scripture and authority", ("Scripture revelation and authority",)),
    ("history", "History and sources", ("Origins and the evidence we examine",)),
    ("discuss", "Read and discuss", ("Read compare and discuss",)),
    ("next", "Your next step", ("Continue the investigation",)),
    ("sources", "Sources", ("Sources and reading",)),
)

CASE_CHAPTERS = (
    ("overview", "Overview", ("Investigation summary", "The claim under investigation", "How this investigation weighs evidence")),
    ("evidence", "Evidence", ("The historical timeline", "Exhibit one The public claim and the historical person", "Exhibit two The reported first calling", "Exhibit three A related account and the problem of transmission", "Exhibit four Character and recognition", "Exhibit five The message as its own proposed sign")),
    ("witnesses", "Witnesses", ("Assessing the witnesses and sources",)),
    ("explanations", "Explanations", ("The strongest Muslim argument", "Competing explanations", "Motives benefits and costs")),
    ("scripture", "Scripture", ("A biblical assessment",)),
    ("assessment", "Assessment", ("Findings and confidence", "Overall assessment")),
    ("discuss", "Discuss", ("Read compare and discuss", "Accuracy notes and further research")),
    ("sources", "Sources", ("Sources and reading",)),
)

ISLAM_CASE_FILES = {
    "00": {
        "title": "Islam & biblical Christianity",
        "label": "00 · Start Here",
        "topic": "Foundational comparison",
        "description": "God, Jesus, salvation, Scripture, and authority",
        "reading_time": "About 10 minutes in full",
        "markdown": ROOT / "belief_case_islam_00.md",
        "pdf": ROOT / "belief_case_islam_00.pdf",
        "chapters": INTRO_CHAPTERS,
        "sources": 18,
        "source_ids": ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "H1", "H2", "H3", "B1", "B2", "B3", "B4", "B5", "B6", "M1", "A1"),
        "download_name": "Islam_and_Biblical_Christianity_Start_Here.pdf",
        "download_label": "Download the introduction PDF",
        "perspective": "A comparison from an evangelical and Trinitarian Christian perspective. Muslim sources are identified separately from the Christian assessment.",
    },
    "001": {
        "title": "Muhammad and the Prophetic Claim",
        "topic": "Islam origins and authority",
        "description": "Historical investigation and biblical assessment",
        "reading_time": "About 35 minutes in full",
        "markdown": ROOT / "belief_case_islam_001.md",
        "pdf": ROOT / "belief_case_islam_001.pdf",
        "chapters": CASE_CHAPTERS,
        "sources": 39,
        "source_ids": ("P1", "Q1", "Q2", "Q4", "Q5", "Q6", "Q8", "Q10", "Q14", "Q17", "Q18", "Q19", "Q95", "H1", "H2", "H3", "H4", "H5", "H95", "A1", "A2", "A3", "A4", "A5", "A9", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B95", "B96"),
        "download_name": "Islam_Case_File_001_Muhammad_and_the_Prophetic_Claim.pdf",
    },
}
