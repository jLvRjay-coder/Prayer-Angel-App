"""Collection isolation, complete published content, and legacy route coverage."""

from html import unescape
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from streamlit.testing.v1 import AppTest

from belief_files import (
    CASE_FILES, case_href, collection_href, collections_html, islam_library_html,
    manuscript_sections, reader_html,
)
from belief_islam import ISLAM_CASE_FILES, RESEARCH_PDF
from deploy_space_preview import RUNTIME_FILES
from test_belief_files import Document, href


ROOT = Path(__file__).resolve().parents[1]


class CollectionContentTests(unittest.TestCase):
    def test_chooser_and_collection_links_do_not_forward_old_reader_or_email_state(self):
        stale = lambda view: href(view) + "&collection=islam&case=001&section=sources&source=Q1"
        document = Document(collections_html(stale))
        cards = [attrs for tag, attrs in document.elements if tag == "a" and attrs.get("class", "").startswith("bf-case")]
        self.assertEqual(len(cards), 2)
        self.assertEqual([parse_qs(urlsplit(card["href"]).query)["collection"] for card in cards], [["lds"], ["islam"]])
        for card in cards:
            query = parse_qs(urlsplit(card["href"]).query)
            self.assertEqual(set(query), {"sid", "theme", "v", "collection"})
            self.assertEqual(card["target"], "_self")
        self.assertEqual(parse_qs(urlsplit(collection_href(stale)).query),
                         {"sid": ["existing-session"], "theme": ["light"], "v": ["belief"]})

    def test_islam_landing_only_offers_published_readers(self):
        document = Document(islam_library_html(href))
        links = [parse_qs(urlsplit(attrs["href"]).query) for tag, attrs in document.elements if tag == "a"]
        self.assertEqual([link["case"][0] for link in links if "case" in link], ["00", "001"])
        self.assertTrue(all(link.get("collection") == ["islam"] for link in links if "case" in link))
        self.assertIn("as they are completed", document.text)
        self.assertIn("Research Packet 001", document.text)

    def test_every_published_section_and_source_is_preserved_and_ships(self):
        for case_id, case in ISLAM_CASE_FILES.items():
            sections = manuscript_sections(case_id, collection="islam")
            mapped = [name for _, _, names in case["chapters"] for name in names]
            self.assertEqual(len(mapped), len(set(mapped)))
            self.assertEqual(set(mapped), set(sections) - {"Collection notes"})
            registry = re.findall(r"^\*\*([A-Z]+\d+)\*\*", sections["Sources and reading"], re.M)
            self.assertEqual(registry, list(case["source_ids"]))
            self.assertEqual(len(registry), case["sources"])
            all_sources = Document(reader_html(href, "sources", case_id=case_id, collection="islam"))
            self.assertEqual([attrs["id"] for _, attrs in all_sources.elements if attrs.get("class") == "bf-source"],
                             ["source-" + code for code in registry])
            for path in (case["markdown"], case["pdf"]):
                self.assertIn(path.name, RUNTIME_FILES)
                self.assertTrue(path.is_file())
            self.assertTrue(case["pdf"].read_bytes().startswith(b"%PDF-"))
            self.assertNotIn("chatgpt.com/library", case["markdown"].read_text())
        self.assertIn(RESEARCH_PDF.name, RUNTIME_FILES)
        self.assertTrue(RESEARCH_PDF.read_bytes().startswith(b"%PDF-"))
        self.assertIn("belief_islam.py", RUNTIME_FILES)

    def test_all_citations_focus_the_right_source_within_the_same_case_and_collection(self):
        for case_id, case in ISLAM_CASE_FILES.items():
            for key, label, _ in case["chapters"]:
                document = Document(reader_html(href, key, case_id=case_id, collection="islam"))
                self.assertEqual(sum(attrs.get("aria-current") == "page" for _, attrs in document.elements), 1)
                for tag, attrs in document.elements:
                    if tag != "a" or urlsplit(attrs["href"]).scheme:
                        continue
                    query = parse_qs(urlsplit(attrs["href"]).query)
                    self.assertEqual(query["collection"], ["islam"])
                    if attrs.get("class") == "bf-citation":
                        self.assertEqual(query["case"], [case_id])
                        self.assertEqual(query["section"], ["sources"])
                        self.assertIn(query["source"][0], case["source_ids"])
            for code in case["source_ids"]:
                focused = reader_html(href, "sources", case_id=case_id, source=code, collection="islam")
                self.assertIn('aria-label="Referenced source ' + code + '"', focused)
                self.assertIn("All " + str(case["sources"]) + " sources", Document(focused).text)
            invalid = reader_html(href, "sources", case_id=case_id, source="../Q1", collection="islam")
            self.assertNotIn('class="bf-source-focus"', invalid)

    def test_legacy_cases_keep_their_meaning_and_islam_sources_do_not_leak_to_lds(self):
        stale = lambda view: href(view) + "&collection=islam&case=001&source=Q1"
        for case_id in CASE_FILES:
            query = parse_qs(urlsplit(case_href(stale, case_id=case_id)).query)
            self.assertEqual(query["case"], [case_id])
            self.assertNotIn("collection", query)
            self.assertNotIn("source", query)
        islam = Document(reader_html(href, "sources", case_id="001", source="Q1", collection="islam")).text
        lds = Document(reader_html(href, "sources", case_id="002", source="1")).text
        self.assertIn("Qur'an 33:40", islam)
        self.assertNotIn("Qur'an 33:40", lds)


class CollectionAppTests(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)

    def tearDown(self):
        sid = self.at.query_params.get("sid", "")
        if sid:
            (ROOT / ".btm_sessions" / f"{sid}.json").unlink(missing_ok=True)

    def markup(self):
        return "\n".join(element.proto.body for element in self.at.get("html"))

    def test_chooser_islam_every_section_download_and_return_to_lds(self):
        with patch("openai.OpenAI") as api, patch("streamlit.download_button") as download:
            self.at.query_params.update({"v": "belief"})
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertIn("Choose a collection", self.markup())
            self.at.query_params["collection"] = "islam"
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertEqual(download.call_args.kwargs["data"], RESEARCH_PDF.read_bytes())
            for case_id, case in ISLAM_CASE_FILES.items():
                self.at.query_params["case"] = case_id
                for key, label, _ in case["chapters"]:
                    self.at.query_params["section"] = key
                    self.at.run()
                    self.assertFalse(self.at.exception, (case_id, key))
                    self.assertIn('aria-label="' + label + '"', self.markup())
                    self.assertEqual(download.call_args.kwargs["data"], case["pdf"].read_bytes())
                    self.assertEqual(download.call_args.kwargs["file_name"], case["download_name"])
            self.at.query_params.update({"case": "001", "section": "sources", "source": "H95"})
            self.at.run()
            self.assertIn('aria-label="Referenced source H95"', self.markup())
            self.at.query_params.update({"v": "home"})
            self.at.run()
            markup = unescape(self.markup())
            self.assertNotIn("collection=", markup)
            self.assertNotIn("case=", markup)
            self.assertIn("Explore religious claims through history, evidence, and Scripture.", markup)
            self.at.query_params.clear()
            self.at.query_params.update({"v": "belief", "case": "002"})
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertIn('id="bf-title">The Book of Mormon Translation', self.markup())
            api.return_value.chat.completions.create.assert_not_called()

    def test_unknown_scopes_and_unpublished_case_ids_recover_without_opening_another_collection(self):
        for params, expected in (({"collection": "untrusted", "case": "002"}, "Choose a collection"),
                                 ({"collection": "islam", "case": "002"}, "The collection is growing"),
                                 ({"collection": "islam", "case": "conversation"}, "The collection is growing"),
                                 ({"collection": "lds", "case": "001"}, "The First Vision")):
            self.at.query_params.clear()
            self.at.query_params.update({"v": "belief", **params})
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertIn(expected, self.markup())
            self.assertNotIn('id="bf-title">The Book of Mormon Translation', self.markup())


if __name__ == "__main__":
    unittest.main()
