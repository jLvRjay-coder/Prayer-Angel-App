"""Approved case coverage, public references, and real app navigation."""

import os
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
import streamlit as st
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from belief_files import (
    CASE_MARKDOWN, CASE_PDF, CHAPTERS, CASE_FILES, case_href, inline_html,
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
        for case_id, case in CASE_FILES.items():
            sections = manuscript_sections(case_id)
            mapped = [name for _, _, names in case["chapters"] for name in names]
            self.assertEqual(len(mapped), len(set(mapped)))
            self.assertEqual(set(mapped), set(sections) - {"Collection notes"})
            for key, _, names in case["chapters"]:
                document = Document(reader_html(href, key, case_id=case_id))
                for name in names:
                    # Preserve all paragraphs, cells, lists, and qualifications.
                    for line in sections[name].splitlines():
                        text = line.strip()
                        if not text or re.fullmatch(r"[| :\-]+", text):
                            continue
                        text = re.sub(r"^#{2,3}\s+|^\d+\.\s+|^-\s+", "", text)
                        for cell in text.strip("|").split("|"):
                            normalized = Document(inline_html(cell.strip())).text
                            self.assertIn(normalized, document.text, (case_id, key, name))

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
                    self.assertIn(int(parse_qs(url.query)["source"][0]), source_ids)
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

    def test_collection_order_intro_and_both_download_assets(self):
        doc = Document(library_html(href, "https://beyondthemessage.org/the-belief-files/?edition=1"))
        cards = [attrs for tag, attrs in doc.elements if tag == "a" and attrs.get("class", "").startswith("bf-case")]
        self.assertEqual(len(cards), 4)
        self.assertEqual([urlsplit(card["href"]).fragment for card in cards[:2]], ["tbf-intro", "tbf-first-vision"])
        self.assertTrue(all(parse_qs(urlsplit(card["href"]).query) == {"edition": ["1"]} for card in cards[:2]))
        self.assertEqual([parse_qs(urlsplit(card["href"]).query)["case"][0] for card in cards[2:]], ["002", "003"])
        self.assertTrue(all(card["target"] == "_self" for card in cards[2:]))
        for case in CASE_FILES.values():
            self.assertIn(case["markdown"].name, RUNTIME_FILES)
            self.assertIn(case["pdf"].name, RUNTIME_FILES)
            self.assertTrue(case["pdf"].read_bytes().startswith(b"%PDF-"))

    def test_each_case_keeps_its_own_citations_navigation_and_source_focus(self):
        for case_id, case in CASE_FILES.items():
            source_ids = ["source-" + str(i) for i in range(1, case["sources"] + 1)]
            sources = Document(reader_html(href, "sources", case_id=case_id))
            self.assertEqual([attrs["id"] for _, attrs in sources.elements if attrs.get("id", "").startswith("source-")], source_ids)
            for section, _, _ in case["chapters"]:
                doc = Document(reader_html(href, section, case_id=case_id))
                for tag, attrs in doc.elements:
                    if tag != "a" or urlsplit(attrs["href"]).scheme:
                        continue
                    params = parse_qs(urlsplit(attrs["href"]).query)
                    self.assertNotIn("token", params)
                    if "case" in params:
                        self.assertEqual(params["case"], [case_id])
                    if attrs.get("class") == "bf-citation":
                        number = params["source"][0]
                        self.assertIn("source-" + number, source_ids)
                        focused = reader_html(href, "sources", case_id=case_id, source=number)
                        self.assertIn('aria-label="Referenced source ' + number + '"', focused)
            for number in ("1", str(case["sources"])):
                focused = reader_html(href, "sources", case_id=case_id, source=number)
                self.assertIn('aria-label="Referenced source ' + number + '"', focused)
            invalid = reader_html(href, "sources", case_id=case_id, source="../../private")
            self.assertNotIn('class="bf-source-focus"', invalid)
            self.assertIn('id="source-22"', invalid)
        abraham = reader_html(href, "sources", case_id="003", source="13")
        self.assertIn("Joseph Coe", abraham)
        self.assertNotIn("Three Witnesses statement", abraham)

    def test_abraham_distinguishes_surviving_artifacts_missing_sources_and_intent(self):
        overview = Document(reader_html(href, case_id="003")).text
        evidence = Document(reader_html(href, "evidence", case_id="003")).text
        explanations = Document(reader_html(href, "explanations", case_id="003")).text
        self.assertIn("do not, by themselves, establish that Smith knowingly committed fraud", overview)
        self.assertIn("A damaged ancient vignette survives", evidence)
        self.assertIn("its original papyrus is not extant", evidence)
        self.assertIn("Their precise order and role remain contested", evidence)
        self.assertIn("A naturalistic explanation", explanations)
        self.assertIn("An Abrahamic text on missing papyri", explanations)


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
            self.at.query_params.update({"section": "sources", "source": "13"})
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertIn('class="bf-source-focus" aria-label="Referenced source 13"', self.markup())
            self.assertIn("Three Witnesses statement", self.markup())
            self.at.query_params["v"] = "home"
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertNotIn("case=", unescape(self.markup()))
            self.assertNotIn("section=", unescape(self.markup()))
            self.assertNotIn("source=", unescape(self.markup()))
            api.return_value.chat.completions.create.assert_not_called()

    def test_unknown_case_recovers_to_the_library(self):
        self.at.query_params.update({"v": "belief", "case": "../../private", "section": "unknown"})
        self.at.run()
        self.assertFalse(self.at.exception)
        self.assertIn('id="bf-title">The Belief Files', self.markup())
        self.assertEqual(len(self.at.get("download_button")), 0)

    def test_abraham_direct_entry_every_chapter_sources_and_correct_pdf(self):
        self.at.query_params.update({"v": "belief", "case": "003"})
        with patch("openai.OpenAI") as api, patch("streamlit.download_button", wraps=st.download_button) as download:
            for section, label, _ in CASE_FILES["003"]["chapters"]:
                self.at.query_params["section"] = section
                self.at.run()
                self.assertFalse(self.at.exception, section)
                self.assertIn('id="bf-title">The Book of Abraham', self.markup())
                self.assertIn('aria-label="' + label + '"', self.markup())
                downloads = self.at.get("download_button")
                self.assertEqual(len(downloads), 1)
                self.assertEqual(download.call_args.kwargs["file_name"], "Case_File_003_Book_of_Abraham.pdf")
                self.assertEqual(download.call_args.kwargs["data"], CASE_FILES["003"]["pdf"].read_bytes())
            self.at.query_params.update({"section": "sources", "source": "13"})
            self.at.run()
            self.assertIn('aria-label="Referenced source 13"', self.markup())
            self.assertIn("Joseph Coe", self.markup())
            self.at.query_params["case"] = "002"
            self.at.run()
            self.assertIn("Three Witnesses statement", self.markup())
            api.return_value.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
