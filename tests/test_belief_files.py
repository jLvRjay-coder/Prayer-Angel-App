"""Approved case coverage, public references, and real app navigation."""

import os
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from belief_files import (
    CASE_MARKDOWN, CASE_PDF, CHAPTERS, case_href, inline_html,
    library_html, manuscript_sections, reader_html,
)
from deploy_space_preview import RUNTIME_FILES


ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.elements = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, text):
        self.parts.append(text)

    @property
    def text(self):
        return " ".join(" ".join(self.parts).split())


def href(view):
    return "?sid=existing-session&theme=light&token=private&action=manage&message=old&v=" + view


class BeliefCaseTests(unittest.TestCase):
    def test_every_manuscript_section_has_one_place_and_no_core_prose_is_lost(self):
        sections = manuscript_sections()
        mapped = [name for _, _, names in CHAPTERS for name in names]
        self.assertEqual(len(mapped), len(set(mapped)))
        self.assertEqual(set(mapped), set(sections) - {"Collection notes"})
        for key, _, names in CHAPTERS:
            document = Document(reader_html(href, key))
            for name in names:
                # Check every paragraph/cell/list line of the original, not a
                # generated summary, including all qualification sentences.
                for line in sections[name].splitlines():
                    text = line.strip()
                    if not text or re.fullmatch(r"[| :\-]+", text):
                        continue
                    text = re.sub(r"^#{2,3}\s+|^\d+\.\s+|^-\s+", "", text)
                    for cell in text.strip("|").split("|"):
                        normalized = Document(inline_html(cell.strip())).text
                        self.assertIn(normalized, document.text, (key, name))

    def test_references_and_witness_distinctions_survive_the_app_format(self):
        sources = Document(reader_html(href, "sources"))
        ids = [attrs["id"] for _, attrs in sources.elements if attrs.get("id", "").startswith("source-")]
        self.assertEqual(ids, ["source-" + str(i) for i in range(1, 23)])
        witnesses = Document(reader_html(href, "witnesses"))
        self.assertIn("two collective witness statements with eleven names", witnesses.text)
        self.assertIn("not eleven separately preserved", witnesses.text)
        self.assertIn("about fifty years later", witnesses.text.lower())
        self.assertTrue(any(tag == "td" and attrs.get("data-label") for tag, attrs in witnesses.elements))
        overview = Document(reader_html(href)).text
        self.assertIn("They also do not establish that Smith knowingly committed fraud.", overview)

    def test_case_routes_keep_session_and_theme_but_never_email_actions(self):
        query = parse_qs(urlsplit(case_href(href, "witnesses")).query)
        self.assertEqual(query, {"sid": ["existing-session"], "theme": ["light"], "v": ["belief"], "case": ["002"], "section": ["witnesses"]})
        self.assertNotIn("case=", case_href(href, case_id=None))
        self.assertNotIn("section=", case_href(href))

    def test_chapter_navigation_references_and_external_links_are_usable(self):
        source_ids = set(range(1, 23))
        for key, _, _ in CHAPTERS:
            doc = Document(reader_html(href, key))
            self.assertEqual(sum(attrs.get("aria-current") == "page" for _, attrs in doc.elements), 1)
            for tag, attrs in doc.elements:
                if tag != "a": continue
                url = urlsplit(attrs["href"])
                if url.scheme:
                    self.assertEqual(url.scheme, "https")
                    self.assertEqual(attrs["target"], "_blank")
                    self.assertIn("noopener", attrs["rel"])
                    self.assertNotIn("sid=", attrs["href"])
                    self.assertNotIn("token=", attrs["href"])
                elif attrs.get("class") == "bf-citation":
                    self.assertEqual(parse_qs(url.query)["section"], ["sources"])
                    self.assertIn(int(url.fragment.split("-")[-1]), source_ids)
        bad = reader_html(href, '<script>alert("unsafe")</script>')
        self.assertIn('aria-label="Overview"', bad)
        self.assertNotIn("<script>", bad)

    def test_library_keeps_published_studies_and_pdfs_ship_with_the_reader(self):
        doc = Document(library_html(href))
        links = [attrs["href"] for tag, attrs in doc.elements if tag == "a"]
        self.assertTrue(any(urlsplit(link).fragment == "tbf-first-vision" for link in links))
        self.assertTrue(any(parse_qs(urlsplit(link).query).get("case") == ["002"] for link in links))
        self.assertIn("belief_files.py", RUNTIME_FILES)
        self.assertIn(CASE_MARKDOWN.name, RUNTIME_FILES)
        self.assertIn(CASE_PDF.name, RUNTIME_FILES)
        self.assertTrue(CASE_PDF.read_bytes().startswith(b"%PDF-"))


class BeliefAppTests(unittest.TestCase):
    def setUp(self):
        self.cwd = Path.cwd()
        os.chdir(ROOT)
        self.at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)

    def tearDown(self):
        sid = self.at.query_params.get("sid", "")
        if sid:
            (ROOT / ".btm_sessions" / f"{sid}.json").unlink(missing_ok=True)
        os.chdir(self.cwd)

    def markup(self):
        return "\n".join(e.proto.body for e in self.at.get("html"))

    def test_home_entry_catalog_all_chapters_pdf_and_return_navigation(self):
        with patch("openai.OpenAI") as api:
            self.at.run()
            entry = next(attrs for tag, attrs in Document(self.markup()).elements if tag == "a" and attrs.get("aria-label") == "The Belief Files")
            self.assertEqual(entry["target"], "_self")
            self.at.query_params.update({k: v[-1] for k, v in parse_qs(urlsplit(entry["href"]).query).items()})
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertIn('id="bf-title">The Belief Files', self.markup())
            self.at.query_params["case"] = "002"
            for section, label, _ in CHAPTERS:
                self.at.query_params["section"] = section
                self.at.run()
                self.assertFalse(self.at.exception, section)
                self.assertIn('aria-label="' + label + '"', self.markup())
                self.assertEqual(len(self.at.get("download_button")), 1)
            self.at.query_params["v"] = "home"
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertNotIn("case=", unescape(self.markup()))
            self.assertNotIn("section=", unescape(self.markup()))
            api.return_value.chat.completions.create.assert_not_called()

    def test_unknown_case_recovers_to_the_library(self):
        self.at.query_params.update({"v": "belief", "case": "../../private", "section": "unknown"})
        self.at.run()
        self.assertFalse(self.at.exception)
        self.assertIn('id="bf-title">The Belief Files', self.markup())
        self.assertEqual(len(self.at.get("download_button")), 0)


if __name__ == "__main__":
    unittest.main()
