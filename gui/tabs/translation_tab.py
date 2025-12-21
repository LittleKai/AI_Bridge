import tkinter as tk
from tkinter import ttk, filedialog
import os


class TranslationTab:
    """Translation settings tab"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Create tab content
        self.create_content()

        # Bind variable changes
        self.bind_variable_changes()

    def init_variables(self):
        """Initialize tab variables"""
        self.input_file = tk.StringVar(value="")
        self.start_id = tk.StringVar(value="0")
        self.stop_id = tk.StringVar(value="100000")

        # Set default output directory
        default_output = os.path.join(os.path.expanduser("~"), "Documents", "AIBridge")
        self.output_directory = tk.StringVar(value=default_output)

    def bind_variable_changes(self):
        """Bind variable changes to auto-save"""
        variables = [
            self.input_file,
            self.start_id,
            self.stop_id,
            self.output_directory
        ]

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

        # Add progress update triggers
        self.start_id.trace('w', lambda *args: self.main_window.update_progress_display())
        self.stop_id.trace('w', lambda *args: self.main_window.update_progress_display())
        self.input_file.trace('w', lambda *args: self.main_window.update_progress_display())


    def create_content(self):
        """Create tab content"""
        content_frame = ttk.Frame(self.parent, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(1, weight=1)

        # Input file section
        self.create_input_section(content_frame, row=0)

        # Output info section
        self.create_output_info_section(content_frame, row=1)

        # ID range section
        self.create_id_range_section(content_frame, row=2)

    def create_input_section(self, parent, row):
        """Create input file selection section"""
        input_frame = ttk.LabelFrame(parent, text="Input File", padding="10")
        input_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Button(input_frame, text="Select Input CSV",
                   command=self.select_input_file).grid(row=0, column=0, padx=(0, 10))

        # Display only filename in label, but store full path
        self.input_label_var = tk.StringVar()
        input_label = ttk.Label(input_frame, textvariable=self.input_label_var)
        input_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Show full path on hover
        def show_full_path(event):
            if self.input_file.get():
                input_label.config(cursor="hand2")
                # Create tooltip
                tooltip = tk.Toplevel(input_label)
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = ttk.Label(tooltip, text=self.input_file.get(),
                                  background="lightyellow", relief="solid", borderwidth=1)
                label.pack()
                input_label.tooltip = tooltip

        def hide_full_path(event):
            input_label.config(cursor="")
            if hasattr(input_label, 'tooltip'):
                input_label.tooltip.destroy()

        input_label.bind("<Enter>", show_full_path)
        input_label.bind("<Leave>", hide_full_path)

    def create_output_info_section(self, parent, row):
        """Create output information section"""
        output_frame = ttk.LabelFrame(parent, text="Output Information", padding="10")
        output_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)

        # Default directory info
        ttk.Label(output_frame, text="Output directory:",
                  font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        ttk.Label(output_frame, textvariable=self.output_directory,
                  font=("Arial", 9), foreground="blue").grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

    def create_id_range_section(self, parent, row):
        """Create ID range section"""
        id_frame = ttk.LabelFrame(parent, text="ID Range", padding="10")
        id_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        id_frame.columnconfigure(1, weight=1)
        id_frame.columnconfigure(3, weight=1)

        ttk.Label(id_frame, text="Start ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        start_entry = ttk.Entry(id_frame, textvariable=self.start_id, width=10)
        start_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(id_frame, text="Stop ID:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))

        stop_entry = ttk.Entry(id_frame, textvariable=self.stop_id, width=10)
        stop_entry.grid(row=0, column=3, sticky=tk.W)

    def select_input_file(self):
        """Select input CSV file"""
        filename = filedialog.askopenfilename(
            title="Select Input CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            # Store the full path
            self.input_file.set(filename)
            # Display only basename in label
            self.input_label_var.set(os.path.basename(filename))
            self.main_window.log_message(f"Input file selected: {os.path.basename(filename)}")

            # Detect and log language
            lang = self.detect_language(filename)
            if lang:
                self.main_window.log_message(f"Detected language: {lang}")

            # Update progress display when file is selected
            self.main_window.update_progress_display()

    def detect_language(self, filepath):
        """Detect language from filename"""
        filename = os.path.basename(filepath)

        # Look for language codes in filename
        for lang in ['JP', 'EN', 'KR', 'CN', 'VI']:
            if lang in filename.upper():
                return lang

        return None

    def get_settings(self):
        """Get current tab settings"""
        return {
            'input_file': self.input_file.get(),  # This now contains full path
            'output_file': '',  # No longer used
            'start_id': self.start_id.get(),
            'stop_id': self.stop_id.get(),
            'output_directory': self.output_directory.get()
        }

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            if 'input_file' in settings:
                self.input_file.set(settings['input_file'])
                # Update display label
                if settings['input_file']:
                    self.input_label_var.set(os.path.basename(settings['input_file']))

            if 'start_id' in settings:
                self.start_id.set(settings['start_id'])
            if 'stop_id' in settings:
                self.stop_id.set(settings['stop_id'])
            if 'output_directory' in settings:
                self.output_directory.set(settings['output_directory'])
        except Exception as e:
            print(f"Warning: Could not load translation tab settings: {e}")