"""
Finestra principale dell'applicazione
"""
import os
import time
import logging
import numpy as np
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSystemTrayIcon, QMenu,
    QAction, QMessageBox, QSizePolicy, QStatusBar,
    QDockWidget
)
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSlot

from core.camera_service import CLEyeService
from gui.settings_panel import SettingsPanel

class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione"""

    def __init__(self):
        super().__init__()
        
        # Inizializza il servizio telecamera
        self.camera_service = CLEyeService()
        
        # Setup UI
        self.setWindowTitle("PS3 Eye Manager")
        self.setMinimumSize(1024, 768)
        
        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principale
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Area visualizzazione frame
        self.frame_label = QLabel()
        self.frame_label.setMinimumSize(640, 480)
        self.frame_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.frame_label)
        
        # Barra degli strumenti
        toolbar = self.addToolBar("Strumenti")
        
        # Azione Screenshot
        screenshot_action = QAction(QIcon.fromTheme("camera-photo"), "Screenshot", self)
        screenshot_action.setStatusTip("Cattura uno screenshot")
        screenshot_action.triggered.connect(self._take_screenshot)
        toolbar.addAction(screenshot_action)
        
        # Azione Registra Video
        self.record_action = QAction(QIcon.fromTheme("media-record"), "Registra", self)
        self.record_action.setStatusTip("Avvia/Ferma la registrazione video")
        self.record_action.setCheckable(True)
        self.record_action.triggered.connect(self._toggle_recording)
        toolbar.addAction(self.record_action)
        
        # Azione Webcam Virtuale
        self.virtual_camera_action = QAction(QIcon.fromTheme("camera-web"), "Webcam Virtuale", self)
        self.virtual_camera_action.setStatusTip("Abilita/Disabilita webcam virtuale")
        self.virtual_camera_action.setCheckable(True)
        self.virtual_camera_action.setChecked(True)  # Abilitata di default
        self.virtual_camera_action.triggered.connect(self._toggle_virtual_camera)
        toolbar.addAction(self.virtual_camera_action)
        
        # Pannello impostazioni
        settings_dock = QDockWidget("Impostazioni", self)
        settings_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.settings_panel = SettingsPanel()
        settings_dock.setWidget(self.settings_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, settings_dock)
        
        # Collega i segnali del pannello impostazioni
        self.settings_panel.parameter_changed.connect(self._on_parameter_changed)
        self.settings_panel.resolution_changed.connect(self._on_resolution_changed)
        self.settings_panel.color_mode_changed.connect(self._on_color_mode_changed)
        
        # Barra di stato
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Label per FPS e risoluzione
        self.fps_label = QLabel()
        self.resolution_label = QLabel()
        self.status_bar.addPermanentWidget(self.resolution_label)
        self.status_bar.addPermanentWidget(self.fps_label)
        
        # Timer per aggiornamento UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(33)  # ~30 FPS
        
        # Avvia la telecamera
        if self.camera_service.start(frame_callback=self._update_frame, enable_virtual_camera=True):
            # Aggiorna il pannello impostazioni con i valori attuali
            self.settings_panel.update_from_camera(self.camera_service.camera)
        else:
            QMessageBox.critical(self, "Errore", "Impossibile avviare la telecamera")
            
    def _update_frame(self, frame: np.ndarray):
        """Callback per l'aggiornamento del frame"""
        try:
            if frame is None or frame.size == 0:
                return
                
            # Converti il frame in QImage
            height, width = frame.shape[:2]
            bytes_per_line = width * 4
            
            q_img = QImage(
                frame.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGBA8888
            )
            
            # Scala l'immagine mantenendo l'aspect ratio
            scaled_pixmap = QPixmap.fromImage(q_img).scaled(
                self.frame_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Aggiorna il label
            self.frame_label.setPixmap(scaled_pixmap)
            
            # Aggiorna il label della risoluzione
            self.resolution_label.setText(f"{width}x{height}")
            
        except Exception as e:
            logging.error(f"Errore nell'aggiornamento del frame: {e}")
            
    def _update_ui(self):
        """Aggiorna l'interfaccia utente"""
        try:
            status = self.camera_service.get_status()
            
            # Aggiorna la barra di stato
            if status['running']:
                fps = status.get('fps', 0)
                self.fps_label.setText(f"FPS: {fps:.1f}")
            else:
                self.fps_label.setText("Camera: Ferma")
                
        except Exception as e:
            logging.error(f"Errore nell'aggiornamento UI: {e}")
            
    def _on_parameter_changed(self, param, value):
        """Gestisce il cambiamento di un parametro della telecamera"""
        try:
            self.camera_service.camera.set_parameter(param, value)
        except Exception as e:
            logging.error(f"Errore nell'impostazione del parametro {param}: {e}")
            
    def _on_resolution_changed(self, resolution):
        """Gestisce il cambiamento della risoluzione"""
        # TODO: Implementare il cambio di risoluzione
        pass
        
    def _on_color_mode_changed(self, color_mode):
        """Gestisce il cambiamento della modalità colore"""
        # TODO: Implementare il cambio di modalità colore
        pass
        
    def _take_screenshot(self):
        """Cattura uno screenshot"""
        try:
            frame = self.camera_service.get_frame()
            if frame is not None:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshots_dir = Path.home() / "PS3EyeManager" / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                
                filename = screenshots_dir / f"screenshot_{timestamp}.png"
                pixmap = self.frame_label.pixmap()
                if pixmap and pixmap.save(str(filename)):
                    self.status_bar.showMessage(f"Screenshot salvato: {filename}", 3000)
                else:
                    raise RuntimeError("Impossibile salvare lo screenshot")
                    
        except Exception as e:
            logging.error(f"Errore nella cattura dello screenshot: {e}")
            self.status_bar.showMessage("Errore nella cattura dello screenshot", 3000)
            
    def _toggle_recording(self, checked: bool):
        """Avvia/Ferma la registrazione video"""
        # TODO: Implementare la registrazione video
        pass
        
    def _toggle_virtual_camera(self, checked: bool):
        """Abilita/Disabilita la webcam virtuale"""
        try:
            if checked:
                # Riavvia il servizio con la webcam virtuale abilitata
                self.camera_service.stop()
                if self.camera_service.start(frame_callback=self._update_frame, enable_virtual_camera=True):
                    self.status_bar.showMessage("Webcam virtuale abilitata", 3000)
                    self.settings_panel.update_from_camera(self.camera_service.camera)
                else:
                    self.virtual_camera_action.setChecked(False)
                    self.status_bar.showMessage("Errore nell'abilitazione della webcam virtuale", 3000)
            else:
                # Riavvia il servizio senza webcam virtuale
                self.camera_service.stop()
                if self.camera_service.start(frame_callback=self._update_frame, enable_virtual_camera=False):
                    self.status_bar.showMessage("Webcam virtuale disabilitata", 3000)
                    self.settings_panel.update_from_camera(self.camera_service.camera)
                else:
                    self.virtual_camera_action.setChecked(True)
                    self.status_bar.showMessage("Errore nella disabilitazione della webcam virtuale", 3000)
                    
        except Exception as e:
            logging.error(f"Errore nel toggle della webcam virtuale: {e}")
            self.status_bar.showMessage("Errore nella gestione della webcam virtuale", 3000)
            
    def closeEvent(self, event):
        """Gestisce la chiusura della finestra"""
        try:
            if self.camera_service:
                self.camera_service.stop()
        except Exception as e:
            logging.error(f"Errore nella chiusura della finestra: {e}")
        event.accept()
