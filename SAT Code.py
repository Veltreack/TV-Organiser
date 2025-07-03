#Importing neccesary Libraries 
import tkinter as tk
import requests
import datetime
import threading
from tkinter import messagebox
import re
#Importing the inbuilt xml library to access the api data
import xml.etree.ElementTree as ET

'''
This code is a Python application that provides a graphical user interface (GUI) for viewing TV channels and their programs using the XMLTV format.
It includes features like searching for programs, filtering by genre, bookmarking channels, and displaying a timeline of current programs. 
The GUI is built using the Tkinter library.
'''
class Mainscreen:
    '''
    This class represents the main screen of the application.
    It initializes the main window, sets the title and description, and provides methods to display channels
    and programs, refresh the channel list, and manage the timeline.
    It also includes methods for displaying channels and programs in a paginated manner, with navigation buttons
    for moving between pages.
    The display method sets up the main screen layout, including genre checkboxes, a refresh button
    for updating the channel list, and a timeline display.
    The display_channels_and_programs method fetches and displays channels and programs from an XML E
    PG source, highlighting currently airing shows and allowing navigation through channels.
    The timebox method displays the current time in the top left corner of the main screen.
    '''
    def __init__(self, parent):
        self.parent = parent
        self.title = "Main Screen"
        self.description = "List of Channels and Programs"
        self.root = tk.Tk() if parent is None else tk.Toplevel(parent)
        self.root.title(self.title)
        self.root.configure(bg="#001f4d")
        self.root.geometry("1320x800")  # Enlarged window size
        self.program_buttons = []  # Initialize program_buttons to avoid attribute errors

    def display(self):
        label_title = tk.Label(self.root, text=self.title, bg="#001f4d", fg="white", font=("Arial", 18, "bold"))
        label_title.pack(pady=(50, 10))
        label_desc = tk.Label(self.root, text=self.description, bg="#001f4d", fg="white", font=("Arial", 12))
        label_desc.pack(pady=(0, 20))

        # Create a frame to hold the genre checkboxes on the left side, next to title/description
        container = tk.Frame(self.root, bg="#001f4d")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        genre_frame = tk.Frame(container, bg="#001f4d")
        genre_frame.pack(side="left", anchor="n", padx=(0, 20), pady=(0, 0))

        content_frame = tk.Frame(container, bg="#001f4d")
        content_frame.pack(side="left", fill="both", expand=True)

        # Add a button to refresh the channel list
        refresh_btn = tk.Button(self.root, text="Update Channel List", command=self.refresh_channel_list, font=("Arial", 12))
        refresh_btn.place(relx=1.0, x=-550, y=10, anchor="ne")  # Adjust x for placement

        # Call the methods to display channels and programs
        self.display_channels_and_programs()
        self.timebox()  # Call the timeline method to display the timeline

    def display_channels_and_programs(self):
        """
        Fetch and display channels from the XML EPG in alphabetical order.
        For each channel, display the channel name and up to 6 programs (current and next 5) side by side.
        This method live updates every minute to reflect the current time (local time).
        Also, highlights the show(s) currently being aired on each channel.
        Supports navigation via left/right buttons.
        """
        self.channel_page = 0  # Track current page for navigation
        self.channels_per_page = 15

        def parse_epg_and_update():
            url = "https://xmltv.net/xml_files/Melbourne.xml"
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                xml_data = response.content
                root = ET.fromstring(xml_data)
                # Build a mapping from channel_id to display_name
                channel_map = {}
                for channel in root.findall('./channel'):
                    channel_id = channel.get('id')
                    display_name = channel.findtext('display-name')
                    if channel_id and display_name:
                        channel_map[channel_id] = display_name

                # Collect programs grouped by channel
                programs_by_channel = {}
                for programme in root.findall('./programme'):
                    channel_id = programme.get('channel')
                    title = programme.findtext('title')
                    start = programme.get('start')
                    stop = programme.get('stop')
                    if channel_id and title and start and stop:
                        if channel_id not in programs_by_channel:
                            programs_by_channel[channel_id] = []
                        programs_by_channel[channel_id].append({
                            'title': title,
                            'start': start,
                            'stop': stop
                        })

                # Sort programs by start time for each channel
                for plist in programs_by_channel.values():
                    plist.sort(key=lambda p: p['start'])

                # Sort channels for consistent display
                sorted_channels = sorted(channel_map.items(), key=lambda x: x[1])
            except Exception as e:
                print(f"Error fetching or parsing XML: {e}")
                sorted_channels = []
                programs_by_channel = {}

            self.sorted_channels = sorted_channels
            self.programs_by_channel = programs_by_channel
            self.update_channel_program_display()
#           # Update the channel program display with the fetched data
        def update_loop():
            parse_epg_and_update()
            self.root.after(60000, update_loop)

        self.update_channel_program_display = lambda: self._update_channel_program_display()
        self._update_channel_program_display = lambda: None  # Placeholder, will be replaced below
#        # Define the method to update the channel and program display
        def _update_channel_program_display():
            # Remove previous widgets if any
            if hasattr(self, 'channel_prog_widgets'):
                for widgets in self.channel_prog_widgets:
                    for w in widgets:
                        w.destroy()
            self.channel_prog_widgets = []

            sorted_channels = getattr(self, 'sorted_channels', [])
            programs_by_channel = getattr(self, 'programs_by_channel', {})
            y_offset = 200
            x_channel = 40  # Channel buttons
            x_program = x_channel + 220  # Move programs further right
            max_channels = self.channels_per_page
            program_box_width = 38
            program_box_height = 3
            program_box_x_spacing = 200  # More space between boxes

            # Get current UTC time for XMLTV comparison
            now_utc = datetime.datetime.utcnow()

            start_idx = self.channel_page * max_channels
            end_idx = start_idx + max_channels
            for idx, (channel_id, display_name) in enumerate(sorted_channels[start_idx:end_idx]):
                widgets = []
                # Channel button
                btn_channel = tk.Button(self.root, text=display_name, width=30, height=program_box_height)
                btn_channel.place(x=x_channel, y=y_offset)
                widgets.append(btn_channel)
                # Find up to 6 programs: current and next 5
                programs = programs_by_channel.get(channel_id, [])
                prog_indices = []
                found_current = False
                for i, prog in enumerate(programs):
                    try:
                        start_dt = datetime.datetime.strptime(prog['start'][:14], "%Y%m%d%H%M%S")
                        stop_dt = datetime.datetime.strptime(prog['stop'][:14], "%Y%m%d%H%M%S")
                    except Exception:
                        continue
                    # Use CURRENT TIME (now_utc) to find currently airing program
                    if start_dt <= now_utc < stop_dt:
                        prog_indices = list(range(i, min(i + 6, len(programs))))
                        found_current = True
                        break
                    elif now_utc < start_dt and not found_current:
                        prog_indices = list(range(i, min(i + 6, len(programs))))
                        break
                if not prog_indices and programs:
                    prog_indices = list(range(min(6, len(programs))))
                # Display up to 6 program buttons
                for j, prog_idx in enumerate(prog_indices):
                    prog = programs[prog_idx]
                    try:
                        start_dt = datetime.datetime.strptime(prog['start'][:14], "%Y%m%d%H%M%S")
                        stop_dt = datetime.datetime.strptime(prog['stop'][:14], "%Y%m%d%H%M%S")
                        # Convert UTC to local time for display
                        start_str = start_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                        stop_str = stop_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                    except Exception as e:
                        start_str = stop_str = ""
                        start_dt = stop_dt = None
                    # Highlight the program that is currently airing
                    if start_dt and stop_dt and start_dt <= now_utc < stop_dt:
                        prog_text = f"Now: {prog['title']} ({start_str}-{stop_str})"
                        bg_color = "#e0ffe0"
                    else:
                        prog_text = f"{prog['title']} ({start_str}-{stop_str})"
                        bg_color = "#ffffe0"
                    btn_prog = tk.Button(
                        self.root,
                        text=prog_text,
                        width=program_box_width,
                        height=program_box_height,
                        bg=bg_color,
                        wraplength=300,
                        anchor="w",
                        justify="left"
                    )
                    btn_prog.place(x=x_program + j * program_box_x_spacing, y=y_offset)
                    widgets.append(btn_prog)
                self.channel_prog_widgets.append(widgets)
                y_offset += 55

        self._update_channel_program_display = _update_channel_program_display

        # Add navigation buttons
        self.navigationf_of_channels_and_program()

        update_loop()
#Creates buttons named next and previous which enable the user to navigate through the channels and programs.
#To the next set of channels and programs or the previous set of channels and programs.\
#Previously it was thought that the 6  day schedule could be implemented but it was not possible to do so.
#Thus it has been revised to the next 6 shows on the current channel.
    def navigationf_of_channels_and_program(self):
        """Create left and right navigation buttons to page through channels."""
        # Remove old navigation buttons if they exist
        if hasattr(self, 'nav_left_btn'):
            self.nav_left_btn.destroy()
        if hasattr(self, 'nav_right_btn'):
            self.nav_right_btn.destroy()

        def go_left():
            if self.channel_page > 0:
                self.channel_page -= 1
                self.update_channel_program_display()

        def go_right():
            total_channels = len(getattr(self, 'sorted_channels', []))
            max_page = max(0, (total_channels - 1) // self.channels_per_page)
            if self.channel_page < max_page:
                self.channel_page += 1
                self.update_channel_program_display()

        self.nav_left_btn = tk.Button(self.root, text="<< Prev", command=go_left, font=("Arial", 12))
        self.nav_left_btn.place(x=40, y=160)

        self.nav_right_btn = tk.Button(self.root, text="Next >>", command=go_right, font=("Arial", 12))
        self.nav_right_btn.place(x=220, y=160)
#A timeline is created to show the current time in the top left corner of the main screen.
    def timebox(self):
        """Create a timebox for displaying time. This does NOT live update."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timebox = tk.Label(self.root, text=now, bg="#ffffff", fg="black", font=("Arial", 12))
        self.timebox.place(x=0, y=0)

    def run(self):
        self.display()
        self.root.mainloop()

    def refresh_channel_list(self):
        """
        Refresh the main channel list and program display immediately.
        """
        if hasattr(self, 'display_channels_and_programs'):
            self.display_channels_and_programs()

            
'''
This class represents the search functionality of the application.
It initializes a search screen with an entry field for the search term,
a search button, and a scrollable results frame.
It provides methods to perform the search, fetch EPG data from a URL,
    and display the search results in a new menu.
'''
class Search():
    def __init__(self):
        self.search_term = ""
        self.results = []
        self.root = None  # Initialize root to None

    def searchscreen(self):
        """Initialize the search screen."""
        self.root = tk.Toplevel()
        self.root.title("Search Screen")
        self.root.configure(bg="#003366")
        label = tk.Label(self.root, text="Search", bg="#003366", fg="white", font=("Arial", 18, "bold"))
        label.pack(pady=(20, 10))
        self.entry = tk.Entry(self.root, font=("Arial", 12))
        self.entry.pack(pady=(0, 10))
        tk.Button(self.root, text="Search", command=lambda: self.search(self.entry.get()), font=("Arial", 12)).pack(pady=(0, 20))

        # --- Scrollable results frame ---
        container = tk.Frame(self.root, bg="#003366")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, bg="#003366", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.results_frame = tk.Frame(canvas, bg="#003366")

        self.results_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Removed self.root.mainloop() to avoid nested mainloops

    def search(self, term):
        """Search EPG data from the URL for the given keyword and show results in a new menu."""
        self.search_term = term.strip()
        self.results = []
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        if not self.search_term:
            tk.Label(self.results_frame, text="Please enter a search term.", bg="#003366", fg="white", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)
            return

        url = "https://xmltv.net/xml_files/Melbourne.xml"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            xml_data = response.content
            root = ET.fromstring(xml_data)
        except Exception as e:
            tk.Label(self.results_frame, text=f"Failed to fetch EPG data: {e}", bg="#003366", fg="red", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)
            return

        # Build channel id to display-name mapping
        channel_map = {}
        for channel in root.findall('./channel'):
            channel_id = channel.get('id')
            display_name = channel.findtext('display-name')
            if channel_id and display_name:
                channel_map[channel_id] = display_name

        # Search for matching programs
        for programme in root.findall('./programme'):
            title = programme.findtext('title') or ""
            if self.search_term.lower() in title.lower():
                channel_id = programme.get('channel')
                channel_name = channel_map.get(channel_id, channel_id)
                start = programme.get('start')
                stop = programme.get('stop')
                try:
                    start_dt = datetime.datetime.strptime(start[:14], "%Y%m%d%H%M%S")
                    stop_dt = datetime.datetime.strptime(stop[:14], "%Y%m%d%H%M%S")
                    # Convert UTC to local time for display
                    start_str = start_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
                    stop_str = stop_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                except Exception:
                    start_str = start
                    stop_str = stop
                self.results.append({
                    "channel": channel_name,
                    "title": title,
                    "start": start_str,
                    "stop": stop_str
                })

        if self.results:
            for item in self.results:
                # Each result in its own frame for separation
                result_box = tk.Frame(self.results_frame, bg="#224477", bd=2, relief="groove")
                result_box.pack(fill="x", padx=10, pady=6, anchor="w")
                # Show name (title) on top, channel name below, both medium size
                tk.Label(result_box, text=item["title"], bg="#224477", fg="white", font=("Arial", 14, "bold")).pack(anchor="w", padx=8, pady=(4,0))
                tk.Label(result_box, text=item["channel"], bg="#224477", fg="#ffcc00", font=("Arial", 13)).pack(anchor="w", padx=8, pady=(0,2))
                tk.Label(result_box, text=f"{item['start']} - {item['stop']}", bg="#224477", fg="#cccccc", font=("Arial", 11, "italic")).pack(anchor="w", padx=8, pady=(0,4))
        else:
            tk.Label(self.results_frame, text=f"No results found for '{self.search_term}'.", bg="#003366", fg="white", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)

# --- Add a search button to the top right corner of the main screen ---
def add_search_button_to_main(main_screen):
    def open_search():
        main_screen.root.withdraw()  # Hide the main screen
        search_screen = Search()
        search_screen.searchscreen()
        def on_close():
            search_screen.root.destroy()
            main_screen.root.deiconify()
        search_screen.root.protocol("WM_DELETE_WINDOW", on_close)
    # Place the button in the top right corner
    search_btn = tk.Button(main_screen.root, text="Search", command=open_search, font=("Arial", 12))
    search_btn.place(relx=1.0, x=-120, y=10, anchor="ne")  # Adjust x for padding

# Patch Mainscreen to add the search button after initialization
orig_display = Mainscreen.display
def new_display(self, *args, **kwargs):
    orig_display(self, *args, **kwargs)
    add_search_button_to_main(self)
Mainscreen.display = new_display
class Bookmark:
    def __init__(self):
        self.bookmarked_channels = set()
        self.root = None
        self.all_channels = []

    def bookmarkscreen(self):
        self.root = tk.Toplevel()
        self.root.title("Bookmarked Channels")
        self.root.configure(bg="#003366")
        label = tk.Label(self.root, text="Bookmarked Channels", bg="#003366", fg="white", font=("Arial", 18, "bold"))
        label.pack(pady=(20, 10))

        # --- Scrollable bookmarks frame ---
        container = tk.Frame(self.root, bg="#003366")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, bg="#003366", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.bookmarks_frame = tk.Frame(canvas, bg="#003366")

        self.bookmarks_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=self.bookmarks_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.fetch_all_channels()
        self.display_bookmarks()

    def fetch_all_channels(self):
        # Fetch all channels from the URL and store in self.all_channels
        url = "https://xmltv.net/xml_files/Melbourne.xml"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            xml_data = response.content
            root = ET.fromstring(xml_data)
            channels = []
            for channel in root.findall('./channel'):
                display_name = channel.findtext('display-name')
                if display_name:
                    channels.append(display_name)
            self.all_channels = sorted(set(channels))
        except Exception as e:
            self.all_channels = []
            tk.Label(self.bookmarks_frame, text=f"Failed to fetch channels: {e}", bg="#003366", fg="red", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)

    def display_bookmarks(self):
        for widget in self.bookmarks_frame.winfo_children():
            widget.destroy()
        if not self.all_channels:
            tk.Label(self.bookmarks_frame, text="No channels found.", bg="#003366", fg="white", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)
            return
        for ch in self.all_channels:
            row = tk.Frame(self.bookmarks_frame, bg="#224477", bd=1, relief="solid")
            row.pack(fill="x", padx=8, pady=4, anchor="w")
            is_bookmarked = ch in self.bookmarked_channels
            star = "★ " if is_bookmarked else ""
            star_color = "#FFD700" if is_bookmarked else "white"
            tk.Label(row, text=star, bg="#224477", fg=star_color, font=("Arial", 13, "bold")).pack(side="left", padx=(8,0), pady=4)
            tk.Label(row, text=ch, bg="#224477", fg="white", font=("Arial", 13)).pack(side="left", padx=(2,8), pady=4)
            if is_bookmarked:
                def make_remove(ch_name):
                    return lambda: self.remove_channel_from_bookmarks(ch_name)
                btn = tk.Button(row, text="Remove", command=make_remove(ch), font=("Arial", 11))
                btn.pack(side="right", padx=8)
            else:
                def make_add(ch_name):
                    return lambda: self.add_channel_to_bookmarks(ch_name)
                btn = tk.Button(row, text="Bookmark", command=make_add(ch), font=("Arial", 11))
                btn.pack(side="right", padx=8)

    def add_channel_to_bookmarks(self, channel_name):
        if channel_name not in self.bookmarked_channels:
            self.bookmarked_channels.add(channel_name)
            if self.root and self.root.winfo_exists():
                self.display_bookmarks()
        # Also update the main screen if it exists
        if hasattr(self, "main_screen_ref") and self.main_screen_ref:
            main_screen = self.main_screen_ref
            if hasattr(main_screen, "sorted_channels"):
                # Move bookmarked channels to the top, keep original order otherwise
                bookmarked = []
                non_bookmarked = []
                for channel_id, display_name in main_screen.sorted_channels:
                    if display_name in self.bookmarked_channels:
                        bookmarked.append((channel_id, display_name))
                    else:
                        non_bookmarked.append((channel_id, display_name))
                main_screen.sorted_channels = bookmarked + non_bookmarked
            main_screen.update_channel_program_display()

    def remove_channel_from_bookmarks(self, channel_name):
        if channel_name in self.bookmarked_channels:
            self.bookmarked_channels.remove(channel_name)
            if self.root and self.root.winfo_exists():
                self.display_bookmarks()
        # Also update the main screen if it exists
        if hasattr(self, "main_screen_ref") and self.main_screen_ref:
            main_screen = self.main_screen_ref
            if hasattr(main_screen, "sorted_channels"):
                # Move bookmarks to top, but keep original order for non-bookmarked
                bookmarked = []
                non_bookmarked = []
                for channel_id, display_name in main_screen.sorted_channels:
                    if display_name in self.bookmarked_channels:
                        bookmarked.append((channel_id, display_name))
                    else:
                        non_bookmarked.append((channel_id, display_name))
                # To restore original order for non-bookmarked, re-sort them by display_name
                orig_order = sorted(non_bookmarked, key=lambda x: x[1])
                main_screen.sorted_channels = bookmarked + orig_order
            main_screen.update_channel_program_display()

# --- Add bookmark logic to Mainscreen ---
def add_bookmark_button_to_main(main_screen):
    # Attach a reference for cross-callbacks
    if not hasattr(main_screen, 'bookmark_window'):
        main_screen.bookmark_window = Bookmark()
        main_screen.bookmark_window.main_screen_ref = main_screen

    def open_bookmarks():
        main_screen.root.withdraw()
        bookmark_window = main_screen.bookmark_window
        bookmark_window.bookmarkscreen()
        def on_close():
            bookmark_window.root.destroy()
            main_screen.root.deiconify()
            main_screen.update_channel_program_display()  # Ensure update on close
        bookmark_window.root.protocol("WM_DELETE_WINDOW", on_close)
    # Move the bookmark button to open the bookmarks window
    if hasattr(main_screen, 'bookmark_button'):
        main_screen.bookmark_button.config(command=open_bookmarks)

    # Add a button to bookmark channels (shows all channels from the URL)
    def open_channel_list():
        win = tk.Toplevel(main_screen.root)
        win.title("All Channels")
        win.configure(bg="#003366")
        label = tk.Label(win, text="Channels", bg="#003366", fg="white", font=("Arial", 16, "bold"))
        label.pack(pady=(20, 10))
        container = tk.Frame(win, bg="#003366")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, bg="#003366", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#003366")
        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Fetch channels from the URL
        url = "https://xmltv.net/xml_files/Melbourne.xml"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            xml_data = response.content
            root = ET.fromstring(xml_data)
            channels = []
            for channel in root.findall('./channel'):
                display_name = channel.findtext('display-name')
                if display_name:
                    channels.append(display_name)
            channels = sorted(set(channels))
        except Exception as e:
            tk.Label(frame, text=f"Failed to fetch channels: {e}", bg="#003366", fg="red", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)
            return

        bookmark_window = main_screen.bookmark_window

        # Show all channels with a bookmark or remove button and star icon if bookmarked
        for ch in channels:
            row = tk.Frame(frame, bg="#224477", bd=1, relief="solid")
            row.pack(fill="x", padx=8, pady=4, anchor="w")
            is_bookmarked = ch in bookmark_window.bookmarked_channels
            star = "★ " if is_bookmarked else ""
            star_color = "#FFD700" if is_bookmarked else "white"
            tk.Label(row, text=star, bg="#224477", fg=star_color, font=("Arial", 13, "bold")).pack(side="left", padx=(8,0), pady=4)
            tk.Label(row, text=ch, bg="#224477", fg="white", font=("Arial", 13)).pack(side="left", padx=(2,8), pady=4)
            if is_bookmarked:
                def make_remove(ch_name):
                    return lambda: remove_channel_from_bookmarks(ch_name)
                btn = tk.Button(row, text="Remove", command=make_remove(ch), font=("Arial", 11))
                btn.pack(side="right", padx=8)
            else:
                def make_add(ch_name):
                    return lambda: add_channel_to_bookmarks(ch_name)
                btn = tk.Button(row, text="Bookmark", command=make_add(ch), font=("Arial", 11))
                btn.pack(side="right", padx=8)

        def add_channel_to_bookmarks(channel_name):
            if channel_name not in bookmark_window.bookmarked_channels:
                bookmark_window.bookmarked_channels.add(channel_name)
                if bookmark_window.root and bookmark_window.root.winfo_exists():
                    bookmark_window.display_bookmarks()
            # Also update the main screen display and move bookmarks to top
            if hasattr(main_screen, "sorted_channels"):
                bookmarked = []
                non_bookmarked = []
                for channel_id, display_name in main_screen.sorted_channels:
                    if display_name in bookmark_window.bookmarked_channels:
                        bookmarked.append((channel_id, display_name))
                    else:
                        non_bookmarked.append((channel_id, display_name))
                main_screen.sorted_channels = bookmarked + non_bookmarked
            main_screen.update_channel_program_display()
            # Refresh this window to update star and button
            win.destroy()
            open_channel_list()

        def remove_channel_from_bookmarks(channel_name):
            if channel_name in bookmark_window.bookmarked_channels:
                bookmark_window.bookmarked_channels.remove(channel_name)
                if bookmark_window.root and bookmark_window.root.winfo_exists():
                    bookmark_window.display_bookmarks()
            # Also update the main screen display and move bookmarks to top
            if hasattr(main_screen, "sorted_channels"):
                bookmarked = []
                non_bookmarked = []
                for channel_id, display_name in main_screen.sorted_channels:
                    if display_name in bookmark_window.bookmarked_channels:
                        bookmarked.append((channel_id, display_name))
                    else:
                        non_bookmarked.append((channel_id, display_name))
                # Restore original order for non-bookmarked
                orig_order = sorted(non_bookmarked, key=lambda x: x[1])
                main_screen.sorted_channels = bookmarked + orig_order
            main_screen.update_channel_program_display()
            # Refresh this window to update star and button
            win.destroy()
            open_channel_list()

    # Add the "Add Channel Bookmark" button to the main screen (top right, next to others)
    channel_btn = tk.Button(main_screen.root, text="Bookmark Channel", command=open_channel_list, font=("Arial", 12))
    channel_btn.place(relx=1.0, x=-380, y=10, anchor="ne")  # Adjust x for padding

# Patch Mainscreen to add the bookmark button logic after initialization
orig_display3 = Mainscreen.display
def new_display3(self, *args, **kwargs):
    orig_display3(self, *args, **kwargs)
    add_bookmark_button_to_main(self)
Mainscreen.display = new_display3

# --- Patch Mainscreen to show bookmarked channels at the top with a yellow star icon ---
orig_update_channel_program_display = getattr(Mainscreen, "_update_channel_program_display", None)
def patched_update_channel_program_display(self):
    # Get bookmarks if available
    bookmarked_channels = set()
    if hasattr(self, "bookmark_window"):
        bookmarked_channels = self.bookmark_window.bookmarked_channels

    # Remove previous widgets if any
    if hasattr(self, 'channel_prog_widgets'):
        for widgets in self.channel_prog_widgets:
            for w in widgets:
                w.destroy()
    self.channel_prog_widgets = []

    sorted_channels = getattr(self, 'sorted_channels', [])
    programs_by_channel = getattr(self, 'programs_by_channel', {})
    y_offset = 200
    x_channel = 40  # Channel buttons
    x_program = x_channel + 220  # Move programs further right
    max_channels = self.channels_per_page
    program_box_width = 38
    program_box_height = 3
    program_box_x_spacing = 200

    now_utc = datetime.datetime.utcnow()

    # Separate bookmarked and non-bookmarked channels, keep original order for non-bookmarked
    bookmarked = []
    non_bookmarked = []
    for channel_id, display_name in sorted_channels:
        if display_name in bookmarked_channels:
            bookmarked.append((channel_id, display_name))
        else:
            non_bookmarked.append((channel_id, display_name))

    # Only show up to max_channels, but always show all bookmarks at the top
    display_channels = bookmarked + non_bookmarked
    display_channels = display_channels[:max_channels]

    for idx, (channel_id, display_name) in enumerate(display_channels):
        widgets = []
        # Add yellow star icon for bookmarked channels at the top
        is_bookmarked = display_name in bookmarked_channels and idx < len(bookmarked)
        star = "★ " if is_bookmarked else ""
        star_color = "#FFD700" if is_bookmarked else "black"
        btn_channel = tk.Button(
            self.root,
            text=star + display_name,
            width=30,
            height=program_box_height,
            fg=star_color
        )
        btn_channel.place(x=x_channel, y=y_offset)
        widgets.append(btn_channel)
        # Find up to 6 programs: current and next 5
        programs = programs_by_channel.get(channel_id, [])
        prog_indices = []
        found_current = False
        for i, prog in enumerate(programs):
            try:
                start_dt = datetime.datetime.strptime(prog['start'][:14], "%Y%m%d%H%M%S")
                stop_dt = datetime.datetime.strptime(prog['stop'][:14], "%Y%m%d%H%M%S")
            except Exception:
                continue
            if start_dt <= now_utc < stop_dt:
                prog_indices = list(range(i, min(i + 6, len(programs))))
                found_current = True
                break
            elif now_utc < start_dt and not found_current:
                prog_indices = list(range(i, min(i + 6, len(programs))))
                break
        if not prog_indices and programs:
            prog_indices = list(range(min(6, len(programs))))
        for j, prog_idx in enumerate(prog_indices):
            prog = programs[prog_idx]
            try:
                start_dt = datetime.datetime.strptime(prog['start'][:14], "%Y%m%d%H%M%S")
                stop_dt = datetime.datetime.strptime(prog['stop'][:14], "%Y%m%d%H%M%S")
                start_str = start_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                stop_str = stop_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
            except Exception as e:
                start_str = stop_str = ""
                start_dt = stop_dt = None
            if start_dt and stop_dt and start_dt <= now_utc < stop_dt:
                prog_text = f"Now: {prog['title']} ({start_str}-{stop_str})"
                bg_color = "#e0ffe0"
            else:
                prog_text = f"{prog['title']} ({start_str}-{stop_str})"
                bg_color = "#ffffe0"
            btn_prog = tk.Button(
                self.root,
                text=prog_text,
                width=program_box_width,
                height=program_box_height,
                bg=bg_color,
                wraplength=300,
                anchor="w",
                justify="left"
            )
            btn_prog.place(x=x_program + j * program_box_x_spacing, y=y_offset)
            widgets.append(btn_prog)
        self.channel_prog_widgets.append(widgets)
        y_offset += 55

Mainscreen._update_channel_program_display = patched_update_channel_program_display


# Patch Mainscreen to add description popups to existing program buttons
# --- Description popup logic for program buttons on Mainscreen ---

# --- Description popup logic for program buttons on Mainscreen ---
class ChannelDescription:
    def __init__(self):
        self.channel_descriptions = {}

    def fetch_channel_descriptions(self):
        url = "https://xmltv.net/xml_files/Melbourne.xml"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            xml_data = response.content
            root = ET.fromstring(xml_data)
            for channel in root.findall('./channel'):
                channel_id = channel.get('id')
                display_name = channel.findtext('display-name')
                desc = channel.findtext('desc') or "No description available."
                if channel_id and display_name:
                    self.channel_descriptions[display_name] = desc
        except Exception:
            self.channel_descriptions = {}

    def show_channel_description(self, display_name):
        desc = self.channel_descriptions.get(display_name, "No description available.")
        messagebox.showinfo(f"{display_name} - Channel Description", desc)
class Description:
    def __init__(self, main_screen=None):
        self.main_screen = main_screen
        self.program_descriptions = {}

    def fetch_program_descriptions(self):
        url = "https://xmltv.net/xml_files/Melbourne.xml"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            xml_data = response.content
            root = ET.fromstring(xml_data)
            for programme in root.findall('./programme'):
                channel_id = programme.get('channel')
                start = programme.get('start')
                stop = programme.get('stop')
                title = programme.findtext('title') or ""
                desc = programme.findtext('desc') or "No description available."
                key = (channel_id, start, stop, title)
                self.program_descriptions[key] = desc
        except Exception:
            self.program_descriptions = {}

    def show_description(self, channel_id, start, stop, title):
        key = (channel_id, start, stop, title)
        desc = self.program_descriptions.get(key, "No description available.")
        messagebox.showinfo(f"{title} - Description", desc)

# Patch Mainscreen channel and program buttons for description popups
def patch_mainscreen_for_descriptions():
    orig_update = Mainscreen._update_channel_program_display
    def new_update(self):
        orig_update(self)
        # Attach channel description logic to channel buttons
        if not hasattr(self, 'channel_description_window'):
            self.channel_description_window = ChannelDescription()
            self.channel_description_window.fetch_channel_descriptions()
        chan_desc_window = self.channel_description_window

        if not hasattr(self, 'description_window'):
            self.description_window = Description(self)
            self.description_window.fetch_program_descriptions()
        desc_window = self.description_window

        if hasattr(self, 'channel_prog_widgets'):
            # Map display_name to channel_id for quick lookup
            display_to_id = {display_name: channel_id for channel_id, display_name in getattr(self, 'sorted_channels', [])}
            for widgets in self.channel_prog_widgets:
                # Channel button
                channel_btn = widgets[0]
                channel_btn_text = channel_btn.cget("text").replace("★ ", "")
                channel_btn.config(command=lambda name=channel_btn_text: chan_desc_window.show_channel_description(name))
                # Program buttons
                channel_id = display_to_id.get(channel_btn_text)
                for btn in widgets[1:]:
                    prog_text = btn.cget("text")
                    m = re.match(r"(?:Now:\s*)?(.*) \((\d{2}:\d{2})-(\d{2}:\d{2})\)", prog_text)
                    if m:
                        title, start_str, stop_str = m.groups()
                        prog_match = None
                        if channel_id:
                            for prog in self.programs_by_channel.get(channel_id, []):
                                if prog['title'] == title:
                                    try:
                                        start_dt = datetime.datetime.strptime(prog['start'][:14], "%Y%m%d%H%M%S")
                                        stop_dt = datetime.datetime.strptime(prog['stop'][:14], "%Y%m%d%H%M%S")
                                        start_local = start_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                                        stop_local = stop_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                                        if start_local == start_str and stop_local == stop_str:
                                            prog_match = prog
                                            break
                                    except Exception:
                                        continue
                        if channel_id and prog_match:
                            btn.config(command=lambda cid=channel_id, st=prog_match['start'], sp=prog_match['stop'], t=title:
                                       desc_window.show_description(cid, st, sp, t))
                        else:
                            btn.config(command=lambda: messagebox.showinfo("Description", "No description available."))
    Mainscreen._update_channel_program_display = new_update

patch_mainscreen_for_descriptions()

# --- Patch Search results for description popups ---
orig_search = Search.search
def new_search(self, term):
    orig_search(self, term)
    # Attach description logic to search result boxes
    if not hasattr(self, 'description_window'):
        self.description_window = Description()
        self.description_window.fetch_program_descriptions()
    desc_window = self.description_window

    # Build a mapping from (channel, title, start, stop) to description
    # Already done in desc_window.program_descriptions

    # Map channel display name to channel_id for lookup
    # We'll need to fetch this mapping
    url = "https://xmltv.net/xml_files/Melbourne.xml"
    channel_name_to_id = {}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for channel in root.findall('./channel'):
            channel_id = channel.get('id')
            display_name = channel.findtext('display-name')
            if channel_id and display_name:
                channel_name_to_id[display_name] = channel_id
    except Exception:
        pass

    # Attach click event to each result_box (for all results)
    if hasattr(self, 'results_frame'):
        children = self.results_frame.winfo_children()
        for i, item in enumerate(self.results):
            if i < len(children):
                result_box = children[i]
                # Find channel_id
                channel_id = channel_name_to_id.get(item["channel"])
                title = item["title"]
                # Parse start and stop as in Description
                start = item["start"]
                stop = item["stop"]
                # Try to find the original UTC start/stop from the XML
                prog_start = prog_stop = None
                try:
                    for programme in root.findall('./programme'):
                        prog_title = programme.findtext('title') or ""
                        ch_id = programme.get('channel')
                        if ch_id == channel_id and prog_title == title:
                            # Compare local time string
                            start_dt = datetime.datetime.strptime(programme.get('start')[:14], "%Y%m%d%H%M%S")
                            stop_dt = datetime.datetime.strptime(programme.get('stop')[:14], "%Y%m%d%H%M%S")
                            start_local = start_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
                            stop_local = stop_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                            if start_local == start and stop_local == stop:
                                prog_start = programme.get('start')
                                prog_stop = programme.get('stop')
                                break
                except Exception:
                    pass

                def make_show_desc(cid=channel_id, st=prog_start, sp=prog_stop, t=title):
                    return lambda e: desc_window.show_description(cid, st, sp, t) if cid and st and sp else messagebox.showinfo("Description", "No description available.")

                # Bind left-click to show description
                result_box.bind("<Button-1>", make_show_desc())
                # Also change cursor on hover for better UX
                result_box.config(cursor="hand2")

Search.search = new_search

# --- Patch GenreFilter results for description popups ---
orig_apply_filter = GenreFilter.apply_filter
def new_apply_filter(self):
    orig_apply_filter(self)
    # Attach description logic to genre filter result boxes
    if not hasattr(self, 'description_window'):
        self.description_window = Description()
        self.description_window.fetch_program_descriptions()
    desc_window = self.description_window

    # Map channel display name to channel_id for lookup
    url = "https://xmltv.net/xml_files/Melbourne.xml"
    channel_name_to_id = {}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for channel in root.findall('./channel'):
            channel_id = channel.get('id')
            display_name = channel.findtext('display-name')
            if channel_id and display_name:
                channel_name_to_id[display_name] = channel_id
    except Exception:
        pass

    # Attach click event to each result_box (for all results)
    if hasattr(self, 'results_frame'):
        children = self.results_frame.winfo_children()
        for i, item in enumerate(self.results):
            if i < len(children):
                result_box = children[i]
                # Find channel_id
                channel_id = channel_name_to_id.get(item["channel"])
                title = item["title"]
                # Parse start and stop as in Description
                start = item["start"]
                stop = item["stop"]
                # Try to find the original UTC start/stop from the XML
                prog_start = prog_stop = None
                try:
                    for programme in root.findall('./programme'):
                        prog_title = programme.findtext('title') or ""
                        ch_id = programme.get('channel')
                        if ch_id == channel_id and prog_title == title:
                            # Compare local time string
                            start_dt = datetime.datetime.strptime(programme.get('start')[:14], "%Y%m%d%H%M%S")
                            stop_dt = datetime.datetime.strptime(programme.get('stop')[:14], "%Y%m%d%H%M%S")
                            start_local = start_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
                            stop_local = stop_dt.replace(tzinfo=datetime.timezone.utc).astimezone().strftime("%H:%M")
                            if start_local == start and stop_local == stop:
                                prog_start = programme.get('start')
                                prog_stop = programme.get('stop')
                                break
                except Exception:
                    pass

                def make_show_desc(cid=channel_id, st=prog_start, sp=prog_stop, t=title):
                    return lambda e: desc_window.show_description(cid, st, sp, t) if cid and st and sp else messagebox.showinfo("Description", "No description available.")

                # Bind left-click to show description
                result_box.bind("<Button-1>", make_show_desc())
                # Also change cursor on hover for better UX
                result_box.config(cursor="hand2")

GenreFilter.apply_filter = new_apply_filter
if __name__ == "__main__":
    main_screen = Mainscreen(None)
    main_screen.run() 
