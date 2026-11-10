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

The bundled database contains metadata for 201 artists, 439 albums, and 5,350 songs. The app reads the existing `artists`, `albums`, and `songs` tables without changing the catalog. Records are selected by ID, keeping duplicate names separate.

If you tried the earlier local-file playback version, any existing `song_media` table is left intact but is no longer used. Pygame is no longer required.

## Checks

```bash
python3 -m unittest discover -s tests -v
```

Tests check hierarchy queries, duplicate titles, track order, literal search, URL encoding, browser invocation, and browser failure handling. Browser calls are mocked so tests do not open tabs.
