import copy
import json
from pathlib import Path
import sqlite3
import unittest

from scripts.import_catalog import import_catalog


class ImportCatalogTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')
        self.addCleanup(self.connection.close)
        self.connection.executescript('''
            CREATE TABLE artists (_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE albums (_id INTEGER PRIMARY KEY, name TEXT NOT NULL, artist INTEGER);
            CREATE TABLE songs (_id INTEGER PRIMARY KEY, track INTEGER, title TEXT NOT NULL, album INTEGER);
            INSERT INTO artists VALUES (12, 'Original Artist');
            INSERT INTO albums VALUES (20, 'Original Album', 12);
            INSERT INTO songs VALUES (30, 1, 'Original Song', 20);
        ''')
        self.catalog = {'artists': [{'name': 'Beyoncé', 'albums': [
            {'name': 'Example Album', 'songs': [{'title': 'Example Song', 'track': 2}]}]}]}

    def test_adds_complete_hierarchy_and_preserves_original(self):
        self.assertEqual(import_catalog(self.connection, self.catalog), {'artists': 1, 'albums': 1, 'songs': 1})
        rows = self.connection.execute('''SELECT artists.name, albums.name, songs.title, songs.track
            FROM artists JOIN albums ON albums.artist=artists._id
            JOIN songs ON songs.album=albums._id ORDER BY artists._id''').fetchall()
        self.assertEqual(rows, [('Original Artist', 'Original Album', 'Original Song', 1),
                                ('Beyoncé', 'Example Album', 'Example Song', 2)])
        self.assertEqual(self.connection.execute('SELECT * FROM songs WHERE _id=30').fetchone(),
                         (30, 1, 'Original Song', 20))

    def test_reruns_and_spelling_variants_skip_existing_artist(self):
        import_catalog(self.connection, self.catalog)
        self.catalog['artists'][0]['name'] = 'BEYONCE'
        self.assertEqual(import_catalog(self.connection, self.catalog), {'artists': 0, 'albums': 0, 'songs': 0})
        self.assertEqual(self.connection.execute('SELECT COUNT(*) FROM songs').fetchone()[0], 2)

    def test_expansion_fills_existing_artist_and_corrects_track_without_changing_id(self):
        import_catalog(self.connection, self.catalog)
        song_id = self.connection.execute("SELECT _id FROM songs WHERE title='Example Song'").fetchone()[0]
        expanded = copy.deepcopy(self.catalog)
        expanded['artists'][0]['albums'][0]['songs'] = [
            {'title': 'Opening', 'track': 1}, {'title': 'Example Song', 'track': 3}]
        expanded['artists'][0]['albums'].append(
            {'name': 'Another Album', 'songs': [{'title': 'Another Song', 'track': 1}]})
        self.assertEqual(import_catalog(self.connection, expanded, expand_existing=True),
                         {'artists': 0, 'albums': 1, 'songs': 2})
        self.assertEqual(self.connection.execute('SELECT track FROM songs WHERE _id=?', (song_id,)).fetchone(), (3,))
        self.assertEqual(import_catalog(self.connection, expanded, expand_existing=True),
                         {'artists': 0, 'albums': 0, 'songs': 0})

    def test_expansion_preserves_repeated_titles_at_different_track_positions(self):
        songs = self.catalog['artists'][0]['albums'][0]['songs']
        songs.append({'title': 'Example Song', 'track': 4})
        self.assertEqual(import_catalog(self.connection, self.catalog, expand_existing=True)['songs'], 2)
        self.assertEqual(import_catalog(self.connection, self.catalog, expand_existing=True)['songs'], 0)
        self.assertEqual(self.connection.execute("SELECT track FROM songs WHERE title='Example Song' ORDER BY track").fetchall(), [(2,), (4,)])

    def test_complete_album_flag_rejects_truncated_tracklist(self):
        album = self.catalog['artists'][0]['albums'][0]
        album.update(complete_audio_tracklist=True, source_track_count=10, excluded_music_videos=0)
        with self.assertRaisesRegex(ValueError, 'Incomplete album tracklist'):
            import_catalog(self.connection, self.catalog)

    def test_invalid_data_is_rejected_before_any_write(self):
        invalid = copy.deepcopy(self.catalog)
        invalid['artists'].append({'name': 'Invalid', 'albums': [{'name': 'Empty', 'songs': []}]})
        with self.assertRaises(ValueError):
            import_catalog(self.connection, invalid)
        self.assertEqual(self.connection.execute('SELECT COUNT(*) FROM artists').fetchone()[0], 1)

    def test_database_failure_rolls_back_whole_import(self):
        self.connection.execute('''CREATE TRIGGER reject_new_song BEFORE INSERT ON songs
                                  BEGIN SELECT RAISE(ABORT, 'test failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            import_catalog(self.connection, self.catalog)
        for table in ('artists', 'albums', 'songs'):
            self.assertEqual(self.connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 1)


class CatalogSnapshotTests(unittest.TestCase):
    def test_drake_has_all_eleven_studio_albums_and_complete_audio_tracklists(self):
        catalog = json.loads((Path(__file__).resolve().parents[1] / 'data/catalog_additions.json').read_text(encoding='utf-8'))
        drake = next(a for a in catalog['artists'] if a['name'] == 'Drake')
        studios = {a['name'] for a in drake['albums'] if a.get('release_type') == 'studio'}
        self.assertEqual(studios, {'Thank Me Later', 'Take Care (Deluxe Version)',
            'Nothing Was the Same (Deluxe)', 'Views', 'Scorpion', 'Certified Lover Boy',
            'Honestly, Nevermind', 'For All The Dogs', 'ICEMAN', 'MAID OF HONOUR', 'HABIBTI'})
        for album in drake['albums']:
            self.assertTrue(album['complete_audio_tracklist'])
            self.assertEqual(len(album['songs']), album['source_track_count'] - album['excluded_music_videos'])
            self.assertEqual([s['track'] for s in album['songs']], list(range(1, len(album['songs']) + 1)))

    def test_checked_in_snapshot_imports_and_reruns_without_duplicates(self):
        catalog = json.loads((Path(__file__).resolve().parents[1] / 'data/catalog_additions.json').read_text(encoding='utf-8'))
        connection = sqlite3.connect(':memory:')
        self.addCleanup(connection.close)
        connection.executescript('''
            CREATE TABLE artists (_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE albums (_id INTEGER PRIMARY KEY, name TEXT NOT NULL, artist INTEGER);
            CREATE TABLE songs (_id INTEGER PRIMARY KEY, track INTEGER, title TEXT NOT NULL, album INTEGER);
        ''')
        result = import_catalog(connection, catalog)
        self.assertEqual(result['artists'], len(catalog['artists']))
        self.assertEqual(result['albums'], sum(len(a['albums']) for a in catalog['artists']))
        self.assertEqual(result['songs'], sum(len(b['songs']) for a in catalog['artists'] for b in a['albums']))
        self.assertEqual(import_catalog(connection, catalog), {'artists': 0, 'albums': 0, 'songs': 0})


if __name__ == '__main__':
    unittest.main()
