"""
Widget per la visualizzazione del video
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

class VideoWidget(QLabel):
    """Widget per la visualizzazione del video dalla telecamera"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")
    
    def update_frame(self, frame):
        """Aggiorna il frame visualizzato"""
        if frame is None:
            return
        
        try:
            # Converti il frame per la visualizzazione
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
            
            # Scala il frame mantenendo le proporzioni
            pixmap = QPixmap.fromImage(qimg)
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Errore nell'aggiornamento del frame: {e}")
    
    def resizeEvent(self, event):
        """Gestisce il ridimensionamento del widget"""
        super().resizeEvent(event)
        # Aggiorna le dimensioni del pixmap se presente
        if self.pixmap():
            scaled_pixmap = self.pixmap().scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
