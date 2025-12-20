import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import webbrowser


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
        self.ai_model = tk.StringVar(value="")
        self.prompt_types = []

        # API configuration
        self.api_configs = {
            'Gemini API': {
                'models': ['gemini-2.0-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-pro', 'gemini-3-flash-preview', 'gemini-3-pro-preview'],
                'default_model': 'gemini-2.5-flash-lite',
                'keys': [],
                'max_tokens': 8192,
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'help_url': 'https://ai.google.dev/models/gemini'
            },
            'ChatGPT API': {
                'models': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                'default_model': 'gpt-3.5-turbo',
                'keys': [],
                'max_tokens': 4096,
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'help_url': 'https://platform.openai.com/docs/models'
            },
            'Claude API': {
                'models': ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
                'default_model': 'claude-3-5-sonnet-20241022',
                'keys': [],
                'max_tokens': 4096,
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'help_url': 'https://platform.claude.com/docs/en/about-claude/models/overview'
            },
            'Grok API': {
                'models': ['grok-2-1212', 'grok-2-vision-1212', 'grok-beta'],
                'default_model': 'grok-2-1212',
                'keys': [],
                'max_tokens': 4096,
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'help_url': 'https://docs.x.ai/docs/models'
            },
            'Perplexity API': {
                'models': ['llama-3.1-sonar-small-128k-online', 'llama-3.1-sonar-large-128k-online'],
                'default_model': 'llama-3.1-sonar-small-128k-online',
                'keys': [],
                'max_tokens': 4096,
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'help_url': 'https://docs.perplexity.ai/getting-started/models'
            }
        }

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
            self.ai_service,
            self.ai_model
        ]

        for var in variables:
            var.trace('w', lambda *args: self.main_window.save_settings())

        # Special handler for AI service change
        self.ai_service.trace('w', self.on_ai_service_change)

        # Update progress when prompt type changes (affects output file path)
        self.prompt_type.trace('w', lambda *args: self.main_window.update_progress_display())

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

        # Service selection row
        ttk.Label(ai_frame, text="Select Service:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        services = ["Gemini", "ChatGPT", "Claude", "Perplexity", "Grok", "Gemini API", "ChatGPT API", "Claude API", "Grok API", "Perplexity API"]
        self.ai_dropdown = ttk.Combobox(
            ai_frame,
            textvariable=self.ai_service,
            values=services,
            state="readonly",
            width=15
        )
        self.ai_dropdown.grid(row=0, column=1, sticky=tk.W)

        # Model configuration row (initially hidden)
        self.model_frame = ttk.Frame(ai_frame)
        self.model_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.model_frame.columnconfigure(1, weight=1)

        ttk.Label(self.model_frame, text="Model Code:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        self.model_entry = ttk.Entry(self.model_frame, textvariable=self.ai_model, width=25)
        self.model_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        self.settings_button = ttk.Button(self.model_frame, text="⚙ Settings",
                                          command=self.open_api_settings)
        self.settings_button.grid(row=0, column=2, padx=(5, 5))

        self.help_button = ttk.Button(self.model_frame, text="?", width=3,
                                      command=self.open_api_help)
        self.help_button.grid(row=0, column=3)

        # Initially hide model configuration
        self.model_frame.grid_remove()

        # Check initial service selection
        self.on_ai_service_change()

    def on_ai_service_change(self, *args):
        """Handle AI service selection change"""
        service = self.ai_service.get()

        # Show/hide model configuration based on service type
        if "API" in service:
            self.model_frame.grid()

            # Set default model for the selected API service
            if service in self.api_configs:
                default_model = self.api_configs[service]['default_model']
                if not self.ai_model.get():  # Only set if empty
                    self.ai_model.set(default_model)
        else:
            self.model_frame.grid_remove()
            self.ai_model.set("")  # Clear model name for non-API services

    def open_api_settings(self):
        """Open API settings dialog"""
        service = self.ai_service.get()
        if service in self.api_configs:
            from gui.dialogs.api_settings_dialog import APISettingsDialog
            APISettingsDialog(self.main_window, self, service)
        else:
            messagebox.showinfo("Info", "Please select an API service first")

    def open_api_help(self):
        """Open API documentation in browser"""
        service = self.ai_service.get()
        if service in self.api_configs:
            url = self.api_configs[service]['help_url']
            webbrowser.open(url)
        else:
            messagebox.showinfo("Info", "Please select an API service first")

    def open_prompt_dialog(self):
        """Open prompt editing dialog"""
        from gui.dialogs.prompt_dialog import PromptDialog
        PromptDialog(self.main_window, self)

    def get_settings(self):
        """Get current tab settings"""
        settings = {
            'batch_size': self.batch_size.get(),
            'prompt_type': self.prompt_type.get(),
            'ai_service': self.ai_service.get(),
            'ai_model': self.ai_model.get()
        }

        # Add API configurations
        settings['api_configs'] = {}
        for service, config in self.api_configs.items():
            settings['api_configs'][service] = {
                'keys': config['keys'],
                'max_tokens': config['max_tokens'],
                'temperature': config['temperature'],
                'top_p': config['top_p'],
                'top_k': config['top_k']
            }

        return settings

    def load_settings(self, settings):
        """Load settings into tab"""
        try:
            if 'batch_size' in settings:
                self.batch_size.set(settings['batch_size'])
            if 'prompt_type' in settings:
                self.prompt_type.set(settings['prompt_type'])
            if 'ai_service' in settings:
                self.ai_service.set(settings['ai_service'])
            if 'ai_model' in settings:
                self.ai_model.set(settings['ai_model'])

            # Load API configurations
            if 'api_configs' in settings:
                for service, config in settings['api_configs'].items():
                    if service in self.api_configs:
                        self.api_configs[service].update(config)

            # Trigger service change handler to show/hide model config
            self.on_ai_service_change()
        except Exception as e:
            print(f"Warning: Could not load processing tab settings: {e}")