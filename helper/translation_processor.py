import pandas as pd
import time
import os
import re
from datetime import datetime
from helper.ai_api_handler import AIAPIHandler
from helper.prompt_helper import PromptHelper


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
                # Count rows with text in edit column as processed
                if 'edit' in output_df.columns:
                    self.processed_rows = len(output_df[output_df['edit'].notna() & (output_df['edit'] != '')])
                else:
                    self.processed_rows = 0
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
        return PromptHelper.generate_output_path(input_path, prompt_type)

    def load_translation_prompt(self, input_path, prompt_type):
        """Load translation prompt based on detected language and prompt type"""
        return PromptHelper.load_translation_prompt(
            input_path,
            prompt_type,
            self.main_window.log_message
        )

    def process_with_api(self, input_file, output_file, ai_service, model_name, api_config,
                         batch_size, prompt_type, start_id, stop_id):
        """Process translation using AI API with proper missing/failed row handling"""

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

        # Apply ID range filters
        try:
            start_id = int(start_id) if start_id else None
            stop_id = int(stop_id) if stop_id else None

            original_df = df.copy()  # Keep original for reference

            if start_id is not None:
                df = df[df['id'] >= start_id]
                self.main_window.log_message(f"Filtered by start_id >= {start_id}: {len(original_df)} -> {len(df)} rows")

            if stop_id is not None:
                df = df[df['id'] <= stop_id]
                self.main_window.log_message(f"Filtered by stop_id <= {stop_id}: {len(df)} rows")

        except Exception as e:
            self.main_window.log_message(f"Warning: Could not filter by ID range: {e}")

        # Create a set of all IDs that should be in the output (from filtered input)
        all_input_ids = set(df['id'].tolist())
        self.main_window.log_message(f"Total IDs in range: {len(all_input_ids)} (Range: {min(all_input_ids)} to {max(all_input_ids)})")

        # Load existing output and check what needs processing
        existing_results = {}
        completed_ids = set()
        failed_ids = set()

        if os.path.exists(output_file):
            try:
                existing_df = pd.read_csv(output_file)
                if not existing_df.empty:
                    for _, row in existing_df.iterrows():
                        row_id = row['id']
                        existing_results[row_id] = {
                            'id': row_id,
                            'raw': row.get('raw', ''),
                            'edit': row.get('edit', ''),
                            'status': row.get('status', '')
                        }

                        # Check if this ID has valid translation
                        edit_value = row.get('edit', '')
                        if edit_value and str(edit_value).strip() and str(edit_value).strip() != 'nan':
                            completed_ids.add(row_id)
                        else:
                            failed_ids.add(row_id)

                    self.main_window.log_message(f"Existing output has {len(existing_results)} rows total")
                    self.main_window.log_message(f"  - Completed: {len(completed_ids)} rows")
                    self.main_window.log_message(f"  - Failed/Empty: {len(failed_ids)} rows")

            except Exception as e:
                self.main_window.log_message(f"Warning: Could not read existing output: {e}")

        # Find IDs that need processing
        missing_ids = all_input_ids - set(existing_results.keys())
        retry_ids = all_input_ids & failed_ids
        ids_to_process = sorted(missing_ids | retry_ids)

        self.main_window.log_message(f"Analysis of IDs to process:")
        self.main_window.log_message(f"  - Missing from output: {len(missing_ids)} IDs")
        if missing_ids and len(missing_ids) <= 10:
            self.main_window.log_message(f"    Missing IDs: {sorted(list(missing_ids))}")
        elif missing_ids:
            sample_missing = sorted(list(missing_ids))[:10]
            self.main_window.log_message(f"    First 10 missing IDs: {sample_missing}...")

        self.main_window.log_message(f"  - Failed/need retry: {len(retry_ids)} IDs")
        if retry_ids and len(retry_ids) <= 10:
            self.main_window.log_message(f"    Failed IDs: {sorted(list(retry_ids))}")
        elif retry_ids:
            sample_retry = sorted(list(retry_ids))[:10]
            self.main_window.log_message(f"    First 10 failed IDs: {sample_retry}...")

        self.main_window.log_message(f"  - Total to process: {len(ids_to_process)} IDs")

        if not ids_to_process:
            self.main_window.log_message("All IDs in range already have valid translations. Nothing to process.")
            return

        # Set total for progress tracking
        self.total_input_rows = len(all_input_ids)
        self.processed_rows = len(completed_ids & all_input_ids)

        # Process IDs in batches
        batch_size = int(batch_size) if batch_size else 10
        total_batches = (len(ids_to_process) - 1) // batch_size + 1 if len(ids_to_process) > 0 else 0
        rows_processed_count = 0

        # Process IDs directly from the list, not from dataframe
        for batch_num in range(1, total_batches + 1):
            if not self.is_running:
                self.main_window.log_message("Processing stopped by user")
                break

            # Get batch of IDs
            batch_start_idx = (batch_num - 1) * batch_size
            batch_end_idx = min(batch_start_idx + batch_size, len(ids_to_process))
            batch_ids = ids_to_process[batch_start_idx:batch_end_idx]

            # Get actual data for these specific IDs only
            batch_df = df[df['id'].isin(batch_ids)].sort_values('id')

            if len(batch_df) != len(batch_ids):
                self.main_window.log_message(f"Warning: Expected {len(batch_ids)} rows but found {len(batch_df)}")
                # Some IDs might not have data in input file
                missing_in_input = set(batch_ids) - set(batch_df['id'].tolist())
                if missing_in_input:
                    self.main_window.log_message(f"  IDs not found in input: {sorted(missing_in_input)}")

            if len(batch_df) == 0:
                self.main_window.log_message(f"Skipping batch {batch_num} - no data found for IDs: {batch_ids}")
                continue

            actual_batch_ids = batch_df['id'].tolist()
            self.main_window.log_message(f"Processing batch {batch_num}/{total_batches} (IDs: {min(actual_batch_ids)}-{max(actual_batch_ids)}, {len(batch_df)} rows)")

            # Create batch text
            batch_lines = []
            for j, (_, row) in enumerate(batch_df.iterrows(), 1):
                batch_lines.append(f"{j}. {row['text']}")
            batch_text = "\n".join(batch_lines)

            # Format prompt with actual values
            count_info = f"Nội dung bao gồm {len(batch_df)} dòng có đánh số từ 1 đến {len(batch_df)}."
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

            if translated_text:
                # Parse translated text
                translations = self.parse_numbered_text(translated_text, len(batch_df))
                successful_count = sum(1 for t in translations if t)
                self.main_window.log_message(f"Batch {batch_num} completed: {successful_count}/{len(batch_df)} translations successful")

                # Update results
                for (idx, row), translation in zip(batch_df.iterrows(), translations):
                    existing_results[row['id']] = {
                        'id': row['id'],
                        'raw': row['text'],
                        'edit': translation,
                        'status': '' if translation else 'failed'
                    }
            else:
                # Mark batch as failed
                self.main_window.log_message(f"Batch {batch_num} failed: {error_msg}")
                for idx, row in batch_df.iterrows():
                    existing_results[row['id']] = {
                        'id': row['id'],
                        'raw': row['text'],
                        'edit': '',
                        'status': 'failed'
                    }

            rows_processed_count += len(batch_df)

            # Save and sort periodically
            if rows_processed_count >= 1000 or batch_num == total_batches:
                results_list = list(existing_results.values())
                results_df = pd.DataFrame(results_list)
                results_df_sorted = results_df.sort_values('id')
                results_df_sorted.to_csv(output_file, index=False)
                self.update_progress()

                if rows_processed_count >= 1000:
                    self.main_window.log_message(f"Saved and sorted after {rows_processed_count} rows")
                    rows_processed_count = 0

            # Small delay between batches
            if batch_num < total_batches and self.is_running:
                self.main_window.log_message(f"Waiting 2 seconds before next batch...")
                time.sleep(2)

        # Final save
        if existing_results:
            results_list = list(existing_results.values())
            results_df = pd.DataFrame(results_list)
            results_df_sorted = results_df.sort_values('id')
            results_df_sorted.to_csv(output_file, index=False)

            # Final count
            completed_count = sum(1 for r in results_list if r.get('edit') and str(r.get('edit')).strip())
            failed_count = len(results_list) - completed_count

            self.main_window.log_message(f"Translation completed!")
            self.main_window.log_message(f"Total rows in output: {len(results_list)}")
            self.main_window.log_message(f"Successful: {completed_count} rows")
            self.main_window.log_message(f"Failed/Empty: {failed_count} rows")
            self.main_window.log_message(f"Output saved to: {output_file}")


    @staticmethod
    def parse_numbered_text(text, expected_count):
        """Parse numbered text into list of translations"""
        lines = []

        # Find all numbered lines with pattern "number. text"
        pattern = r'(\d+)\.\s*(.*?)(?=\n\d+\.|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            # Create dictionary with line number as key
            numbered_lines = {}
            for num, content in matches:
                line_num = int(num)
                if 1 <= line_num <= expected_count:
                    # Clean up the content - remove \r if present
                    content = content.strip().replace('\r', '')

                    # Special handling for the last line in batch
                    if line_num == expected_count:
                        content = TranslationProcessor.clean_last_line_content(content)

                    numbered_lines[line_num] = content

            # Check if line 1 is missing but line 2 exists
            if 1 not in numbered_lines and 2 in numbered_lines:
                # Extract text before "2." as content for line 1
                pre_match = re.search(r'^(.*?)(?=\n?2\.)', text, re.DOTALL)
                if pre_match:
                    pre_text = pre_match.group(1).strip().replace('\r', '')
                    if pre_text and not re.match(r'^\d+\.', pre_text):
                        numbered_lines[1] = pre_text

            # Fill in all lines in order
            for i in range(1, expected_count + 1):
                if i in numbered_lines:
                    lines.append(numbered_lines[i])
                else:
                    lines.append("")  # Missing line
        else:
            # Fallback: split by newline and clean
            text_lines = text.strip().split('\n')
            for i, line in enumerate(text_lines[:expected_count]):
                # Remove line numbers if present and \r characters
                cleaned = re.sub(r'^\d+\.\s*', '', line).strip().replace('\r', '')

                # Special handling for the last line in fallback mode
                if i == expected_count - 1:  # Last line (0-indexed)
                    cleaned = TranslationProcessor.clean_last_line_content(cleaned)

                lines.append(cleaned)

            # Pad with empty strings if needed
            while len(lines) < expected_count:
                lines.append("")

        return lines

    @staticmethod
    def clean_last_line_content(content):
        """
        Clean AI-added comments strictly based on patterns.
        If a separator or keyword pattern is found, remove everything after/including it.
        """
        if not content:
            return content

        # 1. HARD SEPARATORS (Các ký tự phân cách rõ ràng)
        # Nếu tìm thấy các ký tự này, cắt bỏ toàn bộ nội dung phía sau nó.
        separator_patterns = ['***', '---', '===', '___', '•••']

        for separator in separator_patterns:
            if separator in content:
                # Lấy phần text trước separator đầu tiên tìm thấy
                return content.split(separator)[0].strip()

        # 2. KEYWORD PATTERNS (Các cụm từ bắt đầu câu hỏi/nhận xét của AI)
        # Kiểm tra dòng cuối cùng có bắt đầu bằng các từ khóa này không.
        ai_start_phrases = [
            'bạn muốn', 'bạn có', 'có muốn', 'có hài lòng',
            'would you', 'do you', 'let me know', 'is there',
            'có cần', 'nếu bạn', 'hãy cho', 'please',
            'tôi có thể', 'i can', 'if you', 'feel free'
        ]

        lines = content.split('\n')
        if not lines:
            return content

        # Duyệt ngược từ dòng cuối cùng lên để tìm dòng có nội dung
        for i in range(len(lines) - 1, -1, -1):
            current_line = lines[i].strip().lower()

            # Bỏ qua các dòng trống ở cuối
            if not current_line:
                continue

            # Nếu dòng cuối cùng (có nội dung) bắt đầu bằng keyword
            if any(current_line.startswith(phrase) for phrase in ai_start_phrases):
                # Trả về toàn bộ nội dung TRƯỚC dòng đó
                return '\n'.join(lines[:i]).strip()

            # Nếu dòng cuối cùng có nội dung nhưng KHÔNG khớp pattern,
            # dừng lại ngay (không xóa nhầm nội dung truyện/bài viết)
            break

        return content

