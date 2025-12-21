import pandas as pd
import time
import os
import re
from datetime import datetime
from helper.ai_api_handler import AIAPIHandler


class TranslationProcessor:
    """Handles translation processing using various AI APIs"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.is_running = False
        self.current_api_keys = []
        self.api_handler = AIAPIHandler(main_window)
        self.current_output_file = None
        self.total_input_rows = 0
        self.processed_rows = 0

    def update_progress(self):
        """Update progress display in status section"""
        if self.current_output_file and os.path.exists(self.current_output_file):
            try:
                output_df = pd.read_csv(self.current_output_file)
                self.processed_rows = len(output_df)
            except:
                self.processed_rows = 0
        else:
            self.processed_rows = 0

        # Update progress display with running status
        self.main_window.status_section.set_progress(
            self.processed_rows,
            self.total_input_rows,
            self.is_running
        )

    def start_processing(self):
        """Start the translation processing"""
        self.is_running = True

        # Initialize progress tracking
        self.processed_rows = 0
        self.total_input_rows = 0

        try:
            # Get settings from tabs
            translation_settings = self.main_window.translation_tab.get_settings()
            processing_settings = self.main_window.processing_tab.get_settings()

            # Get input file (now contains full path)
            input_file = translation_settings.get('input_file')
            if not input_file:
                self.main_window.log_message("Error: No input file selected")
                self.main_window.status_section.set_bot_status("Error: No input file", "red")
                return

            # Check if input file exists
            if not os.path.exists(input_file):
                self.main_window.log_message(f"Error: Input file does not exist: {input_file}")
                self.main_window.status_section.set_bot_status("Error: File not found", "red")
                return

            self.main_window.log_message(f"Processing file: {os.path.basename(input_file)}")
            self.main_window.log_message(f"Full path: {input_file}")

            # Generate output path based on input file and prompt type
            output_path = self.generate_output_path(input_file, processing_settings.get('prompt_type'))
            self.current_output_file = output_path
            self.main_window.log_message(f"Output will be saved to: {output_path}")

            # Load API configuration
            ai_service = processing_settings.get('ai_service')
            # Check if it's an API service
            if "API" not in ai_service:
                self.main_window.log_message(f"Error: {ai_service} is not an API service. Use web interface mode instead.")
                self.main_window.status_section.set_bot_status("Error: Not API service", "red")
                return

            api_config = processing_settings['api_configs'].get(ai_service, {})
            self.current_api_keys = api_config.get('keys', [])

            if not self.current_api_keys:
                self.main_window.log_message(f"Error: No API keys configured for {ai_service}")
                self.main_window.status_section.set_bot_status("Error: No API keys", "red")
                return

            # Update status to processing
            self.main_window.status_section.set_bot_status("Initializing...", "orange")

            # Process with API
            self.process_with_api(
                input_file,
                output_path,
                ai_service,
                processing_settings.get('ai_model'),
                api_config,
                int(processing_settings.get('batch_size', 10)),
                processing_settings.get('prompt_type'),
                translation_settings.get('start_id'),
                translation_settings.get('stop_id')
            )

        except Exception as e:
            self.main_window.log_message(f"Error during processing: {e}")
            import traceback
            self.main_window.log_message(traceback.format_exc())
        finally:
            self.is_running = False
            # Final progress update with stopped status
            self.update_progress()
            # Update main window running status
            self.main_window.root.after(0, self.set_main_window_stopped)

    def set_main_window_stopped(self):
        """Set main window to stopped state"""
        self.main_window.is_running = False
        self.main_window.update_progress_display()

    def generate_output_path(self, input_path, prompt_type):
        """Generate output path based on input file name and prompt type"""
        # Get absolute path to work with
        input_path = os.path.abspath(input_path)
        input_filename = os.path.basename(input_path)

        # Detect language from filename only
        lang_folder = None
        for lang in ['JP', 'EN', 'KR', 'CN', 'VI']:
            if lang in input_filename.upper():
                lang_folder = lang
                break

        if not lang_folder:
            lang_folder = "Other"
            self.main_window.log_message(f"Warning: Could not detect language from filename, using 'Other' folder")

        # Create output filename with prompt type only (don't duplicate language)
        filename_without_ext, ext = os.path.splitext(input_filename)

        # Format: original_name_prompttype_translated.csv
        if prompt_type:
            output_filename = f"{filename_without_ext}_{prompt_type}_translated{ext}"
        else:
            output_filename = f"{filename_without_ext}_translated{ext}"

        # Create output directory
        output_dir = os.path.join(
            os.path.expanduser("~"),
            "Documents",
            "AIBridge",
            "Translated",
            lang_folder
        )

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, output_filename)

    def load_translation_prompt(self, input_path, prompt_type):
        """Load translation prompt based on detected language and prompt type"""
        # Get absolute path
        input_path = os.path.abspath(input_path)
        input_filename = os.path.basename(input_path)

        # Detect source language from filename only
        source_lang = None
        for lang in ['JP', 'EN', 'KR', 'CN', 'VI']:
            if lang in input_filename.upper():
                source_lang = lang
                break

        if not source_lang:
            self.main_window.log_message("Error: Could not detect source language from filename")
            self.main_window.log_message("Filename should contain language code (CN, JP, EN, KR, VI)")
            return None

        self.main_window.log_message(f"Loading prompt for source language: {source_lang}, type: {prompt_type}")

        # Load prompt from Excel file
        try:
            prompt_file = "assets/translate_prompt.xlsx"
            if not os.path.exists(prompt_file):
                self.main_window.log_message("Error: Prompt file not found at assets/translate_prompt.xlsx")
                return None

            df = pd.read_excel(prompt_file)

            # Find prompt for the specified type and language
            if 'type' in df.columns and source_lang in df.columns:
                prompt_row = df[df['type'] == prompt_type]
                if not prompt_row.empty:
                    prompt = prompt_row.iloc[0][source_lang]
                    if pd.notna(prompt) and prompt:
                        self.main_window.log_message(f"Successfully loaded prompt for {source_lang}, type: {prompt_type}")
                        return prompt
                    else:
                        self.main_window.log_message(f"Error: Prompt is empty for {source_lang}, type: {prompt_type}")
                else:
                    self.main_window.log_message(f"Error: Prompt type '{prompt_type}' not found in file")
            else:
                if 'type' not in df.columns:
                    self.main_window.log_message("Error: 'type' column not found in prompt file")
                if source_lang not in df.columns:
                    self.main_window.log_message(f"Error: Language column '{source_lang}' not found in prompt file")
                    available_langs = [col for col in df.columns if col not in ['type', 'description']]
                    self.main_window.log_message(f"Available languages: {', '.join(available_langs)}")

            return None

        except Exception as e:
            self.main_window.log_message(f"Error loading prompt file: {e}")
            return None

    def process_with_api(self, input_file, output_file, ai_service, model_name, api_config,
                         batch_size, prompt_type, start_id, stop_id):
        """Process translation using AI API"""

        # Load translation prompt
        prompt_template = self.load_translation_prompt(input_file, prompt_type)
        if not prompt_template:
            self.main_window.log_message("Error: Failed to load translation prompt")
            return

        # Read input CSV
        try:
            df = pd.read_csv(input_file)
            self.main_window.log_message(f"Loaded {len(df)} rows from input file")

            # Check required columns
            if 'id' not in df.columns:
                self.main_window.log_message("Error: CSV file must have 'id' column")
                return
            if 'text' not in df.columns:
                self.main_window.log_message("Error: CSV file must have 'text' column")
                self.main_window.log_message(f"Available columns: {', '.join(df.columns)}")
                return

        except Exception as e:
            self.main_window.log_message(f"Error reading input file: {e}")
            return

        # Check for existing output file and get last processed ID
        last_processed_id = None
        existing_results = []
        if os.path.exists(output_file):
            try:
                existing_df = pd.read_csv(output_file)
                if not existing_df.empty:
                    existing_results = existing_df.to_dict('records')
                    last_processed_id = existing_df['id'].max()
                    self.main_window.log_message(f"Found existing output with {len(existing_df)} rows, last ID: {last_processed_id}")
            except Exception as e:
                self.main_window.log_message(f"Warning: Could not read existing output: {e}")

        # Filter by ID range
        try:
            # Apply start/stop ID filters
            start_id = int(start_id) if start_id else None
            stop_id = int(stop_id) if stop_id else None

            if start_id is not None:
                df = df[df['id'] >= start_id]
            if stop_id is not None:
                df = df[df['id'] <= stop_id]

            # Filter out already processed IDs
            if last_processed_id is not None:
                df = df[df['id'] > last_processed_id]
                self.main_window.log_message(f"Continuing from ID {last_processed_id + 1}")

            self.main_window.log_message(f"Processing {len(df)} rows after filtering (ID range: {start_id or 'start'} to {stop_id or 'end'})")
            self.total_input_rows = len(df)

            # Add already processed rows to total for progress display
            if existing_results:
                self.processed_rows = len(existing_results)
                self.total_input_rows += self.processed_rows

        except Exception as e:
            self.main_window.log_message(f"Warning: Could not filter by ID range: {e}")
            self.total_input_rows = len(df)

        # Start with existing results
        results = existing_results.copy()

        # Process in batches
        batch_size = int(batch_size) if batch_size else 10
        total_batches = (len(df) - 1) // batch_size + 1 if len(df) > 0 else 0

        for batch_num, i in enumerate(range(0, len(df), batch_size), 1):
            if not self.is_running:
                self.main_window.log_message("Processing stopped by user")
                break

            batch = df.iloc[i:i+batch_size]
            batch_ids = batch['id'].tolist()
            self.main_window.log_message(f"Processing batch {batch_num}/{total_batches} (IDs: {batch_ids[0]}-{batch_ids[-1]}, {len(batch)} rows)")

            # Create batch text without trailing newline
            batch_lines = []
            for j, (_, row) in enumerate(batch.iterrows()):
                batch_lines.append(f"{j+1}. {row['text']}")
            batch_text = "\n".join(batch_lines)

            # Format prompt
            count_info = f"Source text consists of {len(batch)} numbered lines from 1 to {len(batch)}."
            prompt = prompt_template.format(count_info=count_info, text=batch_text)

            # Call appropriate API
            translated_text = None
            error_msg = None

            if ai_service == "Gemini API":
                translated_text, error_msg = self.api_handler.call_gemini_api(prompt, model_name, api_config, self.current_api_keys)
            elif ai_service == "ChatGPT API":
                translated_text, error_msg = self.api_handler.call_openai_api(prompt, model_name, api_config, self.current_api_keys)
            elif ai_service == "Claude API":
                translated_text, error_msg = self.api_handler.call_claude_api(prompt, model_name, api_config, self.current_api_keys)
            elif ai_service == "Grok API":
                translated_text, error_msg = self.api_handler.call_grok_api(prompt, model_name, api_config, self.current_api_keys)
            elif ai_service == "Perplexity API":
                translated_text, error_msg = self.api_handler.call_perplexity_api(prompt, model_name, api_config, self.current_api_keys)

            if translated_text:
                # Parse translated text
                translations = self.parse_numbered_text(translated_text, len(batch))
                successful_count = sum(1 for t in translations if t)
                self.main_window.log_message(f"Batch {batch_num} completed: {successful_count}/{len(batch)} translations successful")

                # Add to results
                for (idx, row), translation in zip(batch.iterrows(), translations):
                    results.append({
                        'id': row['id'],
                        'raw': row['text'],
                        'edit': translation,
                        'status': 'completed' if translation else 'failed'
                    })
            else:
                # Mark batch as failed
                self.main_window.log_message(f"Batch {batch_num} failed: {error_msg}")
                for idx, row in batch.iterrows():
                    results.append({
                        'id': row['id'],
                        'raw': row['text'],
                        'edit': '',
                        'status': 'failed'
                    })

            # Save intermediate results and update progress
            if results:
                results_df = pd.DataFrame(results)
                results_df_sorted = results_df.sort_values('id')
                results_df_sorted.to_csv(output_file, index=False)
                self.update_progress()

            # Small delay between batches
            if batch_num < total_batches:
                self.main_window.log_message(f"Waiting 2 seconds before next batch...")
                time.sleep(2)

        # Final save and summary
        if results:
            results_df = pd.DataFrame(results)
            results_df_sorted = results_df.sort_values('id')
            results_df_sorted.to_csv(output_file, index=False)

            completed_count = len([r for r in results if r['status'] == 'completed'])
            failed_count = len([r for r in results if r['status'] == 'failed'])

            self.main_window.log_message(f"Translation completed!")
            self.main_window.log_message(f"Total: {len(results)} rows processed")
            self.main_window.log_message(f"Successful: {completed_count} rows")
            self.main_window.log_message(f"Failed: {failed_count} rows")
            self.main_window.log_message(f"Output saved to: {output_file}")
        else:
            self.main_window.log_message("No results to save")

    def parse_numbered_text(self, text, expected_count):
        """
        Parse numbered text into list of translations
        """
        lines = []

        # Remove common separator patterns that indicate end of content
        separator_patterns = [
            r'\n---+\n.*$',  # Dashes separator
            r'\n={3,}\n.*$',  # Equal signs separator
            r'\n\*{3,}\n.*$',  # Asterisk separator
            r'\n_{3,}\n.*$',  # Underscore separator
        ]

        for pattern in separator_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)

        # Find lines with pattern "number. text"
        pattern = r'(\d+)\.\s*(.*?)(?=\n\d+\.|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            # Create dictionary with line number as key
            numbered_lines = {}
            for num, content in matches:
                # Clean up the content
                content = content.strip()
                # Remove trailing questions or notes from AI
                content = re.sub(r'\n+(Bạn có muốn|Do you want|Would you like).*$', '', content, flags=re.IGNORECASE | re.DOTALL)
                content = re.sub(r'\n+(Tôi có thể|I can|Let me know).*$', '', content, flags=re.IGNORECASE | re.DOTALL)
                # Remove any MJMJ or similar patterns (CSV line break artifacts)
                content = re.sub(r'\s*MJMJ\s*$', '', content)
                content = content.strip()
                numbered_lines[int(num)] = content

            # Fill in all lines
            for i in range(1, expected_count + 1):
                if i in numbered_lines:
                    lines.append(numbered_lines[i])
                else:
                    lines.append("")  # Missing line
        else:
            # Fallback: split by newline
            text_lines = text.strip().split('\n')
            for line in text_lines[:expected_count]:
                cleaned = re.sub(r'^\d+\.\s*', '', line).strip()
                # Clean up trailing content
                cleaned = re.sub(r'\s*MJMJ\s*$', '', cleaned)
                lines.append(cleaned)

            # Pad with empty strings if needed
            while len(lines) < expected_count:
                lines.append("")

        return lines

    def clean_translation_response(self, text):
        """
        Clean AI response by removing common artifacts and formatting issues
        """
        if not text:
            return text

        # Remove separator lines and everything after them
        separator_patterns = [
            r'\n---+.*$',
            r'\n={3,}.*$',
            r'\n\*{3,}.*$',
            r'\n_{3,}.*$',
        ]

        for pattern in separator_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)

        # Remove common AI helper phrases at the end
        ai_phrases = [
            r'\n+(Bạn có muốn|Do you want|Would you like).*$',
            r'\n+(Tôi có thể|I can|Let me know).*$',
            r'\n+(Nếu bạn cần|If you need).*$',
            r'\n+(Hãy cho tôi biết|Please let me know).*$',
        ]

        for phrase in ai_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE | re.DOTALL)

        return text.strip()