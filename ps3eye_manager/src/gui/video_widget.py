"""
Video widget for displaying video from the camera
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

class VideoWidget(QLabel):
    """Video widget for displaying video from the camera"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")
    
    def update_frame(self, frame):
        """Update the displayed frame"""
        if frame is None:
            return
        
        try:
            # Convert frame for display
            if frame.ndim == 2:  # Grayscale
                h, w = frame.shape
                bytes_per_line = w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
            else:  # RGB/RGBA
                h, w, ch = frame.shape
                if ch == 3:  # RGB
                    bytes_per_line = 3 * w
                    qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                else:  # RGBA
                    bytes_per_line = 4 * w
                    qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
            
            # Scale frame maintaining proportions
            pixmap = QPixmap.fromImage(qimg)
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error updating frame: {e}")
    
    def resizeEvent(self, event):
        """Handle widget resizing"""
        super().resizeEvent(event)
        # Update pixmap size if present
        if self.pixmap():
            scaled_pixmap = self.pixmap().scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
