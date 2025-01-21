"""
Application settings for PS3 Eye Manager
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

class Settings:
    """Class for managing settings"""
    
    def __init__(self):
        # Directory base
        self.base_dir = Path(__file__).parent.parent.parent
        
        # Working directory
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "config"
        self.resources_dir = self.base_dir / "resources"
        
        # Create directories if they don't exist
        self.logs_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        self.resources_dir.mkdir(exist_ok=True)
        
        # Configuration file
        self.config_file = self.config_dir / "settings.json"
        
        # Default settings
        self.default_settings = {
            "camera": {
                "resolution": "VGA",  # VGA or QVGA
                "fps": 60,
                "auto_start": True,
                "auto_reconnect": True,
                "timeout": 5.0  # seconds
            },
            "server": {
                "host": "localhost",
                "port": 50000,
                "max_clients": 5,
                "buffer_size": 1024 * 1024  # 1MB
            },
            "virtual_camera": {
                "enabled": False,
                "device_name": "PS3 Eye Virtual Camera",
                "width": 640,
                "height": 480,
                "fps": 30
            },
            "ui": {
                "theme": "dark",
                "language": "it",
                "window_size": [800, 600],
                "always_on_top": False,
                "start_minimized": False
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True,
                "max_size_mb": 10,
                "backup_count": 3,
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            }
        }
        
        # Load settings
        self.settings = self.load_settings()
        
        # Assign settings to attributes
        self.camera = self.settings["camera"]
        self.server = self.settings["server"]
        self.virtual_camera = self.settings["virtual_camera"]
        self.ui = self.settings["ui"]
        self.logging = self.settings["logging"]
        
        # Dark theme flag
        self.dark_theme = self.settings["ui"]["theme"] == "dark"
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self.default_settings.copy()
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logging.info("Settings saved successfully")
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from settings"""
        try:
            keys = key.split('.')
            value = self.settings
            for k in keys:
                value = value[k]
            return value
        except:
            return default
    
    def set(self, key: str, value: Any):
        """Set a value in settings"""
        try:
            keys = key.split('.')
            target = self.settings
            for k in keys[:-1]:
                target = target[k]
            target[keys[-1]] = value
            self.save_settings()
        except Exception as e:
            logging.error(f"Error setting value {key}: {e}")

def setup_logging():
    """Configure logging system"""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_file = logs_dir / "ps3eye_manager.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file)
            ]
        )
        
        logging.info("Logging system configured successfully")
        
    except Exception as e:
        print(f"Error configuring logging: {e}")
        sys.exit(1)

# Global instance of settings
settings = Settings()
