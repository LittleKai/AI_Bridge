import os
import pandas as pd


class PromptHelper:
    """Helper class for prompt and batch processing operations"""

    @staticmethod
    def detect_language(filepath):
        """Detect language from filename"""
        filename = os.path.basename(filepath)
        for lang in ['JP', 'EN', 'KR', 'CN', 'VI']:
            if lang in filename.upper():
                return lang
        return None

    @staticmethod
    def load_translation_prompt(input_path, prompt_type, log_func=None):
        """Load translation prompt based on detected language and prompt type"""
        source_lang = PromptHelper.detect_language(input_path)

        if not source_lang:
            if log_func:
                log_func("Error: Could not detect source language from filename")
                log_func("Filename should contain language code (CN, JP, EN, KR, VI)")
            return None

        if log_func:
            log_func(f"Loading prompt for source language: {source_lang}, type: {prompt_type}")

        try:
            prompt_file = "assets/translate_prompt.xlsx"
            if not os.path.exists(prompt_file):
                if log_func:
                    log_func("Error: Prompt file not found at assets/translate_prompt.xlsx")
                return None

            df = pd.read_excel(prompt_file)

            if 'type' in df.columns and source_lang in df.columns:
                prompt_row = df[df['type'] == prompt_type]
                if not prompt_row.empty:
                    prompt = prompt_row.iloc[0][source_lang]
                    if pd.notna(prompt) and prompt:
                        if log_func:
                            log_func(f"Successfully loaded prompt for {source_lang}, type: {prompt_type}")

                        prompt_with_format = prompt.strip() + "\n{count_info}\nVẫn giữ định dạng đánh số như bản gốc (1., 2., ...).\n" \
                                                              "Đây là văn bản cần chuyển ngữ:\n{text}"
                        # "Chỉ trả về các dòng dịch được đánh số, không viết thêm bất kỳ nội dung nào khác.\n" \ \
                        return prompt_with_format
                    else:
                        if log_func:
                            log_func(f"Error: Prompt is empty for {source_lang}, type: {prompt_type}")
                else:
                    if log_func:
                        log_func(f"Error: Prompt type '{prompt_type}' not found in file")
            else:
                if log_func:
                    if 'type' not in df.columns:
                        log_func("Error: 'type' column not found in prompt file")
                    if source_lang not in df.columns:
                        log_func(f"Error: Language column '{source_lang}' not found in prompt file")
                        available_langs = [col for col in df.columns if col not in ['type', 'description']]
                        log_func(f"Available languages: {', '.join(available_langs)}")

            return None

        except Exception as e:
            if log_func:
                log_func(f"Error loading prompt file: {e}")
            return None

    @staticmethod
    def generate_output_path(input_path, prompt_type):
        """Generate output path based on input file name and prompt type"""
        input_filename = os.path.basename(input_path)

        # Detect language from filename
        lang_folder = PromptHelper.detect_language(input_path)
        if not lang_folder:
            lang_folder = "Other"

        # Create output filename
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

    @staticmethod
    def apply_id_filters(df, start_id, stop_id):
        """Apply start_id and stop_id filters to dataframe"""
        try:
            if start_id:
                start_id = int(start_id)
                df = df[df['id'] >= start_id]

            if stop_id:
                stop_id = int(stop_id)
                df = df[df['id'] <= stop_id]
        except:
            pass

        return df

    @staticmethod
    def load_existing_results(output_path):
        """Load and analyze existing output file"""
        existing_results = {}
        completed_ids = set()
        failed_ids = set()

        if os.path.exists(output_path):
            try:
                existing_df = pd.read_csv(output_path)
                if not existing_df.empty:
                    for _, row in existing_df.iterrows():
                        row_id = row['id']
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
            except:
                pass

        return existing_results, completed_ids, failed_ids

    @staticmethod
    def create_batch_text(batch_df):
        """Create numbered text from batch dataframe"""
        batch_lines = []
        for j, (_, row) in enumerate(batch_df.iterrows(), 1):
            batch_lines.append(f"{j}. {row['text']}")
        return "\n".join(batch_lines)

    @staticmethod
    def save_results(existing_results, output_path):
        """Save results to CSV file"""
        if existing_results:
            results_list = list(existing_results.values())
            results_df = pd.DataFrame(results_list)
            results_df_sorted = results_df.sort_values('id')
            results_df_sorted.to_csv(output_path, index=False)
            return True
        return False

    @staticmethod
    def find_next_batch(df, output_path, batch_size):
        """Find the next batch of IDs that need processing"""
        if df is None or df.empty:
            return None

        if batch_size <= 0:
            return None

        all_input_ids = set(df['id'].tolist())

        # Load existing results
        _, completed_ids, _ = PromptHelper.load_existing_results(output_path)

        # Find IDs to process
        ids_to_process = sorted(all_input_ids - completed_ids)

        if not ids_to_process:
            return None

        # Get next batch
        batch_ids = ids_to_process[:min(batch_size, len(ids_to_process))]
        batch_df = df[df['id'].isin(batch_ids)].sort_values('id')

        # Return a copy to ensure data persists
        return batch_df.copy() if not batch_df.empty else None