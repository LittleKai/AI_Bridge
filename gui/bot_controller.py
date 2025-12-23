import threading
import pandas as pd
import os
import time
from helper.web_bot_services import WebBotServices


class BotController:
    """Controller for bot automation tasks"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.running = False
        self.bot_thread = None
        self.web_bot_services = WebBotServices(main_window)

    def start(self):
        """Start the bot in a separate thread"""
        if not self.bot_thread or not self.bot_thread.is_alive():
            self.running = True
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()

    def stop(self):
        """Stop the bot"""
        self.running = False
        self.web_bot_services.running = False
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=2)

    def run_web_service(self, service_name):
        """Run bot for specific web service with batch processing"""
        self.main_window.log_message(f"Starting web automation for: {service_name}")

        try:
            # Get settings from tabs
            translation_settings = self.main_window.translation_tab.get_settings()
            processing_settings = self.main_window.processing_tab.get_settings()

            # Get input file
            input_file = translation_settings.get('input_file')
            if not input_file or not os.path.exists(input_file):
                self.main_window.log_message("Error: No valid input file selected")
                self.main_window.root.after(0, self.main_window.stop_bot)
                return

            # Load translation prompt
            prompt_type = processing_settings.get('prompt_type')
            prompt = self.load_translation_prompt(input_file, prompt_type)
            if not prompt:
                self.main_window.log_message("Error: Failed to load translation prompt")
                self.main_window.root.after(0, self.main_window.stop_bot)
                return

            # Read input CSV
            df = pd.read_csv(input_file)
            if 'text' not in df.columns:
                self.main_window.log_message("Error: CSV file must have 'text' column")
                self.main_window.root.after(0, self.main_window.stop_bot)
                return

            # Ensure ID column is integer type
            if 'id' in df.columns:
                df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)

            # Generate output path
            output_path = self.generate_output_path(input_file, prompt_type)

            # Check for existing output and analyze processed/failed IDs
            existing_results = {}
            completed_ids = set()
            failed_ids = set()

            if os.path.exists(output_path):
                try:
                    existing_df = pd.read_csv(output_path)
                    if not existing_df.empty:
                        # Ensure ID is integer in existing data
                        existing_df['id'] = pd.to_numeric(existing_df['id'], errors='coerce').fillna(0).astype(int)

                        # Build existing results dictionary
                        for _, row in existing_df.iterrows():
                            row_id = int(row['id'])
                            existing_results[row_id] = {
                                'id': row_id,
                                'raw': row.get('raw', ''),
                                'edit': row.get('edit', ''),
                                'status': row.get('status', '')
                            }

                            # Check if translation exists and is valid
                            edit_value = row.get('edit', '')
                            if edit_value and str(edit_value).strip() and str(edit_value).strip() != 'nan':
                                completed_ids.add(row_id)
                            else:
                                failed_ids.add(row_id)

                        self.main_window.log_message(f"Found existing output with {len(existing_df)} rows")
                        self.main_window.log_message(f"  - Completed: {len(completed_ids)} rows")
                        self.main_window.log_message(f"  - Failed/Empty: {len(failed_ids)} rows")
                except Exception as e:
                    self.main_window.log_message(f"Warning: Could not read existing output: {e}")

            # Filter by ID range
            start_id = translation_settings.get('start_id')
            stop_id = translation_settings.get('stop_id')

            try:
                start_id = int(start_id) if start_id else None
                stop_id = int(stop_id) if stop_id else None

                if start_id is not None:
                    df = df[df['id'] >= start_id]
                if stop_id is not None:
                    df = df[df['id'] <= stop_id]

            except Exception as e:
                self.main_window.log_message(f"Warning: Could not filter by ID range: {e}")

            # Get all IDs in the filtered range
            all_input_ids = set(df['id'].tolist())

            # Find IDs that need processing (not completed)
            missing_ids = all_input_ids - set(existing_results.keys())
            retry_ids = all_input_ids & failed_ids
            # Only process IDs that are NOT in completed_ids
            ids_to_process = sorted((missing_ids | retry_ids) - completed_ids)

            if ids_to_process:
                self.main_window.log_message(f"IDs to process: {len(ids_to_process)} (excluding completed IDs)")
                if len(ids_to_process) <= 10:
                    self.main_window.log_message(f"  Processing IDs: {ids_to_process}")
                else:
                    self.main_window.log_message(f"  First 10 IDs: {ids_to_process[:10]}...")
                    self.main_window.log_message(f"  ID range: {min(ids_to_process)} to {max(ids_to_process)}")
            else:
                self.main_window.log_message("All IDs in range have valid translations. Nothing to process.")
                self.main_window.root.after(0, self.main_window.stop_bot)
                return

            # Get batch settings
            batch_size = int(processing_settings.get('batch_size', 10))
            total_batches = (len(ids_to_process) - 1) // batch_size + 1 if len(ids_to_process) > 0 else 0

            # Process batches from the ID list directly
            for batch_num in range(1, total_batches + 1):
                if not self.running:
                    self.main_window.log_message("Processing stopped by user")
                    break

                # Get batch of IDs (not necessarily continuous)
                batch_start_idx = (batch_num - 1) * batch_size
                batch_end_idx = min(batch_start_idx + batch_size, len(ids_to_process))
                batch_ids = ids_to_process[batch_start_idx:batch_end_idx]

                # Get actual data for these specific IDs only
                batch = df[df['id'].isin(batch_ids)].sort_values('id')

                if len(batch) == 0:
                    self.main_window.log_message(f"Skipping batch {batch_num} - no data found for IDs: {batch_ids}")
                    continue

                actual_batch_ids = batch['id'].tolist()
                # Show actual IDs being processed (may not be continuous)
                if len(actual_batch_ids) <= 10:
                    self.main_window.log_message(f"Processing batch {batch_num}/{total_batches} (IDs: {actual_batch_ids}, {len(batch)} rows)")
                else:
                    self.main_window.log_message(f"Processing batch {batch_num}/{total_batches} ({len(batch)} rows, ID range: {min(actual_batch_ids)}-{max(actual_batch_ids)})")

                # Create batch text without trailing newline
                batch_lines = []
                for j, (_, row) in enumerate(batch.iterrows()):
                    batch_lines.append(f"{j+1}. {row['text']}")
                batch_text = "\n".join(batch_lines)

                # Use the generic bot function for all services
                translations, error = self.web_bot_services.run_generic_bot(
                    service_name,
                    prompt,
                    batch_text,
                    len(batch)
                )

                if translations:
                    self.main_window.log_message(f"Successfully processed {len(translations)} translations")
                    # Add results for this batch
                    for (idx, row), translation in zip(batch.iterrows(), translations):
                        row_id = int(row['id'])
                        existing_results[row_id] = {
                            'id': row_id,
                            'raw': row['text'],
                            'edit': translation,
                            'status': ''
                        }
                else:
                    self.main_window.log_message(f"Failed to get translations: {error}")
                    # Mark batch as failed
                    for idx, row in batch.iterrows():
                        row_id = int(row['id'])
                        existing_results[row_id] = {
                            'id': row_id,
                            'raw': row['text'],
                            'edit': '',
                            'status': 'failed'
                        }

                # Save intermediate results (sorted by ID)
                if existing_results:
                    results_list = list(existing_results.values())
                    results_df = pd.DataFrame(results_list)
                    # Ensure ID column is integer before sorting
                    results_df['id'] = pd.to_numeric(results_df['id'], errors='coerce').fillna(0).astype(int)
                    results_df_sorted = results_df.sort_values('id')
                    results_df_sorted.to_csv(output_path, index=False)

                    # Update progress
                    self.main_window.translation_processor.current_output_file = output_path
                    self.main_window.translation_processor.total_input_rows = len(all_input_ids)
                    self.main_window.translation_processor.update_progress()

                # Delay between batches if not the last one
                if batch_num < total_batches and self.running:
                    self.main_window.log_message(f"Waiting 3 seconds before next batch...")
                    time.sleep(3)

            # Final summary
            if existing_results:
                results_list = list(existing_results.values())
                completed_count = sum(1 for r in results_list if r.get('edit') and str(r.get('edit')).strip())
                failed_count = sum(1 for r in results_list if not r.get('edit') or not str(r.get('edit')).strip())

                self.main_window.log_message(f"Processing completed!")
                self.main_window.log_message(f"Total: {len(results_list)} rows")
                self.main_window.log_message(f"Successful: {completed_count} rows")
                self.main_window.log_message(f"Failed: {failed_count} rows")
                self.main_window.log_message(f"Output saved to: {output_path}")

        except Exception as e:
            self.main_window.log_message(f"Web service error: {str(e)}")
            import traceback
            self.main_window.log_message(traceback.format_exc())
        finally:
            self.main_window.root.after(0, self.main_window.stop_bot)

    def load_translation_prompt(self, input_path, prompt_type):
        """Load translation prompt based on detected language and prompt type"""
        input_filename = os.path.basename(input_path)

        # Detect source language from filename
        source_lang = None
        for lang in ['JP', 'EN', 'KR', 'CN', 'VI']:
            if lang in input_filename.upper():
                source_lang = lang
                break

        if not source_lang:
            self.main_window.log_message("Error: Could not detect source language from filename")
            return None

        try:
            prompt_file = "assets/translate_prompt.xlsx"
            if not os.path.exists(prompt_file):
                self.main_window.log_message("Error: Prompt file not found")
                return None

            df = pd.read_excel(prompt_file)

            if 'type' in df.columns and source_lang in df.columns:
                prompt_row = df[df['type'] == prompt_type]
                if not prompt_row.empty:
                    prompt = prompt_row.iloc[0][source_lang]
                    if pd.notna(prompt) and prompt:
                        self.main_window.log_message(f"Loaded prompt for {source_lang}, type: {prompt_type}")
                        # Add format placeholders and additional instructions
                        # These will be replaced with actual values later
                        prompt_with_format = prompt.strip() + "\n{count_info}\nVẫn giữ định dạng đánh số như bản gốc (1., 2., ...).\nChỉ trả về các dòng dịch được đánh số, không viết thêm bất kỳ nội dung nào khác.\nĐây là văn bản cần chuyển ngữ:\n{text}"
                        return prompt_with_format

            return None

        except Exception as e:
            self.main_window.log_message(f"Error loading prompt: {e}")
            return None

    def process_batch_results(self, batch, translations, input_file, prompt_type):
        """Process batch results and save to output file"""
        try:
            # Generate output path
            output_path = self.generate_output_path(input_file, prompt_type)
            self.main_window.log_message(f"Saving results to: {output_path}")

            # Create results
            results = []
            for (idx, row), translation in zip(batch.iterrows(), translations):
                results.append({
                    'id': row['id'],
                    'raw': row['text'],
                    'edit': translation,
                    'status': 'completed' if translation else 'failed'
                })

            # Save to CSV
            if results:
                results_df = pd.DataFrame(results)
                results_df_sorted = results_df.sort_values('id')
                results_df_sorted.to_csv(output_path, index=False)

                completed_count = len([r for r in results if r['status'] == 'completed'])
                self.main_window.log_message(f"Batch completed: {completed_count}/{len(results)} successful")

        except Exception as e:
            self.main_window.log_message(f"Error processing results: {e}")

    def generate_output_path(self, input_path, prompt_type):
        """Generate output path based on input file name and prompt type"""
        input_filename = os.path.basename(input_path)

        # Detect language from filename
        lang_folder = None
        for lang in ['JP', 'EN', 'KR', 'CN', 'VI']:
            if lang in input_filename.upper():
                lang_folder = lang
                break

        if not lang_folder:
            lang_folder = "Other"

        # Create output filename without duplicating language
        filename_without_ext, ext = os.path.splitext(input_filename)
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
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, output_filename)

    def run_bot(self):
        """Legacy method - redirects to run_web_service"""
        # Get selected service
        processing_settings = self.main_window.processing_tab.get_settings()
        ai_service = processing_settings.get('ai_service', 'Perplexity')
        self.run_web_service(ai_service)