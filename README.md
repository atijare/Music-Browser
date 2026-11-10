# Music Browser

A Python desktop music catalog with artist → album → song browsing and YouTube search. Built with Tkinter and SQLite; no third-party Python packages or API keys are needed.

## Run

Use Python 3.12 with Tkinter available (`python3 -m tkinter` opens a test window).
Keep `music.sqlite` beside `jukebox.py`, then run:

```bash
python3 jukebox.py
```

The database is located relative to the script, so launching from another directory also works.

## Listen on YouTube

1. Search for or select an artist.
2. Select an album.
3. Click a song to open YouTube search results for its artist and title in your default browser.
4. Choose a video on YouTube to play it. Use YouTube's playback and volume controls.

**Open on YouTube ↗** reopens the selected search. **Copy search link** copies the URL if you prefer another browser or the browser cannot open automatically.

Opening search results does not automatically select or play a video. This version does not resolve video IDs or embed a YouTube player. It requires internet access and a browser; no local music files are needed.

The app keeps the three browsing panels, artist search, breadcrumbs, counts, track numbers, and keyboard navigation. Changing the artist or album clears the song selection. It does not control existing YouTube tabs.

## Storage

The bundled database contains metadata for 283 artists, 686 albums, and 7,642 songs. The app reads the existing `artists`, `albums`, and `songs` tables without changing the catalog. Records are selected by ID, keeping duplicate names separate.

### Expanded artist catalog

The expansion adds **82 artists, 247 albums, and 2,292 songs**, preserving all 201 original artists and their albums and songs.

The catalog now includes a broad selection of previously missing pop, hip-hop, R&B, Latin, K-pop, Indian, country, electronic, and rock artists. Album names, track titles, and track numbers come from the [Apple iTunes catalog](https://performance-partners.apple.com/search-api). Most added artists currently have selected tracks from up to three album releases, rather than complete discographies. **Drake is expanded to all 11 solo studio albums plus eight mixtape, compilation, and collaborative releases, with full audio tracklists for the selected editions.** His releases were checked against the [official album catalog](https://music.apple.com/us/artist/drake/271256/full-albums). Duplicate album editions are consolidated where possible.

[data/catalog_additions.json](data/catalog_additions.json) records the imported metadata and source identifiers/URLs. The database already includes these additions; no import step is needed to use the app. To apply the same snapshot to an older copy of the catalog:

```bash
python3 scripts/import_catalog.py --database /path/to/music.sqlite
```

The importer preserves existing rows, matches artist names regardless of case, accents, and punctuation, and skips artists already present by default. To fill missing albums and tracks for existing artists as well:

```bash
python3 scripts/import_catalog.py --database /path/to/music.sqlite --expand-existing
```

Expansion preserves record IDs, adds missing albums and songs, and corrects matching song titles and track positions. It does not delete existing releases. Multi-disc tracks use continuous display numbering in album order; original disc and track numbers are retained in the JSON snapshot. Re-running the import does not create duplicates. Imports run in a single transaction and reject invalid data before writing. Releases marked complete are checked against their source audio song counts. Some store item counts include non-song extras, so those editions use the verified Apple Music audio count instead.

If you tried the earlier local-file playback version, any existing `song_media` table is left intact but is no longer used. Pygame is no longer required.

## Checks

```bash
python3 -m unittest discover -s tests -v
```

Tests check hierarchy queries, duplicate titles, track order, literal search, URL encoding, browser invocation, and browser failure handling. Browser calls are mocked so tests do not open tabs. Import tests also check that original records are preserved, reruns are safe, invalid data is rejected, database failures roll back, and the checked-in snapshot imports correctly.
