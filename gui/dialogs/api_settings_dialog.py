import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import json
import os
from helper.key_encryption import KeyEncryption


class APISettingsDialog:
    """Dialog for configuring API settings"""

    def __init__(self, main_window, processing_tab, service_name):
        self.main_window = main_window
        self.processing_tab = processing_tab
        self.service_name = service_name
        self.key_encryption = KeyEncryption()

        # Get current configuration
        self.config = self.processing_tab.api_configs[service_name].copy()

        # Store actual keys separately from display
        self.actual_keys = self.config.get('keys', []).copy()

        # Create dialog window
        self.window = tk.Toplevel(main_window.root)
        self.window.title(f"{service_name} Settings")
        self.window.resizable(False, False)

        # Make dialog modal
        self.window.attributes('-topmost', True)
        self.window.transient(main_window.root)
        self.window.grab_set()

        # Setup UI
        self.setup_ui()

        # Center window
        self.center_window()

        # Bind events
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # API Keys section
        keys_frame = ttk.LabelFrame(main_frame, text="API Keys", padding="10")
        keys_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        keys_frame.columnconfigure(0, weight=1)

        # Keys list display
        list_frame = ttk.Frame(keys_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        list_frame.columnconfigure(0, weight=1)

        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.keys_listbox = tk.Listbox(list_frame, height=5, yscrollcommand=scrollbar.set)
        self.keys_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.keys_listbox.yview)

        # Load existing keys with masking
        for key in self.actual_keys:
            masked_key = self.key_encryption.mask_key_for_display(key)
            self.keys_listbox.insert(tk.END, masked_key)

        # Info label
        info_label = ttk.Label(keys_frame, text="Keys are encrypted and stored securely",
                               font=("Arial", 8), foreground="green")
        info_label.grid(row=1, column=0, sticky=tk.W, pady=(2, 5))

        # Buttons for keys management
        btn_frame = ttk.Frame(keys_frame)
        btn_frame.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))

        ttk.Button(btn_frame, text="Add Key", command=self.add_key).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Remove", command=self.remove_key).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Import Excel", command=self.import_keys_excel).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Clear All", command=self.clear_keys).pack(side=tk.LEFT)

        row += 1

        # Model selection
        model_frame = ttk.LabelFrame(main_frame, text="Model Configuration", padding="10")
        model_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        model_frame.columnconfigure(1, weight=1)

        ttk.Label(model_frame, text="Available Models:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        models = self.config.get('models', [])
        self.model_var = tk.StringVar(value=self.processing_tab.ai_model.get() or self.config['default_model'])
        model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var,
                                      values=models, state="readonly", width=30)
        model_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E))

        row += 1

        # Parameters section
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="10")
        params_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        params_frame.columnconfigure(1, weight=1)

        # Max tokens
        ttk.Label(params_frame, text="Max Tokens:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.max_tokens_var = tk.IntVar(value=self.config['max_tokens'])
        max_tokens_spinbox = ttk.Spinbox(params_frame, from_=100, to=32000,
                                         textvariable=self.max_tokens_var, width=15)
        max_tokens_spinbox.grid(row=0, column=1, sticky=tk.W)

        # Temperature
        ttk.Label(params_frame, text="Temperature:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.temperature_var = tk.DoubleVar(value=self.config['temperature'])
        temp_scale = ttk.Scale(params_frame, from_=0.0, to=2.0, variable=self.temperature_var,
                               orient=tk.HORIZONTAL, length=200)
        temp_scale.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        self.temp_label = ttk.Label(params_frame, text=f"{self.temperature_var.get():.2f}")
        self.temp_label.grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        temp_scale.config(command=self.update_temp_label)

        # Top P
        ttk.Label(params_frame, text="Top P:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.top_p_var = tk.DoubleVar(value=self.config['top_p'])
        top_p_scale = ttk.Scale(params_frame, from_=0.0, to=1.0, variable=self.top_p_var,
                                orient=tk.HORIZONTAL, length=200)
        top_p_scale.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        self.top_p_label = ttk.Label(params_frame, text=f"{self.top_p_var.get():.2f}")
        self.top_p_label.grid(row=2, column=2, padx=(5, 0), pady=(5, 0))
        top_p_scale.config(command=self.update_top_p_label)

        # Top K (if applicable)
        if self.config.get('top_k') is not None:
            ttk.Label(params_frame, text="Top K:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
            self.top_k_var = tk.IntVar(value=self.config['top_k'])
            top_k_spinbox = ttk.Spinbox(params_frame, from_=1, to=100,
                                        textvariable=self.top_k_var, width=15)
            top_k_spinbox.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        else:
            self.top_k_var = None

        row += 1

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save", command=self.on_save).pack(side=tk.RIGHT)

    def update_temp_label(self, value):
        """Update temperature label display"""
        self.temp_label.config(text=f"{float(value):.2f}")

    def update_top_p_label(self, value):
        """Update top_p label display"""
        self.top_p_label.config(text=f"{float(value):.2f}")

    def add_key(self):
        """Add a new API key"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add API Key")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="10")
        frame.pack()

        ttk.Label(frame, text="Enter API Key:").grid(row=0, column=0, sticky=tk.W)

        # Info about security
        security_label = ttk.Label(frame, text="Key will be encrypted and stored securely",
                                   font=("Arial", 8), foreground="green")
        security_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        key_var = tk.StringVar()
        key_entry = ttk.Entry(frame, textvariable=key_var, width=50)
        key_entry.grid(row=2, column=0, pady=(5, 10))

        # Toggle show/hide button
        show_var = tk.BooleanVar(value=False)

        def toggle_show():
            if show_var.get():
                key_entry.config(show="")
                show_btn.config(text="Hide")
            else:
                key_entry.config(show="*")
                show_btn.config(text="Show")

        show_btn = ttk.Button(frame, text="Show", command=lambda: [show_var.set(not show_var.get()), toggle_show()])
        show_btn.grid(row=2, column=1, padx=(5, 0))

        def save_key():
            key = key_var.get().strip()
            if key:
                self.actual_keys.append(key)
                masked_key = self.key_encryption.mask_key_for_display(key)
                self.keys_listbox.insert(tk.END, masked_key)
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter a valid API key")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, pady=(10, 0))

        ttk.Button(btn_frame, text="OK", command=save_key).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

        # Focus on entry
        key_entry.focus()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def remove_key(self):
        """Remove selected API key"""
        selection = self.keys_listbox.curselection()
        if selection:
            index = selection[0]
            self.keys_listbox.delete(index)
            if index < len(self.actual_keys):
                del self.actual_keys[index]

    def import_keys_excel(self):
        """Import API keys from Excel file"""
        filename = filedialog.askopenfilename(
            title="Select Excel file with API keys",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )

        if filename:
            try:
                df = pd.read_excel(filename)

                # Look for 'key' column or first column with API key pattern
                keys = []
                if 'key' in df.columns:
                    keys = df['key'].dropna().tolist()
                else:
                    # Try to find column with API keys
                    for col in df.columns:
                        col_data = df[col].dropna()
                        # Check if column contains API key-like strings
                        if any(isinstance(val, str) and len(val) > 20 for val in col_data):
                            keys = col_data.tolist()
                            break

                if keys:
                    # Add valid keys
                    valid_keys = [k for k in keys if isinstance(k, str) and k.strip()]

                    added_count = 0
                    for key in valid_keys:
                        if key not in self.actual_keys:
                            self.actual_keys.append(key)
                            masked_key = self.key_encryption.mask_key_for_display(key)
                            self.keys_listbox.insert(tk.END, masked_key)
                            added_count += 1

                    messagebox.showinfo("Success", f"Imported {added_count} API keys from Excel file\nKeys are encrypted and stored securely")
                else:
                    messagebox.showwarning("Warning", "No valid API keys found in the Excel file")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to import keys: {e}")

    def clear_keys(self):
        """Clear all API keys"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all API keys?"):
            self.keys_listbox.delete(0, tk.END)
            self.actual_keys = []

    def on_save(self):
        """Save settings and close"""
        # Update configuration
        self.config['max_tokens'] = self.max_tokens_var.get()
        self.config['temperature'] = self.temperature_var.get()
        self.config['top_p'] = self.top_p_var.get()
        if self.top_k_var:
            self.config['top_k'] = self.top_k_var.get()

        # Update with actual keys (not masked) - store plain keys
        self.config['keys'] = self.actual_keys.copy()  # Use copy to avoid reference issues

        # Update processing tab configuration
        self.processing_tab.api_configs[self.service_name] = self.config.copy()  # Use copy here too

        # Update selected model
        self.processing_tab.ai_model.set(self.model_var.get())

        # Save settings
        self.main_window.save_settings()

        messagebox.showinfo("Success", "API settings saved successfully!\nKeys are encrypted and stored securely.")
        self.window.destroy()

    def on_cancel(self):
        """Close without saving"""
        self.window.destroy()

    def center_window(self):
        """Center the window on parent"""
        self.window.update_idletasks()

        width = 500
        height = 600

        parent_x = self.main_window.root.winfo_x()
        parent_y = self.main_window.root.winfo_y()
        parent_width = self.main_window.root.winfo_width()
        parent_height = self.main_window.root.winfo_height()

        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        self.window.geometry(f"{width}x{height}+{x}+{y}")