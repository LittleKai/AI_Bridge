import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path

class ConverterTab:
    """
    Tab for converting novel files (TXT, DOCX, EPUB) to CSV format
    """

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.is_processing = False

        self.create_widgets()
        self.update_ruby_handling_visibility()

    def create_widgets(self):
        """
        Create all widgets for converter tab
        """
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_input_section(main_frame)
        self.create_language_section(main_frame)
        self.create_action_section(main_frame)

    def create_input_section(self, parent):
        """
        Create input file/folder selection section
        """
        input_frame = ttk.LabelFrame(parent, text="Input", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # Create a frame for label and format dropdown on same row
        label_frame = ttk.Frame(input_frame)
        label_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(label_frame, text="Select Input (Supported: TXT, DOCX, EPUB):").pack(side=tk.LEFT)

        # Add output format dropdown
        ttk.Label(label_frame, text="Output format:").pack(side=tk.LEFT, padx=(20, 5))
        self.output_format_var = tk.StringVar(value="Excel")
        format_combo = ttk.Combobox(label_frame, textvariable=self.output_format_var,
                                    values=["CSV", "Excel"], state="readonly", width=10)
        format_combo.pack(side=tk.LEFT)

        path_frame = ttk.Frame(input_frame)
        path_frame.pack(fill=tk.X, pady=(5, 0))

        self.input_path_var = tk.StringVar()
        self.input_entry = ttk.Entry(path_frame, textvariable=self.input_path_var)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(path_frame, text="Browse File",
                   command=self.browse_file).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(path_frame, text="Browse Folder",
                   command=self.browse_folder).pack(side=tk.LEFT, padx=(5, 0))

    def create_language_section(self, parent):
        """
        Create language selection section with three widgets in one row
        """
        lang_frame = ttk.LabelFrame(parent, text="Language", padding=10)
        lang_frame.pack(fill=tk.X, pady=(0, 10))

        # Biến ngôn ngữ
        self.language_var = tk.StringVar(value="EN")
        self.language_var.trace('w', lambda *args: self.update_ruby_handling_visibility())

        # Danh sách ngôn ngữ
        languages = ["CN", "JP", "KR", "EN", "VI"]
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var,
                                  values=languages, state="readonly", width=10)
        lang_combo.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(5, 0))

        # Nhãn Ruby Handling
        self.ruby_label = ttk.Label(lang_frame, text="Ruby Handling (EPUB only):")
        self.ruby_label.grid(row=0, column=1, sticky="w", padx=(0, 5), pady=(5, 0))

        # Biến và combobox Ruby Handling
        self.ruby_handling_var = tk.StringVar(value="remove_hiragana")
        ruby_options = [
            ("Keep All", "keep_all"),
            ("Remove All", "remove_all"),
            ("Remove Hiragana Only", "remove_hiragana")
        ]

        self.ruby_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.ruby_handling_var,
            values=[opt[1] for opt in ruby_options],
            state="readonly",
            width=20
        )
        self.ruby_combo.grid(row=0, column=2, sticky="w", pady=(5, 0))

        # Cấu hình thêm cột cho ruby_combo nếu cần
        lang_frame.columnconfigure(2, weight=1)


    def update_ruby_handling_visibility(self):
        """
        Show/hide ruby label and combo based on language selection
        """
        if self.language_var.get() == "JP":
            self.ruby_label.grid()
            self.ruby_combo.grid()
        else:
            self.ruby_label.grid_remove()
            self.ruby_combo.grid_remove()

    def create_action_section(self, parent):
        """
        Create action buttons section
        """
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        self.convert_button = ttk.Button(action_frame, text="Convert to CSV",
                                         command=self.start_conversion)
        self.convert_button.pack(fill=tk.X, expand=True, ipady=5)

    def browse_file(self):
        """
        Browse for input file
        """
        filetypes = [
            ("All Supported", "*.txt *.docx *.epub"),
            ("Text Files", "*.txt"),
            ("Word Files", "*.docx"),
            ("EPUB Files", "*.epub"),
            ("All Files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.input_path_var.set(filename)

    def browse_folder(self):
        """
        Browse for input folder
        """
        foldername = filedialog.askdirectory()
        if foldername:
            self.input_path_var.set(foldername)

    def get_output_path(self, input_path, language):
        """
        Generate output path in Documents/AIBridge folder
        """
        output_dir = Path.home() / "Documents" / "AIBridge"
        output_dir.mkdir(parents=True, exist_ok=True)

        input_name = os.path.basename(input_path)
        if os.path.isfile(input_path):
            input_name = os.path.splitext(input_name)[0]

        if f"_{language}" in input_name:
            base_filename = f"{input_name}"
        else:
            base_filename = f"{input_name}_{language}"

        # Use selected output format
        extension = ".xlsx" if self.output_format_var.get() == "Excel" else ".csv"
        output_filename = f"{base_filename}{extension}"

        return str(output_dir / output_filename)

    def start_conversion(self):
        """
        Start the conversion process
        """
        input_path = self.input_path_var.get().strip()
        if not input_path:
            messagebox.showwarning("Warning", "Please select an input file or folder")
            return

        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input path does not exist")
            return

        language = self.language_var.get()
        ruby_handling = self.ruby_handling_var.get() if language == "JP" else None
        output_path = self.get_output_path(input_path, language)

        self.is_processing = True
        self.convert_button.config(state="disabled")

        self.main_window.log_message(f"Starting conversion: {os.path.basename(input_path)}")
        self.main_window.log_message(f"Language: {language}")
        if ruby_handling:
            self.main_window.log_message(f"Ruby handling: {ruby_handling}")
        self.main_window.log_message(f"Output: {output_path}")

        thread = threading.Thread(
            target=self.process_conversion,
            args=(input_path, language, output_path, ruby_handling),
            daemon=True
        )
        thread.start()

    def process_conversion(self, input_path, language, output_path, ruby_handling):
        """
        Process the conversion in background thread
        """
        try:
            from helper.novel_converter import convert_to_csv

            success, result_path = convert_to_csv(
                input_path,
                language,
                output_path,
                ruby_handling=ruby_handling,
                log_callback=self.main_window.log_message
            )

            if success:
                self.main_window.root.after(0, self.conversion_completed, result_path)
            else:
                self.main_window.root.after(0, self.conversion_failed)

        except Exception as e:
            error_msg = f"Error during conversion: {str(e)}"
            self.main_window.root.after(0, self.main_window.log_message, error_msg)
            self.main_window.root.after(0, self.conversion_failed)

    def conversion_completed(self, output_path):
        """
        Handle conversion completion
        """
        self.is_processing = False
        self.convert_button.config(state="normal")

        self.main_window.log_message("Conversion completed successfully!")

        messagebox.showinfo("Success",
                            f"Conversion completed!\n\nOutput file:\n{output_path}")

        if messagebox.askyesno("Open Folder", "Do you want to open the output folder?"):
            import subprocess
            import platform
            folder = os.path.dirname(output_path)
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def conversion_failed(self):
        """
        Handle conversion failure
        """
        self.is_processing = False
        self.convert_button.config(state="normal")

        messagebox.showerror("Error", "Conversion failed. Check log for details.")

    def get_settings(self):
        """
        Get current settings from tab
        """
        settings = {
            'input_path': self.input_path_var.get(),
            'language': self.language_var.get(),
            'output_format': self.output_format_var.get()  # Add output format to settings
        }

        if self.language_var.get() == "JP":
            settings['ruby_handling'] = self.ruby_handling_var.get()

        return settings

    def load_settings(self, settings):
        """
        Load settings into tab
        """
        if 'input_path' in settings:
            self.input_path_var.set(settings['input_path'])
        if 'language' in settings:
            self.language_var.set(settings['language'])
        if 'output_format' in settings:  # Load output format
            self.output_format_var.set(settings['output_format'])
        if 'ruby_handling' in settings and self.language_var.get() == "JP":
            self.ruby_handling_var.set(settings['ruby_handling'])
