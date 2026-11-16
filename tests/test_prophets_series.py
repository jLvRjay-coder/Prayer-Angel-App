"""Published Prophets calendar, preserved content, and complete reader output."""
from collections import Counter
from datetime import date, timedelta
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

from daily_encouragement import DAILY_MESSAGES, default_message, email_preview, email_preview_html, message_by_key

ROOT = Path(__file__).resolve().parents[1]
SERIES_ID = 'whats-in-the-book-the-prophets'
EXISTING_CATALOG_SHA256 = '690d3a664ff70f785076cc6de1fbbe4ed7e8989383e1a1780b0950c3d8c5e67d'
CHECKED_SCRIPTURE_SHA256 = 'c811ccc1950ce8cd02bee1e2b15d11f4a1c777f7f79a4850d6e8a0f097e5d642'


class Text(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.feed(source)

    def handle_data(self, value):
        self.parts.append(value)

    @property
    def value(self):
        return ' '.join(' '.join(self.parts).split())


class ProphetsSeriesTests(unittest.TestCase):
    def setUp(self):
        self.messages = [m for m in DAILY_MESSAGES if m.get('series_id') == SERIES_ID]

    def test_existing_229_entries_are_preserved_exactly(self):
        original = json.dumps(DAILY_MESSAGES[:229], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        self.assertEqual(sha256(original.encode()).hexdigest(), EXISTING_CATALOG_SHA256)

    def test_126_days_follow_parables_and_stop_at_the_new_end(self):
        self.assertEqual(len(self.messages), 126)
        self.assertEqual([m['date'] for m in self.messages], [
            (date(2027, 6, 3) + timedelta(days=i)).isoformat() for i in range(126)
        ])
        self.assertEqual(default_message(date(2027, 6, 2))['id'], 'witb-s2-day-90')
        self.assertEqual(default_message(date(2027, 6, 3))['id'], 'witb-s3-day-001')
        self.assertEqual(default_message(date(2027, 10, 6))['id'], 'witb-s3-day-126')
        self.assertEqual(default_message(date(2027, 10, 7))['id'], 'witb-s3-day-126')

    def test_roadmap_matches_all_titles_readings_dates_and_books(self):
        plan = json.loads((ROOT / 'docs/prophets-series-roadmap.json').read_text())
        self.assertEqual(plan['total_days'], 126)
        self.assertEqual([(m['date'], m['title'], m['reference'], m['series_unit']) for m in self.messages],
                         [(d['date'], d['title'], d['reading'], d['book']) for d in plan['days']])
        self.assertEqual(Counter(m['series_unit'] for m in self.messages), {
            'Introduction': 4, 'Isaiah': 18, 'Jeremiah': 15, 'Lamentations': 5, 'Ezekiel': 15, 'Daniel': 12,
            'Hosea': 7, 'Joel': 4, 'Amos': 5, 'Obadiah': 2, 'Jonah': 4, 'Micah': 6, 'Nahum': 3,
            'Habakkuk': 4, 'Zephaniah': 3, 'Haggai': 3, 'Zechariah': 8, 'Malachi': 4, 'Reflection': 4,
        })

    def test_every_selected_verse_and_complete_key_verse_match_checked_text(self):
        # Frozen after comparison with two independently maintained KJV transcriptions.
        scripture = [(m['reference'], m['reading'], m['verse_reference'], m['verse']) for m in self.messages]
        self.assertEqual(sha256(json.dumps(scripture, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(),
                         CHECKED_SCRIPTURE_SHA256)
        for m in self.messages:
            with self.subTest(day=m['series_day']):
                ref = re.fullmatch(r'.+? (\d+):([\d,-]+)', m['reference'])
                self.assertIsNotNone(ref)
                expected = []
                for span in ref[2].split(','):
                    bounds = list(map(int, span.split('-')))
                    expected.extend(range(bounds[0], bounds[-1] + 1))
                verses = {int(p.split(' ', 1)[0]): p.split(' ', 1)[1] for p in m['reading'].split('\n\n')}
                self.assertEqual(list(verses), expected)
                self.assertEqual(m['verse'], verses[int(m['verse_reference'].split(':')[-1])])
                self.assertNotIn('…', m['reading'])

    def test_every_day_reaches_plain_and_html_email_in_full(self):
        self.assertEqual(len({m['devotional'] for m in self.messages}), 126)
        for m in self.messages:
            with self.subTest(day=m['series_day']):
                count = len(' '.join(m[k] for k in ('devotional', 'reflection', 'prayer')).split())
                self.assertGreaterEqual(count, 450)
                self.assertLessEqual(count, 650)
                self.assertGreaterEqual(len(m['devotional'].split('\n\n')), 7)
                self.assertTrue(m['approved_for_delivery'])
                self.assertTrue(m['reflection'].endswith('?'))
                self.assertTrue(m['prayer'].endswith('Amen.'))
                self.assertIn(m['connection_reference'], m['connection'])
                self.assertEqual(message_by_key(m['id']), message_by_key(m['date']))
                plain, rendered = email_preview(m), Text(email_preview_html(m)).value
                for field in ('reading', 'verse', 'devotional', 'reflection', 'prayer'):
                    self.assertIn(m[field], plain)
                    for paragraph in m[field].split('\n\n'):
                        self.assertIn(' '.join(paragraph.split()), rendered)
                for phrase in m['emphasis']:
                    self.assertIn(phrase, m['devotional'])

    def test_series_links_are_valid_and_closing_readings_remain_distinct(self):
        self.assertEqual([m['series_day'] for m in self.messages], list(range(1, 127)))
        for i, m in enumerate(self.messages):
            previous = 'witb-s2-day-90' if i == 0 else self.messages[i - 1]['id']
            following = None if i == 125 else self.messages[i + 1]['id']
            self.assertEqual(m['previous_message_id'], previous)
            self.assertEqual(m['next_message_id'], following)
        self.assertTrue(all(m['series_part'] == 'Reflection' for m in self.messages[-4:]))

    def test_first_minor_prophet_and_final_readings_render_in_the_app(self):
        from streamlit.testing.v1 import AppTest
        for key in ('witb-s3-day-001', 'witb-s3-day-070', 'witb-s3-day-122', 'witb-s3-day-126'):
            with self.subTest(message=key):
                app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20)
                app.query_params.update({'v': 'daily', 'message': key})
                app.run()
                self.assertFalse(app.exception)
                m = message_by_key(key)
                self.assertEqual(app.subheader[0].value, m['title'])
                rendered = '\n'.join(element.value for element in app.markdown).replace('**', '')
                self.assertIn(m['devotional'], rendered)
                for verse in m['reading'].split('\n\n'):
                    self.assertIn(verse, rendered)
                self.assertEqual(len(app.selectbox[0].options), 355)
                sid = app.query_params.get('sid', '')
                if sid:
                    (ROOT / '.btm_sessions' / f'{sid}.json').unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
