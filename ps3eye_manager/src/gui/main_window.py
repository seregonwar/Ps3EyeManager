"""
Main window of the application
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
import cv2

from core.camera_service import CLEyeService
from gui.settings_panel import SettingsPanel

class MainWindow(QMainWindow):
    """Main window of the application"""

    def __init__(self):
        super().__init__()
        
        # Initialize camera service
        self.camera_service = CLEyeService()
        
        # Recording variables
        self._recording = False
        self._video_writer = None
        self._recording_start_time = None
        
        # Setup UI
        self.setWindowTitle("PS3 Eye Manager")
        self.setMinimumSize(1024, 768)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Frame display area
        self.frame_label = QLabel()
        self.frame_label.setMinimumSize(640, 480)
        self.frame_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.frame_label)
        
        # Toolbar
        toolbar = self.addToolBar("Tools")
        
        # Screenshot action
        screenshot_action = QAction(QIcon.fromTheme("camera-photo"), "Screenshot", self)
        screenshot_action.setStatusTip("Take a screenshot")
        screenshot_action.triggered.connect(self._take_screenshot)
        toolbar.addAction(screenshot_action)
        
        # Record action
        self.record_action = QAction(QIcon.fromTheme("media-record"), "Record", self)
        self.record_action.setStatusTip("Start/Stop recording")
        self.record_action.setCheckable(True)
        self.record_action.triggered.connect(self._toggle_recording)
        toolbar.addAction(self.record_action)
        
        # Virtual camera action
        self.virtual_camera_action = QAction(QIcon.fromTheme("camera-web"), "Virtual Camera", self)
        self.virtual_camera_action.setStatusTip("Enable/Disable virtual camera")
        self.virtual_camera_action.setCheckable(True)
        self.virtual_camera_action.setChecked(True)  # Enabled by default
        self.virtual_camera_action.triggered.connect(self._toggle_virtual_camera)
        toolbar.addAction(self.virtual_camera_action)
        
        # Settings panel
        settings_dock = QDockWidget("Settings", self)
        settings_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.settings_panel = SettingsPanel()
        settings_dock.setWidget(self.settings_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, settings_dock)
        
        # Connect settings panel signals
        self.settings_panel.parameter_changed.connect(self._on_parameter_changed)
        self.settings_panel.resolution_changed.connect(self._on_resolution_changed)
        self.settings_panel.color_mode_changed.connect(self._on_color_mode_changed)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # FPS and resolution label
        self.fps_label = QLabel()
        self.resolution_label = QLabel()
        self.status_bar.addPermanentWidget(self.resolution_label)
        self.status_bar.addPermanentWidget(self.fps_label)
        
        # UI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(100)  # Reduced to 10 FPS for UI update
        
        # Start camera
        if self.camera_service.start(frame_callback=self._update_frame, enable_virtual_camera=True):
            # Update settings panel with current values
            self.settings_panel.update_from_camera(self.camera_service.camera)
        else:
            QMessageBox.critical(self, "Error", "Unable to start camera")
            
    def _update_frame(self, frame: np.ndarray):
        """Callback for frame update"""
        try:
            if frame is None or frame.size == 0:
                logging.warning("Empty frame received")
                return
                
            # Convert from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create QImage from RGB frame
            height, width = frame_rgb.shape[:2]
            bytes_per_line = width * 3  # RGB = 3 channels
            
            q_img = QImage(
                frame_rgb.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888
            ).copy()  # Create a copy to avoid lifetime issues
            
            # Scale image keeping aspect ratio
            scaled_pixmap = QPixmap.fromImage(q_img).scaled(
                self.frame_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Update label
            self.frame_label.setPixmap(scaled_pixmap)
            
            # Update resolution label
            self.resolution_label.setText(f"{width}x{height}")
            
        except Exception as e:
            logging.error(f"Error updating frame: {e}")
            
    def _update_ui(self):
        """Update UI"""
        try:
            status = self.camera_service.get_status()
            
            # Update status bar
            if status['running']:
                fps = status.get('fps', 0)
                self.fps_label.setText(f"FPS: {fps:.1f}")
            else:
                self.fps_label.setText("Camera: Stopped")
                
        except Exception as e:
            logging.error(f"Error updating UI: {e}")
            
    def _on_parameter_changed(self, param, value):
        """Handle camera parameter change"""
        try:
            self.camera_service.camera.set_parameter(param, value)
        except Exception as e:
            logging.error(f"Error setting parameter {param}: {e}")
            
    def _on_resolution_changed(self, resolution):
        """Handle resolution change"""
        try:
            self.camera_service.camera.set_resolution(resolution)
            self.status_bar.showMessage(f"Resolution changed to {resolution}", 3000)
        except Exception as e:
            logging.error(f"Error changing resolution: {e}")
            self.status_bar.showMessage("Failed to change resolution", 3000)
        
    def _on_color_mode_changed(self, color_mode):
        """Handle color mode change"""
        try:
            self.camera_service.camera.set_color_mode(color_mode)
            self.status_bar.showMessage(f"Color mode changed to {color_mode}", 3000)
        except Exception as e:
            logging.error(f"Error changing color mode: {e}")
            self.status_bar.showMessage("Failed to change color mode", 3000)
        
    def _take_screenshot(self):
        """Take a screenshot"""
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
                    raise RuntimeError("Unable to save screenshot")
                    
        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")
            self.status_bar.showMessage("Error taking screenshot", 3000)
            
    def _toggle_recording(self, checked: bool):
        """Start/Stop recording"""
        try:
            if checked:
                # Create output directory if it doesn't exist
                output_dir = Path.home() / "Videos" / "PS3EyeRecordings"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Create output filename with timestamp
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"recording_{timestamp}.avi"
                
                # Get current frame to determine video properties
                frame = self.camera_service.get_frame()
                if frame is None:
                    raise RuntimeError("No frame available to start recording")
                
                height, width = frame.shape[:2]
                
                # Initialize video writer
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self._video_writer = cv2.VideoWriter(
                    str(output_file),
                    fourcc,
                    30.0,  # FPS
                    (width, height)
                )
                
                if not self._video_writer.isOpened():
                    raise RuntimeError("Failed to create video writer")
                
                self._recording = True
                self._recording_start_time = time.time()
                self.status_bar.showMessage(f"Recording started: {output_file}", 3000)
                
                # Start recording timer
                self.recording_timer = QTimer()
                self.recording_timer.timeout.connect(self._record_frame)
                self.recording_timer.start(33)  # ~30 FPS
                
            else:
                # Stop recording
                self._recording = False
                if hasattr(self, 'recording_timer'):
                    self.recording_timer.stop()
                if self._video_writer is not None:
                    self._video_writer.release()
                    self._video_writer = None
                    duration = time.time() - self._recording_start_time
                    self.status_bar.showMessage(f"Recording stopped. Duration: {duration:.1f}s", 3000)
                
        except Exception as e:
            logging.error(f"Error in recording toggle: {e}")
            self.status_bar.showMessage(f"Recording error: {str(e)}", 3000)
            self.record_action.setChecked(False)
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None
            self._recording = False
            
    def _record_frame(self):
        """Record a single frame to video"""
        try:
            if not self._recording or self._video_writer is None:
                return
                
            frame = self.camera_service.get_frame()
            if frame is not None:
                self._video_writer.write(frame)
                
        except Exception as e:
            logging.error(f"Error recording frame: {e}")
            self.record_action.setChecked(False)
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None
            self._recording = False
            
    def _toggle_virtual_camera(self, checked: bool):
        """Enable/Disable virtual camera"""
        try:
            if checked:
                # Restart service with virtual camera enabled
                self.camera_service.stop()
                if self.camera_service.start(frame_callback=self._update_frame, enable_virtual_camera=True):
                    self.status_bar.showMessage("Virtual camera enabled", 3000)
                    self.settings_panel.update_from_camera(self.camera_service.camera)
                else:
                    self.virtual_camera_action.setChecked(False)
                    self.status_bar.showMessage("Error enabling virtual camera", 3000)
            else:
                # Restart service without virtual camera
                self.camera_service.stop()
                if self.camera_service.start(frame_callback=self._update_frame, enable_virtual_camera=False):
                    self.status_bar.showMessage("Virtual camera disabled", 3000)
                    self.settings_panel.update_from_camera(self.camera_service.camera)
                else:
                    self.virtual_camera_action.setChecked(True)
                    self.status_bar.showMessage("Error disabling virtual camera", 3000)
                    
        except Exception as e:
            logging.error(f"Error toggling virtual camera: {e}")
            self.status_bar.showMessage("Error handling virtual camera", 3000)
            
    def closeEvent(self, event):
        """Handle window close"""
        try:
            if self.camera_service:
                self.camera_service.stop()
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None
        except Exception as e:
            logging.error(f"Error closing window: {e}")
        event.accept()
