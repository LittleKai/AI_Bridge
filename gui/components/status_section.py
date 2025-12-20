import tkinter as tk
from tkinter import ttk


class StatusSection:
    """Status monitoring section component"""

    def __init__(self, parent, main_window, row=0):
        self.parent = parent
        self.main_window = main_window
        self.row = row

        self.create_section()

    def create_section(self):
        """Create the status section"""
        self.frame = ttk.LabelFrame(self.parent, text="Status", padding="10")
        self.frame.grid(row=self.row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        # Create left and right columns
        self.create_left_column()
        self.create_right_column()

    def create_left_column(self):
        """Create left column with progress"""
        left_column = ttk.Frame(self.frame)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        left_column.columnconfigure(1, weight=1)

        # Progress
        ttk.Label(left_column, text="Progress:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=3)
        self.progress_label = ttk.Label(left_column, text="0/0", foreground="red")
        self.progress_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)

    def create_right_column(self):
        """Create right column with key status"""
        right_column = ttk.Frame(self.frame)
        right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
        right_column.columnconfigure(1, weight=1)

        # Key Status
        ttk.Label(right_column, text="Key Status:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=3)
        self.key_status_label = ttk.Label(right_column, text="Checking...", foreground="orange")
        self.key_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)

    def set_bot_status(self, status, color):
        """Update bot status display - deprecated, kept for compatibility"""
        pass

    def set_progress(self, current, total, is_running=False):
        """Update progress display"""
        if total == 0:
            self.progress_label.config(text="0/0", foreground="red")
        else:
            progress_text = f"{current}/{total}"
            # Set color based on running status
            if is_running:
                color = "green"
            else:
                color = "red"
            self.progress_label.config(text=progress_text, foreground=color)

    def update_key_status(self, is_valid, message):
        """Update key validation status display"""
        if is_valid:
            self.key_status_label.config(text="Valid ✓", foreground="green")
        else:
            self.key_status_label.config(text="Invalid ✗", foreground="red")