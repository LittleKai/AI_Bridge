
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
import os
import json

from gui.window_manager import WindowManager
from gui.components.status_section import StatusSection
from gui.components.log_section import LogSection
from gui.tabs.translation_tab import TranslationTab
from gui.tabs.processing_tab import ProcessingTab
from gui.dialogs.prompt_dialog import PromptDialog
from key_validator import validate_application_key


class AITranslationBridgeGUI:
    """Main GUI application for AI Translation Bridge"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Translation Bridge")

        # Initialize variables
        self.init_variables()

        # Compact mode flag - Initialize early
        self.compact_mode = False

        # Store app key variable - Initialize early
        self.app_key_var = tk.StringVar(value="")

        # Initialize managers
        self.window_manager = WindowManager(self)

        # Load initial settings (including app_key)
        self.window_manager.load_initial_settings()

        # Setup GUI
        self.setup_gui()

        # Setup events
        self.setup_events()

        # Check key validation after loading settings
        self.check_key_validation()

    def init_variables(self):
        """Initialize all GUI variables"""
        self.is_running = False
        self.key_valid = False
        self.initial_key_validation_done = False

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Setup window from loaded settings
        self.window_manager.setup_window()

        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create content
        self.create_content(self.main_container)

        # Load tab settings after GUI is created
        self.window_manager.load_tab_settings()

    def create_content(self, parent):
        """Create main content area"""
        # Main frame
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)

        # Create sections
        self.create_header_section(self.main_frame, row=0)
        self.status_section = StatusSection(self.main_frame, self, row=1)
        self.create_tabbed_section(self.main_frame, row=2)
        self.create_control_section(self.main_frame, row=3)
        self.log_section = LogSection(self.main_frame, self, row=4)


    def create_header_section(self, parent, row):
        """Create header section with title and settings button"""
        self.header_frame = ttk.Frame(parent)
        self.header_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.header_frame.columnconfigure(0, weight=1)

        # Title
        self.title_label = ttk.Label(self.header_frame, text="AI Translation Bridge",
                                     font=("Arial", 14, "bold"))
        self.title_label.pack(side=tk.LEFT)

        # Settings button
        self.settings_button = ttk.Button(self.header_frame, text="⚙ Settings",
                                          command=self.open_settings)
        self.settings_button.pack(side=tk.RIGHT)

    def create_tabbed_section(self, parent, row):
        """Create tabbed section"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Translation tab
        translation_frame = ttk.Frame(self.notebook)
        self.notebook.add(translation_frame, text="Translation")
        self.translation_tab = TranslationTab(translation_frame, self)

        # Processing tab
        processing_frame = ttk.Frame(self.notebook)
        self.notebook.add(processing_frame, text="Processing")
        self.processing_tab = ProcessingTab(processing_frame, self)

    def create_control_section(self, parent, row):
        """Create bot control buttons section"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="Start (Shift+F1)",
            command=self.start_bot
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E), ipady=5)

        # Stop button
        self.stop_button = ttk.Button(
            control_frame,
            text="Stop (Shift+F3)",
            command=self.stop_bot,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E), ipady=5)

    def setup_events(self):
        """Setup event handlers"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        try:
            import keyboard
            keyboard.add_hotkey('shift+f1', self.start_bot)
            keyboard.add_hotkey('shift+f3', self.stop_bot)
        except Exception as e:
            self.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

    def start_bot(self):
        """Start bot and toggle compact mode"""
        if not self.is_running and self.key_valid:
            self.is_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_section.set_bot_status("Running", "green")
            self.log_message("Bot started")

            # Enter compact mode
            if not self.compact_mode:
                self.toggle_compact_mode()

    def stop_bot(self):
        """Stop bot and exit compact mode"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_section.set_bot_status("Stopped", "red")
            self.log_message("Bot stopped")

            # Exit compact mode
            if self.compact_mode:
                self.toggle_compact_mode()

    def calculate_compact_height(self):
        """Calculate the required height for compact mode"""
        # Force update to get accurate measurements
        self.root.update_idletasks()

        total_height = 0

        # Get main container padding
        main_padding = 20  # Top and bottom padding of main_container

        # Get each visible section's height
        sections = [
            (self.status_section.frame, 1),     # row 1
            (None, 3),                           # row 3 - control buttons
            (self.log_section.frame, 4)         # row 4
        ]

        for widget, row in sections:
            if widget is None:
                # Get control frame from row 3
                control_widgets = self.main_frame.grid_slaves(row=row)
                if control_widgets:
                    widget = control_widgets[0]

            if widget and widget.winfo_exists():
                # Get widget height
                widget_height = widget.winfo_reqheight()
                total_height += widget_height

                # Get pady from grid info
                grid_info = widget.grid_info()
                if 'pady' in grid_info:
                    pady = grid_info['pady']
                    if isinstance(pady, tuple):
                        total_height += pady[0] + pady[1]
                    else:
                        total_height += pady * 2

        # Add main container padding and some buffer
        total_height += main_padding + 30

        return total_height

    def toggle_compact_mode(self):
        """Toggle compact mode"""
        self.compact_mode = not self.compact_mode

        # Get current position
        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()

        if self.compact_mode:
            # Hide header and tabs
            self.header_frame.grid_forget()
            self.notebook.grid_forget()

            # Keep window on top
            self.root.attributes('-topmost', True)

            # Force update before calculating
            self.root.update_idletasks()

            # Calculate required height
            compact_height = self.calculate_compact_height()

            # Keep original width
            compact_width = self.window_manager.original_size['width']

            # Set compact size while maintaining position
            self.root.geometry(f"{compact_width}x{compact_height}+{current_x}+{current_y}")

            # Force minimum size for compact mode
            self.root.minsize(compact_width, compact_height)

        else:
            # Show header and tabs
            self.header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
            self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

            # Remove always on top
            self.root.attributes('-topmost', False)

            # Restore original size while maintaining position
            width = self.window_manager.original_size['width']
            height = self.window_manager.original_size['height']

            # Restore original minimum size
            self.root.minsize(500, 750)

            # Set geometry
            self.root.geometry(f"{width}x{height}+{current_x}+{current_y}")

            # Force update
            self.root.update_idletasks()


    def check_key_validation(self):
        """Check key validation status"""
        def check_in_background():
            try:
                # Get key from settings or variable
                key_to_validate = self.app_key_var.get() if self.app_key_var.get() else ""

                if not key_to_validate:
                    self.key_valid = False
                    self.initial_key_validation_done = True
                    self.root.after(0, self.status_section.update_key_status, False, "No key provided")
                    return

                from key_validator import validate_application_key_with_input
                is_valid, message = validate_application_key_with_input(key_to_validate)
                self.key_valid = is_valid
                self.initial_key_validation_done = True
                self.root.after(0, self.status_section.update_key_status, is_valid, message)
            except Exception as e:
                self.initial_key_validation_done = True
                self.root.after(0, self.status_section.update_key_status, False, f"Validation error: {e}")

        threading.Thread(target=check_in_background, daemon=True).start()

    def open_settings(self):
        """Open settings window"""
        from gui.dialogs.settings_dialog import SettingsDialog
        SettingsDialog(self)

    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.root.after(0, self.log_section.add_message, formatted_message)

    def save_settings(self):
        """Save all settings to file"""
        self.window_manager.save_settings()

    def load_settings(self):
        """Load settings from file"""
        self.window_manager.load_settings()

    def on_closing(self):
        """Handle window close event"""
        self.save_settings()

        try:
            import keyboard
            keyboard.unhook_all()
        except:
            pass

        self.root.destroy()

    def get_current_settings(self):
        """Get current settings from all tabs"""
        return {
            'translation': self.translation_tab.get_settings(),
            'processing': self.processing_tab.get_settings()
        }

    def run(self):
        """Start the GUI application"""
        self.log_message("AI Translation Bridge initialized.")
        self.log_message("Press Shift+F1 to start, Shift+F3 to stop.")

        self.root.mainloop()