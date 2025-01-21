"""
Main entry point of the application
"""
import os
import sys
from pathlib import Path

# Add the src directory path to PYTHONPATH
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import logging
import subprocess
import time
import socket
import signal
import atexit
from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from gui.main_window import MainWindow
from core.camera_service import CLEyeService
from utils.logging_config import setup_logging

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def start_camera_service() -> Optional[CLEyeService]:
    """Start the camera service"""
    try:
        # Check if the port is already in use
        if is_port_in_use(50000):
            logging.error("Port 50000 is already in use")
            return None
        
        # Create and start the service
        service = CLEyeService()
        if not service.start():
            logging.error("Unable to start the camera service")
            return None
        
        return service
        
    except FileNotFoundError as e:
        # Driver not found - show a message to the user
        logging.error(f"Error starting the service: {e}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("PS3 Eye Camera Driver Not Found")
        msg.setText(str(e))
        msg.setInformativeText(
            "The application will run in limited mode without camera access.\n"
            "Install the drivers and restart the application to use the camera."
        )
        msg.exec_()
        return None
    except Exception as e:
        # Other errors
        logging.error(f"Error starting the service: {e}")
        return None

def stop_camera_service(service: Optional[CLEyeService]):
    """Stop the camera service"""
    if service:
        try:
            service.cleanup()
        except Exception as e:
            logging.error(f"Error stopping the service: {e}")

def create_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    return palette

def main():
    """Main function"""
    try:
        # Configure logging
        setup_logging()
        logging.info("=== PS3 Eye Manager ===")
        logging.info("Version: 1.0.0")
        logging.info(f"Base directory: {src_dir}")
        
        # Create the Qt application
        app = QApplication(sys.argv)
        
        # Set the dark theme
        app.setStyle('Fusion')
        app.setPalette(create_dark_palette())
        logging.info("Dark theme applied")
        logging.info("Qt application configured successfully")
        
        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Run the application
        return app.exec_()
        
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
        QMessageBox.critical(None, "Error", f"The application closed with an error\n{str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
