"""Add missing artists from the checked-in metadata snapshot, without network access."""
import argparse
import json
from pathlib import Path
import sqlite3
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def artist_key(name):
    """Match case, accents and punctuation variants without renaming existing artists."""
    return ''.join(char for char in unicodedata.normalize('NFKD', name).casefold()
                   if char.isalnum())


def validate_catalog(catalog):
    seen = set()
    for artist in catalog['artists']:
        name = artist['name']
        if not isinstance(name, str) or not artist_key(name) or not artist['albums']:
            raise ValueError('Each artist needs a name and at least one album.')
        key = artist_key(name)
        if key in seen:
            raise ValueError(f'Duplicate artist in snapshot: {name}')
        seen.add(key)
        album_names = set()
        for album in artist['albums']:
            title = album['name']
            if not isinstance(title, str) or not title.strip() or not album['songs']:
                raise ValueError(f'Each album needs a name and songs: {name}')
            if title.casefold() in album_names:
                raise ValueError(f'Duplicate album: {name} / {title}')
            album_names.add(title.casefold())
            if album.get('complete_audio_tracklist'):
                expected = album.get('source_track_count')
                videos = album.get('excluded_music_videos', 0)
                if (type(expected) is not int or type(videos) is not int or videos < 0
                        or len(album['songs']) != expected - videos):
                    raise ValueError(f'Incomplete album tracklist: {name} / {title}')
            tracks = set()
            for song in album['songs']:
                track, title = song['track'], song['title']
                if (not isinstance(title, str) or not title.strip()
                        or type(track) is not int or track < 1 or track in tracks):
                    raise ValueError(f'Invalid or duplicate track: {name} / {album["name"]}')
                tracks.add(track)


def import_catalog(connection, catalog, expand_existing=False):
    """Import atomically; optionally fill existing artists without deleting records."""
    validate_catalog(catalog)
    added = {'artists': 0, 'albums': 0, 'songs': 0}
    with connection:
        existing = {artist_key(row[1]): row[0]
                    for row in connection.execute('SELECT _id, name FROM artists')}
        for artist in catalog['artists']:
            key = artist_key(artist['name'])
            artist_id = existing.get(key)
            if artist_id is not None and not expand_existing:
                continue
            if artist_id is None:
                artist_id = connection.execute('INSERT INTO artists(name) VALUES (?)',
                                               (artist['name'],)).lastrowid
                added['artists'] += 1
                existing[key] = artist_id
            albums = {row[1].casefold(): row[0] for row in connection.execute(
                'SELECT _id, name FROM albums WHERE artist=?', (artist_id,))}
            for album in artist['albums']:
                album_id = albums.get(album['name'].casefold())
                if album_id is None:
                    album_id = connection.execute('INSERT INTO albums(name, artist) VALUES (?, ?)',
                                                  (album['name'], artist_id)).lastrowid
                    added['albums'] += 1
                    albums[album['name'].casefold()] = album_id
                # Match by title rather than track number: a partial multi-disc import
                # may have stored disc-relative numbers that must now be corrected.
                matches = {}
                for row in connection.execute(
                        'SELECT _id, title, track FROM songs WHERE album=? ORDER BY track, _id', (album_id,)):
                    matches.setdefault(artist_key(row[1]), []).append(row)
                for song in album['songs']:
                    candidates = matches.get(artist_key(song['title']), [])
                    if candidates:
                        row = next((r for r in candidates if r[2] == song['track']), candidates[0])
                        candidates.remove(row)
                        if row[2] != song['track'] or row[1] != song['title']:
                            connection.execute('UPDATE songs SET track=?, title=? WHERE _id=?',
                                               (song['track'], song['title'], row[0]))
                    else:
                        connection.execute('INSERT INTO songs(track, title, album) VALUES (?, ?, ?)',
                                           (song['track'], song['title'], album_id))
                        added['songs'] += 1
    return added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=ROOT / 'music.sqlite')
    parser.add_argument('--catalog', type=Path, default=ROOT / 'data/catalog_additions.json')
    parser.add_argument('--expand-existing', action='store_true',
                        help='Add missing albums/tracks to existing artists and correct matching track numbers.')
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error(f'Database does not exist: {args.database}')
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
    connection = sqlite3.connect(args.database)
    try:
        counts = import_catalog(connection, catalog, expand_existing=args.expand_existing)
        print('Added ' + ', '.join(f'{count} {kind}' for kind, count in counts.items()))
    finally:
        connection.close()


if __name__ == '__main__':
    main()
