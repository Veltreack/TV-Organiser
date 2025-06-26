import tkinter as tk
import requests
import datetime

import xml.etree.ElementTree as ET

def fetch_and_print_epg(url):
    response = requests.get(url)
    response.raise_for_status()
    xml_data = response.content
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        display_name = channel.findtext('display-name')
        print(f"Channel ID: {channel_id}, Name: {display_name}")
    for programme in root.findall('programme'):
        start = programme.get('start')
        stop = programme.get('stop')
        channel = programme.get('channel')
        title = programme.findtext('title')
        print(f"Programme: {title}, Channel: {channel}, Start: {start}, Stop: {stop}")


# Example usage:
class Mainscreen:
    def __init__(self, parent):
        self.parent = parent
        self.title = "Main Screen"
        self.description = "List of Channels and Programs"
        self.root = tk.Tk() if parent is None else tk.Toplevel(parent)
        self.root.title(self.title)
        self.root.configure(bg="#001f4d")
        self.root.geometry("1400x800")  # Enlarged window size

    def display(self):
        label_title = tk.Label(self.root, text=self.title, bg="#001f4d", fg="white", font=("Arial", 18, "bold"))
        label_title.pack(pady=(50, 10))
        label_desc = tk.Label(self.root, text=self.description, bg="#001f4d", fg="white", font=("Arial", 12))
        label_desc.pack(pady=(0, 20))
        self.bookmark_button = tk.Button(self.root, text="Bookmark", command=self.Bookmark, font=("Arial", 12))
        self.bookmark_button.pack(pady=(0, 10))

        # Create a frame to hold the genre checkboxes on the left side, next to title/description
        container = tk.Frame(self.root, bg="#001f4d")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        genre_frame = tk.Frame(container, bg="#001f4d")
        genre_frame.pack(side="left", anchor="n", padx=(0, 20), pady=(0, 0))

        content_frame = tk.Frame(container, bg="#001f4d")
        content_frame.pack(side="left", fill="both", expand=True)

        genres = [
            "Action", "Comedy", "Drama", "Horror", "Romance",
            "Sci-Fi", "Documentary", "Thriller", "Animation", "Fantasy"
        ]
        self.genre_vars = []
        for i, genre in enumerate(genres):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                genre_frame, text=genre, variable=var,
                bg="#001f4d", fg="white", selectcolor="#003366",
                font=("Arial", 11)
            )
            chk.grid(row=i, column=0, sticky="w", padx=10, pady=2)
            self.genre_vars.append(var)

        # Call the methods to display channels and programs
        self.display_channels()
        self.display_programs()
        self.timeline()  # Call the timeline method to display the timeline
    def display_channels(self):
        """Display the channels in a grid layout."""       
        self.coordinateX = 200  # Initial coordinates
        self.coordinateY = 200

        coordinateX = self.coordinateX  # Resets coordinates to original position
        coordinateY = self.coordinateY

        for row in range(0, 5):
            for coloumn in range(0, 1):
                tk.Button(self.root, text="Channel", width=30, height=10).place(x=coordinateX, y=coordinateY)
                coordinateX = coordinateX + 50  # Moves coordinates to the right by 50
            coordinateX = self.coordinateX  # Resets back to original x value new row
            coordinateY = coordinateY + 100  # Changes the row
    def display_programs(self):
        """Display the programs in a grid layout."""
        self.coordinateX = 400  # Initial coordinates
        self.coordinateY = 200
        coordinateX = self.coordinateX  # Resets coordinates to original position
        coordinateY = self.coordinateY
        for row in range(0, 5):
            for coloumn in range(0, 5):
                tk.Button(self.root, text="Program", width=30, height=10).place(x=coordinateX, y=coordinateY)
                coordinateX = coordinateX + 200  # Moves coordinates to the right by 50
            coordinateX = self.coordinateX  # Resets back to original x value new row
            coordinateY = coordinateY + 100  # Changes the row
    def timeline(self):
        """Display the timeline of programs above the boxes and update it live."""

        # Create a frame above the channel/program boxes to hold the timeline
        timeline_frame = tk.Frame(self.root, bg="#001f4d")
        timeline_frame.place(x=150, y=100)  # Adjust y to be above the boxes

        label = tk.Label(timeline_frame, text="Timeline of Programs", bg="#001f4d", fg="white", font=("Arial", 14, "bold"))
        label.pack(pady=(0, 5))

        # Make the canvas and timeline line longer (e.g., width=1500, line from 50 to 1450)
        self.timeline_canvas = tk.Canvas(timeline_frame, bg="#001f4d", width=1500, height=60, highlightthickness=0)
        self.timeline_canvas.pack()

        # Draw the longer timeline line
        self.timeline_canvas.create_line(50, 30, 1450, 30, fill="white", width=2)

        # Add time markers from 00:00 to 02:00 next day (26 hours, every 2 hours)
        self.timeline_hours = []
        total_hours = 26  # 00:00 to 02:00 next day
        for i in range(0, total_hours // 2 + 1):
            hour = (i * 2) % 24
            day = " (next)" if (i * 2) >= 24 else ""
            x = 50 + i * ((1450 - 50) / (total_hours // 2))
            time_label = f"{hour:02d}:00{day}"
            t = self.timeline_canvas.create_line(x, 25, x, 35, fill="white", width=2)
            t_text = self.timeline_canvas.create_text(x, 45, text=time_label, fill="white", font=("Arial", 9))
            self.timeline_hours.append((t, t_text))

        # Draw the current time indicator
        self.current_time_line = self.timeline_canvas.create_line(0, 15, 0, 45, fill="red", width=2)
        self.current_time_text = self.timeline_canvas.create_text(0, 10, text="", fill="red", font=("Arial", 9, "bold"))

        def update_time_indicator():
            now = datetime.datetime.now()
            # Timeline starts at 00:00, ends at 22:00 (12*2 hours)
            start_hour = 0
            end_hour = 22
            total_minutes = (end_hour - start_hour) * 60
            minutes_now = now.hour * 60 + now.minute
            if minutes_now < start_hour * 60:
                minutes_now = start_hour * 60
            elif minutes_now > end_hour * 60:
                minutes_now = end_hour * 60
            # Map minutes_now to x position
            x = 50 + (minutes_now - start_hour * 60) * (1000 / total_minutes)
            self.timeline_canvas.coords(self.current_time_line, x, 15, x, 45)
            self.timeline_canvas.coords(self.current_time_text, x, 10)
            self.timeline_canvas.itemconfig(self.current_time_text, text=now.strftime("%H:%M"))
            self.timeline_canvas.after(1000, update_time_indicator)

        update_time_indicator()

        # Example: Add program blocks (dummy data)
        # timeline_canvas.create_rectangle(100, 15, 250, 45, fill="#3399ff", outline="")
        # timeline_canvas.create_text(175, 30, text="Sample Program", fill="white", font=("Arial", 10))




    def run(self):
        self.display()
        self.root.mainloop()
    def Bookmark(self):
        # Placeholder for Bookmark functionality
        pass


class Bookmark:
    def __init__(self):
        self.bookmarks = []
        self.isBookmarked = False
    def add_bookmark(self, item):
        """Add an item to the bookmark list."""
        self.bookmarks.append(item)
        self.isBookmarked = not self.isBookmarked
        return self.isBookmarked
    def remove_bookmark(self, item):
        """Remove an item from the bookmark list."""
        if item in self.bookmarks:
            self.bookmarks.remove(item)
    def get_bookmarks(self):
        """Return the list of bookmarks."""
        return self.bookmarks
class Search():
    def __init__(self):
        self.search_term = ""
        self.results = []     

    def searchscreen(self):
        """Initialize the search screen."""
        self.root = tk.Toplevel()
        self.root.title("Search Screen")
        self.root.configure(bg="#003366")
        label = tk.Label(self.root, text="Search", bg="#003366", fg="white", font=("Arial", 18, "bold"))
        label.pack(pady=(20, 10))
        entry = tk.Entry(self.root, font=("Arial", 12))
        entry.pack(pady=(0, 10))
        self.results = []
        self.search_term = ""
        # Removed self.root.mainloop() to avoid nested mainloops

    def search(self, term):
        """Perform a search based on the given term and print its position if found."""
        self.search_term = term
        if not term:
            print("Please enter a search term.")
            return
        self.channels = ['Example', 'Sample', 'Test', 'Demo', 'Channel1', 'Channel2', 'Channel3']
        # Sort the list using selection sort for binary search
        n = len(self.channels)
        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                if self.channels[j] < self.channels[min_idx]:
                    min_idx = j
            if min_idx != i:
                self.channels[i], self.channels[min_idx] = self.channels[min_idx], self.channels[i]
        self.results = []
        left, right = 0, len(self.channels) - 1
        found = False
        position = -1
        while left <= right:
            mid = (left + right) // 2
            if self.channels[mid] == term:
                found = True
                position = mid
                self.results.append(self.channels[mid])
                break
            elif self.channels[mid] < term:
                left = mid + 1
            else:
                right = mid - 1
        if found:
            print(f"'{term}' found at position {position} in the sorted list.")
        else:
            print(f"'{term}' not found in the list.")
class Results:
    def __init__(self, results):
        self.results = results

    def resultscreen(self):
        """Initialize the results screen and display the search results."""
        self.root = tk.Toplevel()
        self.root.title("Results Screen")
        self.root.configure(bg="#003366")
        label = tk.Label(self.root, text="Search Results", bg="#003366", fg="white", font=("Arial", 18, "bold"))
        label.pack(pady=(20, 10))
        self.results_listbox = tk.Listbox(self.root, font=("Arial", 12), width=50)
        self.results_listbox.pack(pady=(0, 20))
        self.update_results_display()

    def update_results_display(self):
        self.results_listbox.delete(0, tk.END)
        for item in self.results:
            self.results_listbox.insert(tk.END, item)
# Example usage
if __name__ == "__main__":
    main_screen = Mainscreen(None)

    # Add a button to open the search screen from the main screen
    def open_search():
        main_screen.root.withdraw()  # Hide the main screen
        search_screen = Search()
        # Override the close event to show main screen again
        def on_close():
            search_screen.root.destroy()
            main_screen.root.deiconify()
        def show_search_screen():
            search_screen.root.title("Search Screen")
            search_screen.root.configure(bg="#003366")
            label = tk.Label(search_screen.root, text="Search", bg="#003366", fg="white", font=("Arial", 18, "bold"))
            label.pack(pady=(20, 10))
            entry = tk.Entry(search_screen.root, font=("Arial", 12))
            entry.pack(pady=(0, 10))
            tk.Button(search_screen.root, text="Search", command=lambda: search_screen.search(entry.get()), font=("Arial", 12)).pack(pady=(0, 20))
            search_screen.root.protocol("WM_DELETE_WINDOW", on_close)
            # Removed search_screen.root.mainloop() to avoid nested mainloops
        show_search_screen()

    # Add the button to the main screen at the top right corner
    search_button = tk.Button(main_screen.root, text="Open Search", command=open_search, font=("Arial", 12))
    search_button.place(relx=1.0, y=10, anchor="ne")  # Top right corner with some padding
    main_screen.run()
    #fetch_and_print_epg("https://xmltv.net/xml_files/Melbourne.xml")

# search_instance = Search()
# print(search_instance.results)  # Print search results for verification
# main_screen.root.mainloop()
