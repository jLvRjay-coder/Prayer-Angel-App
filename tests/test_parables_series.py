"""Season 2 dates, complete readings, and published email output."""
from datetime import date, timedelta
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

from daily_encouragement import DAILY_MESSAGES, default_message, email_preview, email_preview_html, message_by_key

ROOT = Path(__file__).resolve().parents[1]
SERIES_ID = 'whats-in-the-book-the-stories-jesus-told'

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

class ParablesSeriesTests(unittest.TestCase):
    def setUp(self):
        self.messages = [m for m in DAILY_MESSAGES if m.get('series_id') == SERIES_ID]

    def test_ninety_days_follow_the_existing_calendar_without_replacing_it(self):
        self.assertEqual(len(self.messages), 90)
        self.assertEqual(DAILY_MESSAGES[138]['id'], 'witb-s1-day-48')
        self.assertEqual(DAILY_MESSAGES[138]['date'], '2027-03-04')
        self.assertEqual(self.messages[0]['previous_message_id'], 'witb-s1-day-48')
        self.assertEqual([m['date'] for m in self.messages], [
            (date(2027, 3, 5) + timedelta(days=i)).isoformat() for i in range(90)
        ])
        self.assertEqual(self.messages[-1]['date'], '2027-06-02')
        self.assertEqual(default_message(date(2027, 3, 4))['id'], 'witb-s1-day-48')
        self.assertEqual(default_message(date(2027, 3, 5))['id'], 'witb-s2-day-01')
        self.assertEqual(default_message(date(2027, 6, 3))['id'], 'witb-s2-day-90')

    def test_approved_roadmap_order_and_passages_are_preserved(self):
        roadmap = json.loads((ROOT / 'docs/parables-series-roadmap.json').read_text())
        planned = [d for w in roadmap['weeks'] for d in w['days']]
        self.assertEqual([m['title'] for m in self.messages], [d['title'] for d in planned])
        self.assertEqual([m['reference'] for m in self.messages], [d['reading'] for d in planned])
        self.assertEqual([m['series_day'] for m in self.messages], list(range(1,91)))

    def test_every_selected_kjv_verse_is_present_and_the_key_verse_is_complete(self):
        for message in self.messages:
            with self.subTest(day=message['series_day']):
                reference = re.fullmatch(r'.+? (\d+):([\d, -]+)', message['reference'])
                self.assertIsNotNone(reference)
                expected = []
                for span in reference[2].split(','):
                    numbers = [int(n) for n in span.strip().split('-')]
                    expected.extend(range(numbers[0], numbers[-1]+1))
                actual = [int(re.match(r'^(\d+) ', p)[1]) for p in message['reading'].split('\n\n')]
                self.assertEqual(actual, expected)
                key_number = int(message['verse_reference'].split(':')[-1])
                key_reading = next(p.split(' ',1)[1] for p in message['reading'].split('\n\n')
                                   if int(p.split(' ',1)[0]) == key_number)
                self.assertEqual(message['verse'], key_reading)
                self.assertNotIn('…', message['reading'])
                self.assertNotIn('…', message['verse'])

    def test_every_day_has_a_full_distinct_reflection_and_complete_email_output(self):
        self.assertEqual(len({m['devotional'] for m in self.messages}), 90)
        for message in self.messages:
            with self.subTest(day=message['series_day']):
                prose = ' '.join(message[k] for k in ('devotional','reflection','prayer'))
                self.assertGreaterEqual(len(prose.split()),450)
                self.assertLessEqual(len(prose.split()),650)
                self.assertGreaterEqual(len(message['devotional'].split('\n\n')),7)
                self.assertTrue(message['approved_for_delivery'])
                self.assertTrue(message['reflection'].endswith('?'))
                self.assertTrue(message['prayer'].endswith('Amen.'))
                connection = message['connection'].replace('First ', '1 ').replace('Second ', '2 ')
                self.assertIn(message['connection_reference'], connection)
                self.assertEqual(message_by_key(message['id']),message_by_key(message['date']))
                plain = email_preview(message)
                rendered = Text(email_preview_html(message)).value
                for field in ('reading','devotional','reflection','prayer'):
                    self.assertIn(message[field],plain)
                    for paragraph in message[field].split('\n\n'):
                        self.assertIn(' '.join(paragraph.split()),rendered)
                for phrase in message['emphasis']:
                    self.assertIn(phrase,message['devotional'])

    def test_series_links_and_closing_reflections_are_consistent(self):
        for index, message in enumerate(self.messages):
            with self.subTest(day=index+1):
                expected_previous = 'witb-s1-day-48' if index==0 else self.messages[index-1]['id']
                expected_next = None if index==89 else self.messages[index+1]['id']
                self.assertEqual(message['previous_message_id'],expected_previous)
                self.assertEqual(message['next_message_id'],expected_next)
        self.assertTrue(all(m['series_part']=='Reflection' for m in self.messages[-6:]))

if __name__ == '__main__':
    unittest.main()
