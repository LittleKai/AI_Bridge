import json
import os
from helper.key_encryption import KeyEncryption


class WindowManager:
    """Manages window settings, positioning, and file I/O operations"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.key_encryption = KeyEncryption()

        # Default window settings
        self.window_settings = {
            'width': 500,
            'height': 750,
            'x': 1400,
            'y': 20
        }

        # Store original size for compact mode toggle
        self.original_size = {'width': 500, 'height': 750}

    def load_initial_settings(self):
        """Load initial settings including window position before GUI setup"""
        try:
            if os.path.exists('bot_settings.json'):
                with open('bot_settings.json', 'r') as f:
                    settings = json.load(f)

                # Load window settings if they exist
                if 'window' in settings:
                    self.window_settings.update(settings['window'])
                    # Store original size
                    self.original_size = {
                        'width': self.window_settings.get('width', 500),
                        'height': self.window_settings.get('height', 750)
                    }

                # Load app key early if it exists
                if 'app_key' in settings:
                    self.main_window.app_key_var.set(settings.get('app_key', ''))

        except Exception as e:
            print(f"Warning: Could not load initial settings: {e}")

    def setup_window(self):
        """Setup window with loaded settings"""
        settings = self.window_settings

        width = max(500, settings.get('width', 500))
        height = max(750, settings.get('height', 750))

        # Get saved position or use default
        screen_width = self.main_window.root.winfo_screenwidth()
        screen_height = self.main_window.root.winfo_screenheight()

        # Use saved position if available, otherwise use default
        if 'x' in settings and 'y' in settings:
            x = settings['x']
            y = settings['y']
        else:
            # Default position: right half of screen + 20px, y = 20
            default_x = max(20, screen_width // 2) + 20
            default_y = 20
            x = default_x
            y = default_y

        # Ensure window fits on screen
        if x + width > screen_width:
            x = max(0, screen_width - width)
        if y + height > screen_height:
            y = max(0, screen_height - height)

        # Ensure minimum position values
        x = max(0, x)
        y = max(0, y)

        # Set window properties
        self.main_window.root.minsize(500, 750)
        self.main_window.root.geometry(f"{width}x{height}+{x}+{y}")
        self.main_window.root.resizable(True, True)
        self.main_window.root.attributes('-topmost', True)

    def save_settings(self):
        """Save all settings to file with encrypted API keys"""
        try:
            # Check if compact_mode exists before accessing it
            if hasattr(self.main_window, 'compact_mode'):
                # Save current window settings (only if not in compact mode)
                if not self.main_window.compact_mode:
                    try:
                        self.main_window.root.update_idletasks()
                        self.window_settings = {
                            'width': self.main_window.root.winfo_width(),
                            'height': self.main_window.root.winfo_height(),
                            'x': self.main_window.root.winfo_x(),
                            'y': self.main_window.root.winfo_y()
                        }
                        # Update original size
                        self.original_size = {
                            'width': self.window_settings['width'],
                            'height': self.window_settings['height']
                        }
                    except:
                        pass
            else:
                # If compact_mode doesn't exist yet, save current window settings
                try:
                    self.main_window.root.update_idletasks()
                    self.window_settings = {
                        'width': self.main_window.root.winfo_width(),
                        'height': self.main_window.root.winfo_height(),
                        'x': self.main_window.root.winfo_x(),
                        'y': self.main_window.root.winfo_y()
                    }
                except:
                    pass

            # Get settings from tabs if they exist
            tab_settings = {}
            if hasattr(self.main_window, 'translation_tab') and hasattr(self.main_window, 'processing_tab'):
                tab_settings = self.main_window.get_current_settings()

            # Add application key to settings
            app_key = ""
            if hasattr(self.main_window, 'app_key_var'):
                app_key = self.main_window.app_key_var.get()

            # Process processing settings
            processing_settings = tab_settings.get('processing', {})

            # Encrypt API keys in processing settings
            if 'api_configs' in processing_settings:
                for service, config in processing_settings['api_configs'].items():
                    if 'keys' in config and config['keys']:
                        # Only encrypt plain text keys
                        encrypted_keys = []
                        for key in config['keys']:
                            if key:
                                encrypted = self.key_encryption.encrypt_key(key)
                                encrypted_keys.append(encrypted)
                        config['keys'] = encrypted_keys
                    else:
                        config['keys'] = []

            # Combine all settings
            all_settings = {
                'window': self.window_settings,
                'translation': tab_settings.get('translation', {}),
                'processing': processing_settings,
                'converter': tab_settings.get('converter', {}),
                'app_key': app_key
            }

            # Save to file
            with open('bot_settings.json', 'w') as f:
                json.dump(all_settings, f, indent=2)

        except Exception as e:
            # Only log if main_window has log_message method
            if hasattr(self.main_window, 'log_message'):
                self.main_window.log_message(f"Warning: Could not save settings: {e}")
            else:
                print(f"Warning: Could not save settings: {e}")

    def load_tab_settings(self):
        """Load tab settings after tabs are created with decrypted API keys"""
        try:
            if not os.path.exists('bot_settings.json'):
                return
    
            with open('bot_settings.json', 'r') as f:
                settings = json.load(f)
    
            # Load translation settings
            if 'translation' in settings:
                self.main_window.translation_tab.load_settings(settings['translation'])
    
            # Process and decrypt API keys before loading
            if 'processing' in settings:
                processing_settings = settings['processing'].copy()
    
                # Decrypt API keys if they exist
                if 'api_configs' in processing_settings:
                    for service, config in processing_settings['api_configs'].items():
                        if 'keys' in config and config['keys']:
                            try:
                                # Decrypt each key individually
                                decrypted_keys = []
                                for encrypted_key in config['keys']:
                                    if encrypted_key:
                                        decrypted = self.key_encryption.decrypt_key(encrypted_key)
                                        decrypted_keys.append(decrypted)
                                config['keys'] = decrypted_keys
                            except Exception as e:
                                print(f"Warning: Could not decrypt keys for {service}: {e}")
                                config['keys'] = []
                        else:
                            config['keys'] = []
    
                # Load processing settings with decrypted keys
                self.main_window.processing_tab.load_settings(processing_settings)
    
            # Load converter settings
            if 'converter' in settings:
                self.main_window.converter_tab.load_settings(settings['converter'])
    
        except Exception as e:
            self.main_window.log_message(f"Warning: Could not load tab settings: {e}")