"""Browse the SQLite catalog and find songs on YouTube."""
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import urlencode
import webbrowser

BASE_DIR = Path(__file__).resolve().parent


class Library:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row

    def artists(self, search=''):
        # instr treats search text literally, including SQL wildcard characters.
        return self.connection.execute(
            'SELECT _id, name FROM artists WHERE instr(lower(name), lower(?)) > 0 '
            'ORDER BY name COLLATE NOCASE, _id', (search,)
        ).fetchall()

    def albums(self, artist_id):
        return self.connection.execute(
            'SELECT _id, name FROM albums WHERE artist=? ORDER BY name COLLATE NOCASE, _id',
            (artist_id,)
        ).fetchall()

    def songs(self, album_id):
        return self.connection.execute(
            'SELECT _id, title, track FROM songs WHERE album=? ORDER BY track, title, _id',
            (album_id,)
        ).fetchall()

    def close(self):
        self.connection.close()


def youtube_search_url(artist, song):
    """Encode catalog text as one search parameter, including punctuation/Unicode."""
    return 'https://www.youtube.com/results?' + urlencode({
        'search_query': f'{artist} {song}'
    })


def open_youtube(artist, song):
    url = youtube_search_url(artist, song)
    if not webbrowser.open(url, new=2):
        raise RuntimeError('Could not open your browser. Copy the search link and open it manually.')
    return url


class MusicBrowser:
    def __init__(self, root, library):
        self.root = root
        self.library = library
        self.artist = self.album = self.song = None
        self.rows = {'artists': {}, 'albums': {}, 'songs': {}}
        self.trees = {}
        self.counts = {}
        root.title('Music Browser')
        root.geometry('1120x740')
        root.minsize(850, 580)
        root.configure(bg='#f3f5fa')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self._styles()
        self._build()
        self.refresh_artists()

    def _styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', font=('Helvetica', 12), background='#f3f5fa', foreground='#18243b')
        style.configure('TButton', padding=(14, 9))
        style.configure('Accent.TButton', background='#345ce6', foreground='white')
        style.map('Accent.TButton', background=[('active', '#2546b8')])
        style.configure('Title.TLabel', font=('Helvetica', 28, 'bold'))
        style.configure('Muted.TLabel', foreground='#647087')
        style.configure('Panel.TFrame', background='white')
        style.configure('Panel.TLabel', background='white', font=('Helvetica', 14, 'bold'))
        style.configure('Treeview', background='white', fieldbackground='white', rowheight=36,
                        borderwidth=0, font=('Helvetica', 12))
        style.map('Treeview', background=[('selected', '#e1e9ff')],
                  foreground=[('selected', '#203e9a')])
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])

    def _build(self):
        outer = ttk.Frame(self.root, padding=28)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='YOUR MUSIC LIBRARY', style='Muted.TLabel').pack(anchor='w')
        ttk.Label(outer, text='Find your next listen.', style='Title.TLabel').pack(anchor='w', pady=(5, 8))
        ttk.Label(outer, text='Choose an artist, explore an album, then click a song to find it on YouTube.',
                  style='Muted.TLabel').pack(anchor='w')
        search_row = ttk.Frame(outer)
        search_row.pack(fill='x', pady=(22, 14))
        ttk.Label(search_row, text='Search artists').pack(side='left', padx=(0, 12))
        self.search = tk.StringVar()
        entry = ttk.Entry(search_row, textvariable=self.search, width=34)
        entry.pack(side='left', fill='x', expand=True)
        ttk.Button(search_row, text='Clear', command=lambda: self.search.set('')).pack(side='left', padx=(10, 0))
        self.search.trace_add('write', lambda *_: self.refresh_artists())
        self.breadcrumb = tk.StringVar(value='All artists  /  Choose an artist  /  Choose an album')
        ttk.Label(outer, textvariable=self.breadcrumb, style='Muted.TLabel').pack(anchor='w', pady=(0, 12))
        panels = ttk.Frame(outer)
        panels.pack(fill='both', expand=True)
        panels.rowconfigure(0, weight=1)
        for column, (key, title) in enumerate((('artists', '01  Artists'), ('albums', '02  Albums'), ('songs', '03  Songs'))):
            panels.columnconfigure(column, weight=1, uniform='panels')
            panel = ttk.Frame(panels, style='Panel.TFrame', padding=14)
            panel.grid(row=0, column=column, sticky='nsew', padx=(0 if column == 0 else 12, 0))
            heading = ttk.Frame(panel, style='Panel.TFrame')
            heading.pack(fill='x', pady=(0, 12))
            ttk.Label(heading, text=title, style='Panel.TLabel').pack(side='left')
            self.counts[key] = tk.StringVar(value='0')
            ttk.Label(heading, textvariable=self.counts[key], style='Panel.TLabel').pack(side='right')
            body = ttk.Frame(panel, style='Panel.TFrame')
            body.pack(fill='both', expand=True)
            tree = ttk.Treeview(body, show='tree', selectmode='browse', columns=(), height=9)
            tree.column('#0', width=210, minwidth=80)
            scroll = ttk.Scrollbar(body, command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right', fill='y')
            tree.pack(side='left', fill='both', expand=True)
            tree.bind('<<TreeviewSelect>>', lambda event, kind=key: self.select(kind))
            self.trees[key] = tree
        self.hint = tk.StringVar(value='Choose an artist to see their albums.')
        ttk.Label(outer, textvariable=self.hint, style='Muted.TLabel', wraplength=980).pack(anchor='w', pady=(12, 16))
        destination = ttk.Frame(outer, padding=18, style='Panel.TFrame')
        destination.pack(fill='x')
        self.selected_title = tk.StringVar(value='Select a song to search YouTube')
        ttk.Label(destination, textvariable=self.selected_title, style='Panel.TLabel', wraplength=950).pack(anchor='w')
        ttk.Label(destination, text='Choose a video on YouTube to start listening. Playback controls are in your browser.',
                  background='white', foreground='#647087', wraplength=950).pack(anchor='w', pady=(8, 0))
        controls = ttk.Frame(destination, style='Panel.TFrame')
        controls.pack(fill='x', pady=(12, 0))
        self.youtube_button = ttk.Button(controls, text='Open on YouTube ↗', style='Accent.TButton',
                                         command=self.open_selected, state='disabled')
        self.youtube_button.pack(side='left')
        self.copy_button = ttk.Button(controls, text='Copy search link', command=self.copy_link, state='disabled')
        self.copy_button.pack(side='left', padx=8)

    def populate(self, key, rows):
        tree = self.trees[key]
        tree.delete(*tree.get_children())
        self.rows[key] = {str(row['_id']): row for row in rows}
        for item_id, row in self.rows[key].items():
            label = row['title'] if key == 'songs' else row['name']
            if key == 'songs' and row['track'] is not None:
                label = f"{row['track']:02d}   {label}"
            tree.insert('', 'end', iid=item_id, text=label)
        self.counts[key].set(str(len(rows)))

    def clear_song(self):
        self.song = None
        self.youtube_button.configure(state='disabled')
        self.copy_button.configure(state='disabled')
        self.selected_title.set('Select a song to search YouTube')

    def refresh_artists(self):
        self.artist = self.album = None
        self.clear_song()
        self.populate('songs', [])
        self.populate('albums', [])
        self.populate('artists', self.library.artists(self.search.get().strip()))
        self.breadcrumb.set('All artists  /  Choose an artist  /  Choose an album')
        self.hint.set('Choose an artist to see their albums.' if self.rows['artists'] else 'No matching artists. Try a different search.')

    def select(self, key):
        selection = self.trees[key].selection()
        if not selection or selection[0] not in self.rows[key]:
            return
        row = self.rows[key][selection[0]]
        if key == 'artists':
            self.artist, self.album = row, None
            self.clear_song()
            self.populate('songs', [])
            self.populate('albums', self.library.albums(row['_id']))
            self.breadcrumb.set(f"{row['name']}  /  Choose an album")
            self.hint.set('Choose an album to see its songs.' if self.rows['albums'] else 'This artist has no albums in the catalog.')
        elif key == 'albums':
            self.album = row
            self.clear_song()
            self.populate('songs', self.library.songs(row['_id']))
            self.breadcrumb.set(f"{self.artist['name']}  /  {row['name']}")
            self.hint.set('Click a song to open matching YouTube videos in your browser.' if self.rows['songs'] else 'This album has no songs in the catalog.')
        else:
            # Ignore duplicate selection notifications; the button can reopen a search.
            if self.song is not None and self.song['_id'] == row['_id']:
                return
            self.song = row
            self.youtube_button.configure(state='normal')
            self.copy_button.configure(state='normal')
            self.selected_title.set(f"{row['title']}  ·  {self.artist['name']}  ·  {self.album['name']}")
            self.open_selected()

    def open_selected(self):
        if self.song is None:
            return
        try:
            open_youtube(self.artist['name'], self.song['title'])
        except Exception as exc:
            self.hint.set('Browser unavailable. Use Copy search link to open the search manually.')
            messagebox.showerror('Could not open YouTube', str(exc), parent=self.root)
            return
        self.hint.set(f"Opened YouTube search for “{self.song['title']}”. Choose a video there to play it.")

    def copy_link(self):
        if self.song is None:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(youtube_search_url(self.artist['name'], self.song['title']))
        self.hint.set('YouTube search link copied to clipboard.')

    def close(self):
        self.library.close()
        self.root.destroy()


def main():
    database = BASE_DIR / 'music.sqlite'
    if not database.is_file():
        raise SystemExit(f'Music catalog not found: {database}')
    root = tk.Tk()
    try:
        library = Library(database)
    except sqlite3.Error as exc:
        messagebox.showerror('Could not open library', str(exc), parent=root)
        root.destroy()
        return
    MusicBrowser(root, library)
    root.mainloop()


if __name__ == '__main__':
    main()
