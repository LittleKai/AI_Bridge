
import tkinter as tk
from tkinter import ttk
import pandas as pd
import os


class ProcessingTab:
    """Processing settings tab"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Load prompt types
        self.load_prompt_types()

        # Create tab content
        self.create_content()

        # Bind variable changes
        self.bind_variable_changes()

    def init_variables(self):
        """Initialize tab variables"""
        self.batch_size = tk.StringVar(value="10")
        self.prompt_type = tk.StringVar(value="")
        self.ai_service = tk.StringVar(value="Gemini")
        self.prompt_types = []

    def load_prompt_types(self):
        """Load prompt types from Excel file"""
        try:
            prompt_file = "assets/translate_prompt.xlsx"
            if os.path.exists(prompt_file):
                df = pd.read_excel(prompt_file)
                if 'type' in df.columns:
                    self.prompt_types = df['type'].unique().tolist()
                    if self.prompt_types:
                        self.prompt_type.set(self.prompt_types[0])
        except Exception as e:
            self.main_window.log_message(f"Warning: Could not load prompt types: {e}")
            self.prompt_types = ["Default"]
            self.prompt_type.set("Default")

    def bind_variable_changes(self):
        """Bind variable changes to auto-save"""
        variables = [
            self.batch_size,
            self.prompt_type,
            self.ai_service
        ]

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create tab content"""
        content_frame = ttk.Frame(self.parent, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(1, weight=1)

        # Batch size section
        self.create_batch_section(content_frame, row=0)

        # Prompt section
        self.create_prompt_section(content_frame, row=1)

        # AI service section
        self.create_ai_service_section(content_frame, row=2)

    def create_batch_section(self, parent, row):
        """Create batch size section"""
        batch_frame = ttk.LabelFrame(parent, text="Batch Processing", padding="10")
        batch_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        batch_frame.columnconfigure(1, weight=1)

        ttk.Label(batch_frame, text="Batch Size:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        batch_entry = ttk.Entry(batch_frame, textvariable=self.batch_size, width=10)
        batch_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(batch_frame, text="(Number of csv lines to process at once)",
                  font=("Arial", 9), foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))

    def create_prompt_section(self, parent, row):
        """Create prompt selection section"""
        prompt_frame = ttk.LabelFrame(parent, text="Prompt Configuration", padding="10")
        prompt_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        prompt_frame.columnconfigure(2, weight=1)

        # Edit Prompt button
        ttk.Button(prompt_frame, text="Edit Prompt",
                   command=self.open_prompt_dialog).grid(row=0, column=0, padx=(0, 10))

        # Prompt Type label
        ttk.Label(prompt_frame, text="Prompt Type:").grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        # Prompt Type dropdown
        prompt_dropdown = ttk.Combobox(
            prompt_frame,
            textvariable=self.prompt_type,
            values=self.prompt_types,
            state="readonly",
            width=20
        )
        prompt_dropdown.grid(row=0, column=2, sticky=tk.W)

    def create_ai_service_section(self, parent, row):
        """Create AI service selection section"""
        ai_frame = ttk.LabelFrame(parent, text="AI Service", padding="10")
        ai_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        ai_frame.columnconfigure(1, weight=1)

        ttk.Label(ai_frame, text="Select Service:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        ai_dropdown = ttk.Combobox(
            ai_frame,
            textvariable=self.ai_service,
            values=["Gemini", "Claude", "ChatGPT", "Perplexity"],
            state="readonly",
            width=15
        )
        ai_dropdown.grid(row=0, column=1, sticky=tk.W)

    def open_prompt_dialog(self):
        """Open prompt editing dialog"""
        from gui.dialogs.prompt_dialog import PromptDialog
        PromptDialog(self.main_window, self)

    def get_settings(self):
        """Get current tab settings"""
        return {
            'batch_size': self.batch_size.get(),
            'prompt_type': self.prompt_type.get(),
            'ai_service': self.ai_service.get()
        }

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            if 'batch_size' in settings:
                self.batch_size.set(settings['batch_size'])
            if 'prompt_type' in settings:
                self.prompt_type.set(settings['prompt_type'])
            if 'ai_service' in settings:
                self.ai_service.set(settings['ai_service'])
        except Exception as e:
            print(f"Warning: Could not load processing tab settings: {e}")