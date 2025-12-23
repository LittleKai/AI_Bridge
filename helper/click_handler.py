import pyautogui
import random
import time
from typing import Tuple, Optional
from helper.recognizer import match_template

def find_and_click(img_path: str, region: Optional[Tuple[int, int, int, int]] = None,
                   max_attempts: int = 1, delay_between: float = 1.0,
                   click: bool = True, confidence: float = 0.8, log_attempts: bool = True,
                   use_random: bool = True, return_all_coords: bool = False,
                   check_stop_func=None, log_func=None):
    """
    Find and optionally click an image on screen with random clicking support

    Args:
        img_path: Path to the image to find
        region: Optional (left, top, width, height) region to search in
        max_attempts: Number of attempts to find the image
        delay_between: Delay between attempts in seconds
        click: Whether to click when found
        confidence: Template matching confidence (0-1)
        log_attempts: Whether to log attempt failures
        use_random: Whether to click at random position within the box (default True)
        return_all_coords: Whether to return all 6 coordinates (left, top, right, bottom, center_x, center_y)
        check_stop_func: Function to check if should stop
        log_func: Function to log messages

    Returns:
        If return_all_coords is True: Tuple of (left, top, right, bottom, center_x, center_y)
        Otherwise: Tuple of (x, y) coordinates if found, None otherwise
    """
    time.sleep(1)

    # Check stop condition before starting
    if check_stop_func and check_stop_func():
        return None

    # Set default region to full screen if not provided
    if not region:
        screen_width, screen_height = pyautogui.size()
        region = (0, 0, screen_width, screen_height)

    # Extract filename for logging
    filename = img_path.split('/')[-1].replace('.png', '')

    for attempt in range(max_attempts):
        # Check stop condition before each attempt
        if check_stop_func and check_stop_func():
            return None

        try:
            # Try to locate the image
            boxes = match_template(img_path, threshold=confidence, region=region)

            # Check if any matches found
            if boxes and len(boxes) > 0:
                # Get first match
                x, y, w, h = boxes[0]

                # Calculate all coordinates
                left, top = x, y
                right, bottom = x + w, y + h
                center_x = x + w // 2
                center_y = y + h // 2

                # Calculate click position based on use_random
                if use_random:
                    # Random position within the box (with some margin from edges)
                    margin_x = max(2, w // 30)  # 30% margin or minimum 2px
                    margin_y = max(2, h // 30)
                    click_x = random.randint(x + margin_x, x + w - margin_x)
                    click_y = random.randint(y + margin_y, y + h - margin_y)
                else:
                    # Center of the box
                    click_x = center_x
                    click_y = center_y

                if click:
                    # Check stop condition before clicking
                    if check_stop_func and check_stop_func():
                        return None

                    # Click at calculated position
                    pyautogui.moveTo(click_x, click_y, duration=0.175)
                    pyautogui.click()
                    if log_func:
                        log_func(f"Clicked {filename}")

                    if return_all_coords:
                        return (left, top, right, bottom, center_x, center_y)
                    else:
                        return (click_x, click_y)
                else:
                    # Just return the position without clicking
                    if log_func and log_attempts:
                        log_func(f"Found {filename} at ({center_x}, {center_y})")

                    if return_all_coords:
                        return (left, top, right, bottom, center_x, center_y)
                    else:
                        return (center_x, center_y)

        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            if log_func:
                log_func(f"Error processing {filename}: {e}")

        # Delay between attempts if not the last attempt
        if attempt < max_attempts - 1:
            if check_stop_func and check_stop_func():
                return None
            time.sleep(delay_between)

    # Log failure if enabled and multiple attempts were made
    if log_attempts and max_attempts > 1:
        if log_func:
            log_func(f"Failed to find {filename} after {max_attempts} attempts")

    return None