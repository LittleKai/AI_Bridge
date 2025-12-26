import threading
import pandas as pd
import os
import time
from helper.web_bot_services import WebBotServices
from helper.prompt_helper import PromptHelper


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
            # Initialize processing
            input_file, output_path, prompt, df, all_input_ids = self._initialize_processing(service_name)
            if not input_file:
                return

            # Load and analyze existing results
            existing_results, completed_ids, failed_ids = self._load_existing_results(output_path)

            # Determine IDs to process
            ids_to_process = self._determine_ids_to_process(
                all_input_ids, existing_results, completed_ids, failed_ids
            )

            if not ids_to_process:
                self.main_window.log_message("All IDs in range have valid translations. Nothing to process.")
                self.main_window.root.after(0, self.main_window.stop_bot)
                return

            # Process batches
            self._process_batches(
                service_name, prompt, df, ids_to_process,
                existing_results, all_input_ids, output_path
            )

            # Final summary
            self._generate_summary(existing_results, output_path)

        except Exception as e:
            self.main_window.log_message(f"Web service error: {str(e)}")
            import traceback
            self.main_window.log_message(traceback.format_exc())
        finally:
            self.main_window.root.after(0, self.main_window.stop_bot)

    def _initialize_processing(self, service_name):
        """Initialize processing settings and load necessary data"""
        # Get settings from tabs
        translation_settings = self.main_window.translation_tab.get_settings()
        processing_settings = self.main_window.processing_tab.get_settings()

        # Validate input file
        input_file = translation_settings.get('input_file')
        if not input_file or not os.path.exists(input_file):
            self.main_window.log_message("Error: No valid input file selected")
            self.main_window.root.after(0, self.main_window.stop_bot)
            return None, None, None, None, None

        # Load translation prompt
        prompt_type = processing_settings.get('prompt_type')
        prompt = self.load_translation_prompt(input_file, prompt_type)
        if not prompt:
            self.main_window.log_message("Error: Failed to load translation prompt")
            self.main_window.root.after(0, self.main_window.stop_bot)
            return None, None, None, None, None

        # Read and validate input CSV
        df = pd.read_csv(input_file)
        if 'text' not in df.columns:
            self.main_window.log_message("Error: CSV file must have 'text' column")
            self.main_window.root.after(0, self.main_window.stop_bot)
            return None, None, None, None, None

        # Generate output path
        output_path = self.generate_output_path(input_file, prompt_type)

        # Apply ID filters
        df = self._apply_id_filters(df, translation_settings)
        all_input_ids = set(df['id'].tolist())

        return input_file, output_path, prompt, df, all_input_ids

    def _apply_id_filters(self, df, translation_settings):
        """Apply start_id and stop_id filters to dataframe"""
        return PromptHelper.apply_id_filters(
            df,
            translation_settings.get('start_id'),
            translation_settings.get('stop_id')
        )

    def _load_existing_results(self, output_path):
        """Load and analyze existing output file"""
        existing_results, completed_ids, failed_ids = PromptHelper.load_existing_results(output_path)

        if existing_results:
            self.main_window.log_message(f"Found existing output with {len(existing_results)} rows")
            self.main_window.log_message(f"  - Completed: {len(completed_ids)} rows")
            self.main_window.log_message(f"  - Failed/Empty: {len(failed_ids)} rows")

        return existing_results, completed_ids, failed_ids

    def _determine_ids_to_process(self, all_input_ids, existing_results, completed_ids, failed_ids):
        """Determine which IDs need to be processed"""
        missing_ids = all_input_ids - set(existing_results.keys())
        retry_ids = all_input_ids & failed_ids
        ids_to_process = sorted(missing_ids | retry_ids)

        if ids_to_process:
            self.main_window.log_message(f"IDs to process: {len(ids_to_process)} (prioritizing missing/failed IDs)")
            if len(ids_to_process) <= 10:
                self.main_window.log_message(f"  Processing IDs: {ids_to_process}")
            else:
                self.main_window.log_message(f"  First 10 IDs: {ids_to_process[:10]}...")
                self.main_window.log_message(f"  ID range: {min(ids_to_process)} to {max(ids_to_process)}")

        return ids_to_process

    def _process_batches(self, service_name, prompt, df, ids_to_process,
                         existing_results, all_input_ids, output_path):
        """Process all batches"""
        processing_settings = self.main_window.processing_tab.get_settings()
        batch_size = int(processing_settings.get('batch_size', 10))
        total_batches = (len(ids_to_process) - 1) // batch_size + 1 if len(ids_to_process) > 0 else 0

        critical_error_occurred = False

        for batch_num in range(1, total_batches + 1):
            if not self.running or critical_error_occurred:
                if critical_error_occurred:
                    self.main_window.log_message("Processing stopped due to critical error")
                else:
                    self.main_window.log_message("Processing stopped by user")
                break

            # Process single batch
            critical_error_occurred = self._process_single_batch(
                batch_num, total_batches, batch_size, ids_to_process,
                df, service_name, prompt, existing_results,
                output_path, all_input_ids
            )

            if critical_error_occurred:
                break

            # Delay between batches
            if batch_num < total_batches and self.running:
                self.main_window.log_message(f"Waiting 3 seconds before next batch...")
                time.sleep(3)

    def _process_single_batch(self, batch_num, total_batches, batch_size,
                              ids_to_process, df, service_name, prompt,
                              existing_results, output_path, all_input_ids):
        """Process a single batch and return whether critical error occurred"""
        # Get batch of IDs
        batch_start_idx = (batch_num - 1) * batch_size
        batch_end_idx = min(batch_start_idx + batch_size, len(ids_to_process))
        batch_ids = ids_to_process[batch_start_idx:batch_end_idx]

        # Get actual data for these specific IDs
        batch = df[df['id'].isin(batch_ids)].sort_values('id')

        if len(batch) == 0:
            self.main_window.log_message(f"Skipping batch {batch_num} - no data found for IDs: {batch_ids}")
            return False

        actual_batch_ids = batch['id'].tolist()
        self.main_window.log_message(
            f"Processing batch {batch_num}/{total_batches} "
            f"(IDs: {actual_batch_ids[0]}-{actual_batch_ids[-1]}, {len(batch)} rows)"
        )

        # Create batch text
        batch_text = self._create_batch_text(batch)

        # Call web service
        translations, error = self.web_bot_services.run_generic_bot(
            service_name, prompt, batch_text, len(batch)
        )

        # Check for critical errors
        if error and "Critical:" in error:
            self.main_window.log_message(f"Critical error encountered: {error}")
            self._mark_batch_as_failed(batch, existing_results, 'failed - critical error')
            return True  # Critical error occurred

        # Process results
        if translations:
            self._process_successful_batch(batch, translations, existing_results)
        else:
            self.main_window.log_message(f"Failed to get translations: {error}")
            self._mark_batch_as_failed(batch, existing_results, 'failed')

        # Save intermediate results
        self._save_intermediate_results(existing_results, output_path, all_input_ids)

        return False  # No critical error

    def _create_batch_text(self, batch):
        """Create numbered text from batch dataframe"""
        return PromptHelper.create_batch_text(batch)

    def _process_successful_batch(self, batch, translations, existing_results):
        """Process successful translation results"""
        self.main_window.log_message(f"Successfully processed {len(translations)} translations")
        for (idx, row), translation in zip(batch.iterrows(), translations):
            existing_results[row['id']] = {
                'id': row['id'],
                'raw': row['text'],
                'edit': translation,
                'status': ''
            }

    def _mark_batch_as_failed(self, batch, existing_results, status='failed'):
        """Mark all items in batch as failed"""
        for idx, row in batch.iterrows():
            existing_results[row['id']] = {
                'id': row['id'],
                'raw': row['text'],
                'edit': '',
                'status': status
            }

    def _save_intermediate_results(self, existing_results, output_path, all_input_ids):
        """Save intermediate results to file"""
        if existing_results:
            results_list = list(existing_results.values())
            results_df = pd.DataFrame(results_list)
            results_df_sorted = results_df.sort_values('id')
            results_df_sorted.to_csv(output_path, index=False)

            # Update progress
            self.main_window.translation_processor.current_output_file = output_path
            self.main_window.translation_processor.total_input_rows = len(all_input_ids)
            self.main_window.translation_processor.update_progress()

    def _generate_summary(self, existing_results, output_path):
        """Generate and display final summary"""
        if existing_results:
            results_list = list(existing_results.values())
            completed_count = sum(1 for r in results_list if r.get('edit') and str(r.get('edit')).strip())
            failed_count = sum(1 for r in results_list if not r.get('edit') or not str(r.get('edit')).strip())

            self.main_window.log_message(f"Processing completed!")
            self.main_window.log_message(f"Total: {len(results_list)} rows")
            self.main_window.log_message(f"Successful: {completed_count} rows")
            self.main_window.log_message(f"Failed: {failed_count} rows")
            self.main_window.log_message(f"Output saved to: {output_path}")

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
        return PromptHelper.generate_output_path(input_path, prompt_type)

    def load_translation_prompt(self, input_path, prompt_type):
        """Load translation prompt based on detected language and prompt type"""
        return PromptHelper.load_translation_prompt(
            input_path,
            prompt_type,
            self.main_window.log_message
        )

    def run_bot(self):
        """Legacy method - redirects to run_web_service"""
        # Get selected service
        processing_settings = self.main_window.processing_tab.get_settings()
        ai_service = processing_settings.get('ai_service', 'Perplexity')
        self.run_web_service(ai_service)