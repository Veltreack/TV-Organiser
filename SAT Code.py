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
if __name__ == "__main__":
    main_screen = Mainscreen(None)
    main_screen.run() 
