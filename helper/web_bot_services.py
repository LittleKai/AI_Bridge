import time
import pyautogui
import pyperclip
import re
from helper.click_handler import find_and_click


class WebBotServices:
    """Web automation services for various AI platforms"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.running = False

    def run_generic_bot(self, service_name, prompt, batch_text, batch_size):
        """Generic bot runner for all AI web services"""
        try:
            # Service configuration mapping
            service_config = {
                'Perplexity': {
                    'folder': 'Perplexity',
                    'input_box': 'text_input_box.png',
                    'send_btn': 'send_btn.png',
                    'processing_indicator': 'is_processing.png',
                    'action_icons': 'action_icons.png',
                    'copy_btn': 'copy_btn.png',
                    'more_btn': 'more_btn.png',
                    'delete_btn': 'delete_btn.png',
                    'confirm_btn': 'confirm_btn.png',
                    'input_click_offset_y': -20
                },
                'Gemini': {
                    'folder': 'Gemini',
                    'input_box': 'text_input_box.png',
                    'send_btn': 'send_btn.png',
                    'processing_indicator': 'is_processing.png',
                    'action_icons': 'action_icons.png',
                    'copy_btn': 'copy_btn.png',
                    'more_btn': 'more_btn.png',
                    'delete_btn': 'delete_btn.png',
                    'confirm_btn': 'confirm_btn.png',
                    'input_click_offset_y': 0
                },
                'ChatGPT': {
                    'folder': 'ChatGPT',
                    'input_box': 'text_input_box.png',
                    'send_btn': 'send_btn.png',
                    'processing_indicator': 'is_processing.png',
                    'action_icons': 'action_icons.png',
                    'copy_btn': 'copy_btn.png',
                    'more_btn': 'more_btn.png',
                    'delete_btn': 'delete_btn.png',
                    'confirm_btn': 'confirm_btn.png',
                    'input_click_offset_y': 0
                },
                'Claude': {
                    'folder': 'Claude',
                    'input_box': 'text_input_box.png',
                    'send_btn': 'send_btn.png',
                    'processing_indicator': 'is_processing.png',
                    'action_icons': 'action_icons.png',
                    'copy_btn': 'copy_btn.png',
                    'more_btn': 'more_btn.png',
                    'delete_btn': 'delete_btn.png',
                    'confirm_btn': 'confirm_btn.png',
                    'input_click_offset_y': 0
                },
                'Grok': {
                    'folder': 'Grok',
                    'input_box': 'text_input_box.png',
                    'send_btn': 'send_btn.png',
                    'processing_indicator': 'is_processing.png',
                    'action_icons': 'action_icons.png',
                    'copy_btn': 'copy_btn.png',
                    'more_btn': 'more_btn.png',
                    'delete_btn': 'delete_btn.png',
                    'confirm_btn': 'confirm_btn.png',
                    'input_click_offset_y': 0
                }
            }

            if service_name not in service_config:
                self.main_window.log_message(f"Error: Service {service_name} not configured")
                return None, f"Service {service_name} not configured"

            config = service_config[service_name]
            assets_folder = f"assets/{config['folder']}"

            # Step 1: Find and click input box
            box_coords = find_and_click(
                f"{assets_folder}/{config['input_box']}",
                click=False,
                max_attempts=5,
                delay_between=2.0,
                confidence=0.85,
                return_all_coords=True
            )

            if not box_coords:
                error_msg = f"Critical: {service_name} input box not found! Stopping bot."
                self.main_window.log_message(error_msg)
                self.main_window.log_message(f"Make sure {service_name} website is open and visible")
                self.main_window.status_section.set_bot_status("Bot stopped - Image not found", "red")
                return None, error_msg

            # Extract coordinates
            left, top, right, bottom, center_x, center_y = box_coords

            # Calculate click position with offset
            click_x = center_x
            click_y = center_y + config['input_click_offset_y']

            # Click on the input box
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)

            # Step 2: Clear and input text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)

            # Combine prompt with batch text - ensure formatting is correct
            full_text = prompt.format(
                count_info=f"Source text consists of {batch_size} numbered lines from 1 to {batch_size}.",
                text=batch_text
            )

            # Copy to clipboard and paste
            pyperclip.copy(full_text)
            pyautogui.hotkey('ctrl', 'v')
            self.main_window.log_message(f"Pasted prompt with {batch_size} lines to {service_name}")
            time.sleep(0.5)

            # Step 3: Send message
            send_btn_coords = find_and_click(
                f"{assets_folder}/{config['send_btn']}",
                click=False,
                max_attempts=5,
                delay_between=2.0,
                confidence=0.85,
                return_all_coords=True
            )

            if send_btn_coords:
                left, top, right, bottom, center_x, center_y = send_btn_coords
                pyautogui.click(center_x, center_y)
                self.main_window.log_message(f"Clicked send button in {service_name}")
            else:
                # Send button is critical - stop if not found
                error_msg = f"Critical: {service_name} send button not found! Stopping bot."
                self.main_window.log_message(error_msg)
                self.main_window.status_section.set_bot_status("Bot stopped - Image not found", "red")
                return None, error_msg

            # Step 4: Wait for processing to complete
            screen_width, screen_height = pyautogui.size()
            processing_region = (0, screen_height - 300, screen_width, 300)  # Bottom 300px of screen

            is_processing = True
            attempt_count = 0
            max_wait_attempts = 60  # Maximum 5 minutes wait

            self.main_window.log_message(f"Waiting for {service_name} to process...")
            while is_processing and attempt_count < max_wait_attempts:
                processing_icon = find_and_click(
                    f"{assets_folder}/{config['processing_indicator']}",
                    region=processing_region,
                    click=False,
                    max_attempts=1,
                    confidence=0.85,
                    log_func=None  # Don't log each check
                )

                if processing_icon:
                    time.sleep(5.0)
                    attempt_count += 1
                    if attempt_count % 6 == 0:  # Log every 30 seconds
                        self.main_window.log_message(f"Still processing... ({attempt_count * 5} seconds elapsed)")
                else:
                    is_processing = False
                    self.main_window.log_message("Processing completed")

            # Step 5: Scroll to bottom and find copy button
            for i in range(2):
                pyautogui.click(screen_width // 2, screen_height // 2)
                time.sleep(0.5)
                pyautogui.press('end')
                time.sleep(0.5)

            # Step 6: Find action icons and copy response
            action_icons = find_and_click(
                f"{assets_folder}/{config['action_icons']}",
                click=False,
                max_attempts=5,
                delay_between=1.0,
                confidence=0.85,
                return_all_coords=False
            )

            if not action_icons:
                error_msg = f"Critical: {service_name} action icons not found! Stopping bot."
                self.main_window.log_message(error_msg)
                self.main_window.status_section.set_bot_status("Bot stopped - Image not found", "red")
                # Try to clean up before stopping
                self.cleanup_chat(service_name, config, assets_folder)
                return None, error_msg

            # Define region around action icons for copy button
            action_x, action_y = action_icons
            action_region = (action_x - 100, action_y - 100, 200, 200)

            copy_result = find_and_click(
                f"{assets_folder}/{config['copy_btn']}",
                region=action_region,
                click=True,
                max_attempts=3,
                delay_between=1.0,
                confidence=0.85
            )

            if not copy_result:
                error_msg = f"Critical: {service_name} copy button not found! Stopping bot."
                self.main_window.log_message(error_msg)
                self.main_window.status_section.set_bot_status("Bot stopped - Image not found", "red")
                # Try to clean up before stopping
                self.cleanup_chat(service_name, config, assets_folder)
                return None, error_msg

            time.sleep(0.5)
            # Get response from clipboard
            response_text = pyperclip.paste()

            # Parse the response
            translated_lines = self.parse_numbered_text(response_text, batch_size)

            # Clean up chat
            self.cleanup_chat(service_name, config, assets_folder)

            return translated_lines, None

        except Exception as e:
            error_msg = f"{service_name} bot error: {str(e)}"
            self.main_window.log_message(error_msg)
            self.main_window.status_section.set_bot_status("Bot stopped - Error", "red")
            return None, error_msg

    def cleanup_chat(self, service_name, config, assets_folder):
        """Generic cleanup function for all services"""
        try:
            self.main_window.log_message(f"Cleaning up {service_name} chat...")

            # Find chat option region at top of screen
            screen_width, _ = pyautogui.size()

            if service_name == "Perplexity":
                top_region = (screen_width/2, 0, screen_width, 100)
            else:
                top_region = (0, 0, screen_width/2, 100)

            # Click more/options button
            more_clicked = find_and_click(
                f"{assets_folder}/{config['more_btn']}",
                region=top_region,
                click=True,
                max_attempts=3,
                delay_between=1.0,
                confidence=0.85
            )

            if more_clicked:
                time.sleep(0.5)

                # Click delete button
                delete_clicked = find_and_click(
                    f"{assets_folder}/{config['delete_btn']}",
                    click=True,
                    max_attempts=3,
                    delay_between=1.0,
                    confidence=0.85
                )

                if delete_clicked:
                    time.sleep(0.5)

                    # Click confirm button
                    confirm_clicked = find_and_click(
                        f"{assets_folder}/{config['confirm_btn']}",
                        click=True,
                        max_attempts=3,
                        delay_between=1.0,
                        confidence=0.85
                    )

                    if confirm_clicked:
                        self.main_window.log_message(f"{service_name} chat deleted successfully")
                    else:
                        self.main_window.log_message("Failed to confirm deletion")
                else:
                    self.main_window.log_message("Failed to click delete button")
            else:
                self.main_window.log_message("Failed to click more button")

        except Exception as e:
            self.main_window.log_message(f"Cleanup error: {str(e)}")

    def parse_numbered_text(self, text, expected_count):
        """Parse numbered text into list of translations"""
        lines = []

        # Find lines with pattern "number. text"
        pattern = r'(\d+)\.\s*(.*?)(?=\n\d+\.|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            # Create dictionary with line number as key
            numbered_lines = {int(num): content.strip() for num, content in matches}

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
                lines.append(cleaned)

            # Pad with empty strings if needed
            while len(lines) < expected_count:
                lines.append("")

        return lines
