from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlsplit

from home_hub import DEFAULT_BELIEF_FILES_URL, belief_files_url, bottom_nav_html, home_html


class Links(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.links = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


class HomeHubTests(unittest.TestCase):
    def test_published_belief_files_is_visible_on_home_and_navigation(self):
        home = Links(home_html(lambda view: '?v=' + view))
        nav = Links(bottom_nav_html('angel', lambda view: '?v=' + view))
        self.assertEqual(sum(link['href'] == DEFAULT_BELIEF_FILES_URL for link in home.links), 1)
        self.assertEqual(sum(link['href'] == DEFAULT_BELIEF_FILES_URL for link in nav.links), 1)
        self.assertEqual(len(nav.links), 5)
        self.assertIn('How it works', home_html(lambda view: '?v=' + view))

    def test_resource_links_keep_internal_routes_and_external_destinations(self):
        href = lambda view: '?sid=existing-session&theme=light&v=' + view
        markup = Links(home_html(href, show_signup=True))
        for view in ('home', 'about', 'angel', 'daily', 'bible', 'email'):
            self.assertTrue(any(parse_qs(urlsplit(link['href']).query).get('v') == [view] for link in markup.links))
        for link in markup.links:
            if link['href'].startswith('https:'):
                self.assertEqual(link.get('target'), '_blank')
                self.assertIn('noopener', link.get('rel', ''))
                self.assertNotIn('sid=', link['href'])
            else:
                self.assertEqual(link.get('target'), '_self')

    def test_signup_visibility_follows_existing_setting(self):
        self.assertNotIn('?v=email', home_html(lambda view: '?v=' + view))
        self.assertIn('?v=email', home_html(lambda view: '?v=' + view, show_signup=True))

    def test_invalid_override_falls_back_to_public_page(self):
        for value in ('', None, 'http://example.org/', 'javascript:alert(1)', 'https://user:password@example.org/', 'https://[bad'):
            with self.subTest(value=value):
                self.assertEqual(belief_files_url(value), DEFAULT_BELIEF_FILES_URL)
        self.assertEqual(belief_files_url('https://example.org/studies/'), 'https://example.org/studies/')

    def test_urls_are_escaped_and_home_is_not_an_active_chat(self):
        markup = home_html(lambda view: '?v=' + view + '&label="quoted"')
        self.assertIn('&amp;label=&quot;quoted&quot;', markup)
        home_nav = Links(bottom_nav_html('home', lambda view: '?v=' + view))
        self.assertTrue(all('aria-current' not in link for link in home_nav.links))
        chat_nav = Links(bottom_nav_html('angel', lambda view: '?v=' + view))
        self.assertEqual(sum(link.get('aria-current') == 'page' for link in chat_nav.links), 1)


if __name__ == '__main__':
    unittest.main()
