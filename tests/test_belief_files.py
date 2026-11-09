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
    CASE_MARKDOWN, CASE_PDF, CHAPTERS, CASE_FILES, COLLECTION_PLAN, case_href, inline_html,
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

    def test_collection_order_intro_and_all_download_assets(self):
        doc = Document(library_html(href, "https://beyondthemessage.org/the-belief-files/?edition=1"))
        cards = [attrs for tag, attrs in doc.elements if tag == "a" and attrs.get("class", "").startswith("bf-case")]
        self.assertEqual(len(cards), 14)
        self.assertEqual([urlsplit(card["href"]).fragment for card in cards[:2]], ["tbf-intro", "tbf-first-vision"])
        self.assertTrue(all(parse_qs(urlsplit(card["href"]).query) == {"edition": ["1"]} for card in cards[:2]))
        self.assertEqual([parse_qs(urlsplit(card["href"]).query)["case"][0] for card in cards[2:]], [f"{n:03}" for n in range(2, 13)] + ["conversation"])
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
            self.assertIn('id="source-' + str(case["sources"]) + '"', invalid)
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

    def test_exaltation_preserves_historical_limits_and_real_christian_theosis(self):
        evidence = Document(reader_html(href, "evidence", case_id="004")).text
        witnesses = Document(reader_html(href, "witnesses", case_id="004")).text
        explanations = Document(reader_html(href, "explanations", case_id="004")).text
        scripture = Document(reader_html(href, "scripture", case_id="004")).text
        self.assertIn("six surviving individual accounts", evidence)
        self.assertIn("The same work also affirms God's creation of the universe from nothing", evidence)
        self.assertIn("a canonical section", witnesses)
        self.assertIn("does not prove that Smith consciously fabricated revelation", explanations)
        self.assertIn("referents in Psalm 82 are debated", scripture)
        self.assertIn("LDS interpreters distinguish marriages made after resurrection", scripture)

    def test_definitive_index_separates_intro_twelve_cases_and_closing_guide(self):
        self.assertEqual([number for number, _ in COLLECTION_PLAN], ["00"] + [f"{n:03}" for n in range(1, 13)])
        doc = Document(library_html(href))
        self.assertIn("12 case files, and a separate closing Christian conversation guide", doc.text)
        self.assertIn("The Christian conversation guide follows Case 012", doc.text)
        self.assertIn("Plural Marriage in Kirtland and Nauvoo", doc.text)
        self.assertIn("Race and the Priesthood", doc.text)
        for tag, attrs in doc.elements:
            if tag == "a":
                params = parse_qs(urlsplit(attrs["href"]).query)
                if "case" in params:
                    self.assertIn(params["case"][0], CASE_FILES)

    def test_dna_qualifications_and_recent_research_remain_visible(self):
        evidence = Document(reader_html(href, "evidence", case_id="005")).text
        assessment = Document(reader_html(href, "assessment", case_id="005")).text
        sources = Document(reader_html(href, "sources", case_id="005", source="20")).text
        self.assertIn("A 2026 Nature study adds 128", evidence)
        self.assertIn("not automatically evidence for a migration from Jerusalem around 600 BC", evidence)
        self.assertIn("every possible ancestor or tiny migration has been excluded", assessment)
        self.assertIn("The evolutionary history and unique genetic diversity", sources)
        self.assertIn("All 20 sources", sources)

    def test_conversation_guide_is_separate_from_numbered_investigations(self):
        guide = Document(reader_html(href, case_id="conversation"))
        self.assertIn("Christian conversation guide", guide.text)
        self.assertIn("Start Here", guide.text)
        self.assertNotIn("Case File conversation", guide.text)
        self.assertNotIn("Case File 013", guide.text)
        self.assertNotIn("Historical investigation and biblical assessment", guide.text)
        self.assertIn("All fourteen resources are now available", Document(library_html(href)).text)
        self.assertNotIn("draft is prepared", Document(library_html(href)).text)

    def test_conversation_guide_preserves_context_and_honest_practice(self):
        clarify = Document(reader_html(href, "clarify", case_id="conversation")).text
        gospel = Document(reader_html(href, "gospel", case_id="conversation")).text
        practice = Document(reader_html(href, "practice", case_id="conversation")).text
        questions = Document(reader_html(href, "questions", case_id="conversation")).text
        self.assertIn("grace is freely given and cannot be earned", clarify)
        self.assertIn("evangelical explanation", gospel)
        self.assertIn("Romans 4:1–8 and James 2:14–26", gospel)
        self.assertIn("illustrative examples, not quotations from real people", practice)
        self.assertIn("A repeated formula does not itself establish conversion", practice)
        self.assertIn("If the person says they do not want to discuss religion, honor that request", questions)

    def test_priesthood_retains_distinct_authority_and_historical_context(self):
        evidence = Document(reader_html(href, "evidence", case_id="006")).text
        witnesses = Document(reader_html(href, "witnesses", case_id="006")).text
        scripture = Document(reader_html(href, "scripture", case_id="006")).text
        self.assertIn("not claim independent inspection of the archival original", evidence)
        self.assertIn("forbidden to pray for sick people", evidence)
        self.assertIn("Taylor said the earlier ordination did not confer priesthood", witnesses)
        self.assertIn("holding a portion of priesthood in connection with their husbands", witnesses)
        self.assertIn("Christians interpret them alongside", scripture)


    def test_mother_reader_keeps_dates_revelation_and_biblical_context(self):
        evidence = Document(reader_html(href, "evidence", case_id="007")).text
        scripture = Document(reader_html(href, "scripture", case_id="007")).text
        sources = Document(reader_html(href, "sources", case_id="007", source="5")).text
        self.assertIn("published seventy-two years later", evidence)
        self.assertIn("nor does it demonstrate that she waited seventy-two years to tell it", evidence)
        self.assertIn("describes the doctrine as coming through revelation", evidence)
        self.assertIn("not an original Smith-era record", Document(reader_html(href, "sources", case_id="007", source="9")).text)
        self.assertIn("An image of motherly care and a distinct Heavenly Mother are different claims", scripture)
        self.assertIn("A transmitted recollection", sources)
        self.assertIn("All 19 sources", sources)

    def test_violence_reader_retains_responsibility_and_native_evidence_limits(self):
        evidence = Document(reader_html(href, "evidence", case_id="008")).text
        explanations = Document(reader_html(href, "explanations", case_id="008")).text
        scripture = Document(reader_html(href, "scripture", case_id="008")).text
        self.assertIn("Sequence alone therefore does not prove", evidence)
        self.assertIn("The missing incoming letter limits reconstruction", evidence)
        self.assertIn("not newly discovered 1857 eyewitness depositions", evidence)
        self.assertIn("does not establish that Mountain Meadows was a ritual execution", evidence)
        self.assertIn("does not establish an authenticated direct order from Young", explanations)
        self.assertIn("Civil punishment and the saving atonement of Christ are different categories", scripture)
        sources = Document(reader_html(href, "sources", case_id="008", source="15")).text
        self.assertIn("We Shall Remain: The Paiute", sources)
        self.assertIn("All 22 sources", sources)


    def test_nauvoo_keeps_transmission_consent_and_late_testimony_limits(self):
        evidence = Document(reader_html(href, "evidence", case_id="009")).text
        witnesses = Document(reader_html(href, "witnesses", case_id="009")).text
        self.assertIn("1912 typescript", evidence)
        self.assertIn("The original is not extant", evidence)
        self.assertIn("fourteen", evidence.lower())
        self.assertIn("not independent", witnesses)

    def test_utah_families_keeps_denominators_and_womens_distinct_accounts(self):
        evidence = Document(reader_html(href, "evidence", case_id="010")).text
        self.assertIn("Neither says half of Utah's husbands", evidence)
        self.assertIn("not a confidential poll", evidence)
        self.assertIn("does not prove that every plural wife was impoverished", evidence)
        self.assertIn("continuing marital relations", evidence)

    def test_manifesto_distinguishes_new_unions_cohabitation_and_support(self):
        evidence = Document(reader_html(href, "evidence", case_id="011")).text
        self.assertIn("Smoot himself was a monogamist", evidence)
        self.assertIn("September 24", evidence)
        self.assertIn("public release on September 25", evidence)
        self.assertIn("possibility of excommunication", Document(reader_html(href, case_id="011")).text)
        self.assertIn("both were excommunicated immediately", evidence)

    def test_race_preserves_womens_access_primary_voices_and_announcement_dates(self):
        overview = Document(reader_html(href, case_id="012")).text
        evidence = Document(reader_html(href, "evidence", case_id="012")).text
        self.assertIn("Black women and men", overview)
        self.assertIn("contemporary certificate-book copy", evidence)
        self.assertIn("adoption as a daughter", evidence)
        self.assertIn("media release on June 9", evidence)
        self.assertIn("does not attribute a formal apology", evidence)
        self.assertNotIn("Planned case files", Document(library_html(href)).text)


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

    def test_exaltation_reader_sections_source_focus_and_own_pdf(self):
        self.at.query_params.update({"v": "belief", "case": "004"})
        with patch("openai.OpenAI") as api, patch("streamlit.download_button", wraps=st.download_button) as download:
            for section, label, _ in CASE_FILES["004"]["chapters"]:
                self.at.query_params["section"] = section
                self.at.run()
                self.assertFalse(self.at.exception, section)
                self.assertIn('id="bf-title">Becoming Like God', self.markup())
                self.assertIn('aria-label="' + label + '"', self.markup())
                self.assertEqual(len(self.at.get("download_button")), 1)
                self.assertEqual(download.call_args.kwargs["file_name"], "Case_File_004_Becoming_Like_God.pdf")
                self.assertEqual(download.call_args.kwargs["data"], CASE_FILES["004"]["pdf"].read_bytes())
            self.at.query_params.update({"section": "sources", "source": "15"})
            self.at.run()
            self.assertIn('aria-label="Referenced source 15"', self.markup())
            self.assertIn("On the Incarnation", self.markup())
            self.assertNotIn("Joseph Coe", self.markup())
            api.return_value.chat.completions.create.assert_not_called()

    def test_new_cases_direct_entry_every_section_distinct_sources_and_pdf(self):
        with patch("openai.OpenAI") as api, patch("streamlit.download_button", wraps=st.download_button) as download:
            for case_id in ("005", "006", "007", "008", "009", "010", "011", "012", "conversation"):
                case = CASE_FILES[case_id]
                self.at.query_params.update({"v": "belief", "case": case_id})
                for section, label, _ in case["chapters"]:
                    self.at.query_params["section"] = section
                    self.at.run()
                    self.assertFalse(self.at.exception, (case_id, section))
                    self.assertIn('id="bf-title">' + case["title"], self.markup())
                    self.assertIn('aria-label="' + label + '"', self.markup())
                    self.assertEqual(len(self.at.get("download_button")), 1)
                    self.assertEqual(download.call_args.kwargs["file_name"], case["download_name"])
                    self.assertEqual(download.call_args.kwargs["data"], case["pdf"].read_bytes())
                self.at.query_params.update({"section": "sources", "source": str(case["sources"])})
                self.at.run()
                self.assertIn('aria-label="Referenced source ' + str(case["sources"]) + '"', self.markup())
                self.assertIn("All " + str(case["sources"]) + " sources", self.markup())
            api.return_value.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
