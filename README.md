# Music Browser Project

## Overview
The **Music Browser Project** is a graphical application built with Python using the `tkinter` library for its graphical user interface (GUI). It connects to a SQLite database (`music.sqlite`) to display hierarchical data about artists, albums, and songs. The application allows users to explore music data by selecting an artist to view their albums and subsequently selecting an album to view its songs.

## Features
1. **Dynamic Data Loading**:
   - The application uses `DataListBox` widgets to dynamically query and display data from the SQLite database.
   - Selecting an artist filters and displays only their albums.
   - Selecting an album filters and displays only its songs.

2. **Hierarchical Navigation**:
   - Linked listboxes enable smooth navigation from artists to albums and from albums to songs.

3. **Custom Scrollbox**:
   - A custom `Scrollbox` class extends `tkinter.Listbox` to add a vertical scrollbar, enhancing usability.

4. **Resizable GUI**:
   - The interface dynamically adjusts its layout to fit different screen sizes.

## Application Components
### 1. **Scrollbox Class**
- Enhances the default `tkinter.Listbox` by adding a vertical scrollbar.
- Methods:
  - `__init__`: Initializes the listbox with a scrollbar.
  - `grid`: Handles grid placement of both the listbox and its scrollbar.

### 2. **DataListBox Class**
- Extends `Scrollbox` to add database interaction capabilities.
- Key Features:
  - Executes SQL queries to populate the listbox.
  - Dynamically updates linked listboxes when a selection is made.
  - Handles hierarchical navigation (artists → albums → songs).

### 3. **Main Application Window**
- Layout:
  - **Artists Listbox**: Displays a list of artists.
  - **Albums Listbox**: Displays albums filtered by the selected artist.
  - **Songs Listbox**: Displays songs filtered by the selected album.
- Configurations:
  - Resizable columns and rows.
  - Scrollable data fields.

## Database Structure
- **Artists Table**:
  - `name`: Name of the artist.
  - `_id`: Unique identifier.
- **Albums Table**:
  - `name`: Name of the album.
  - `artist`: Foreign key linking to the `artists` table.
  - `_id`: Unique identifier.
- **Songs Table**:
  - `title`: Title of the song.
  - `album`: Foreign key linking to the `albums` table.
  - `track`: Track number.
  - `_id`: Unique identifier.

## How It Works
1. **Startup**:
   - Connects to the `music.sqlite` database.
   - Initializes the main window with three listboxes (Artists, Albums, Songs).

2. **Data Loading**:
   - On startup, the `Artists` listbox is populated with all artists from the database.
   - Selecting an artist queries and populates the `Albums` listbox with the corresponding albums.
   - Selecting an album queries and populates the `Songs` listbox with the corresponding songs.

3. **Event Binding**:
   - The `<<ListboxSelect>>` event is used to detect selections and trigger updates in linked listboxes.

## Error Handling
- Prevents crashes when no item is selected by checking for empty selections in the `on_select` method.

## Prerequisites
- Python 3.12 or later.
- SQLite database (`music.sqlite`) with appropriate tables and data.

## How to Run
1. Ensure you have Python installed.
2. Place the `music.sqlite` database in the same directory as the script.
3. Run the script:
   ```bash
   python jukebox.py
   ```
4. Use the GUI to browse artists, albums, and songs.

## Customization
- Modify the database queries in the `DataListBox` class to customize data sorting or filtering.
- Adjust the layout by modifying the `grid` configuration for the widgets.

## Future Improvements
- Add search functionality for artists, albums, and songs.
- Include error messages or status updates for user actions.
- Implement a play button to integrate music playback (requires additional libraries).

---
Enjoy exploring your music collection with the Music Browser!

