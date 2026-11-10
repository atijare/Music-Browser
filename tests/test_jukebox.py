import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from jukebox import Library, open_youtube, youtube_search_url


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        database = Path(self.temp.name) / 'catalog.sqlite'
        connection = sqlite3.connect(database)
        connection.executescript('''
            CREATE TABLE artists (_id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE albums (_id INTEGER PRIMARY KEY, name TEXT, artist INTEGER);
            CREATE TABLE songs (_id INTEGER PRIMARY KEY, title TEXT, album INTEGER, track INTEGER);
            INSERT INTO artists VALUES (0, 'First'), (1, 'Second'), (2, '100% Band');
            INSERT INTO albums VALUES (0, 'Same album', 0), (1, 'Same album', 1);
            INSERT INTO songs VALUES (0, 'Same song', 0, 2), (1, 'Same song', 1, 1),
                                     (2, 'Opening', 0, 1);
        ''')
        connection.close()
        self.library = Library(database)
        self.addCleanup(self.library.close)

    def test_hierarchy_uses_ids_and_track_order(self):
        self.assertEqual([r['_id'] for r in self.library.albums(0)], [0])
        self.assertEqual([r['_id'] for r in self.library.songs(0)], [2, 0])
        self.assertEqual([r['_id'] for r in self.library.songs(1)], [1])

    def test_search_is_case_insensitive_and_literal(self):
        self.assertEqual([r['_id'] for r in self.library.artists('FIRST')], [0])
        self.assertEqual([r['_id'] for r in self.library.artists('%')], [2])
        self.assertEqual(self.library.artists("' OR 1=1 --"), [])

    def test_catalog_is_not_modified(self):
        tables = self.library.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        self.assertEqual([row['name'] for row in tables], ['albums', 'artists', 'songs'])


class YouTubeTests(unittest.TestCase):
    def test_search_encodes_artist_and_song_as_one_parameter(self):
        artist = 'AC/DC & Beyoncé'
        song = "What's up? #1 + 100%"
        url = urlparse(youtube_search_url(artist, song))
        self.assertEqual(url.scheme, 'https')
        self.assertEqual(url.netloc, 'www.youtube.com')
        self.assertEqual(url.path, '/results')
        self.assertEqual(parse_qs(url.query), {'search_query': [f'{artist} {song}']})
        self.assertEqual(url.fragment, '')

    @patch('jukebox.webbrowser.open', return_value=True)
    def test_opens_search_in_browser(self, browser):
        url = open_youtube('Artist', 'Song')
        browser.assert_called_once_with(youtube_search_url('Artist', 'Song'), new=2)
        self.assertEqual(url, youtube_search_url('Artist', 'Song'))

    @patch('jukebox.webbrowser.open', return_value=False)
    def test_failed_browser_is_reported(self, browser):
        with self.assertRaisesRegex(RuntimeError, 'Copy the search link'):
            open_youtube('Artist', 'Song')


if __name__ == '__main__':
    unittest.main()
