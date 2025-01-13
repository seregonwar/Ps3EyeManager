"""
Widget per il controllo dei parametri della telecamera
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox
)
from PyQt5.QtCore import Qt
import logging

from core.camera import (
    PS3EyeCamera, CLEyeCameraColorMode, CLEyeCameraResolution,
    CLEyeCameraParameter
)

class CameraControlWidget(QWidget):
    """Widget per il controllo dei parametri della telecamera"""
    
    def __init__(self, camera: PS3EyeCamera, parent=None):
        super().__init__(parent)
        self.camera = camera
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Risoluzione e modalità colore
        resolution_group = QGroupBox("Impostazioni Base")
        resolution_layout = QVBoxLayout()
        
        # Risoluzione
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["QVGA (320x240)", "VGA (640x480)"])
        resolution_layout.addWidget(QLabel("Risoluzione:"))
        resolution_layout.addWidget(self.resolution_combo)
        
        # Modalità colore
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Colore", "Scala di grigi"])
        resolution_layout.addWidget(QLabel("Modalità colore:"))
        resolution_layout.addWidget(self.color_mode_combo)
        
        # Frame rate
        self.framerate_spin = QSpinBox()
        self.framerate_spin.setRange(15, 125)
        self.framerate_spin.setValue(60)
        resolution_layout.addWidget(QLabel("Frame rate:"))
        resolution_layout.addWidget(self.framerate_spin)
        
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        # Parametri avanzati
        params_group = QGroupBox("Parametri Avanzati")
        params_layout = QVBoxLayout()
        
        # Gain
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 79)
        self.gain_auto = QCheckBox("Auto")
        params_layout.addWidget(QLabel("Gain:"))
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.gain_auto)
        params_layout.addLayout(gain_layout)
        
        # Exposure
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(0, 511)
        self.exposure_auto = QCheckBox("Auto")
        params_layout.addWidget(QLabel("Exposure:"))
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(self.exposure_slider)
        exposure_layout.addWidget(self.exposure_auto)
        params_layout.addLayout(exposure_layout)
        
        # White Balance
        self.wb_sliders = {}
        self.wb_auto = QCheckBox("Auto")
        params_layout.addWidget(QLabel("White Balance:"))
        wb_layout = QVBoxLayout()
        for color in ['Red', 'Green', 'Blue']:
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            self.wb_sliders[color.lower()] = slider
            color_layout = QHBoxLayout()
            color_layout.addWidget(QLabel(color))
            color_layout.addWidget(slider)
            wb_layout.addLayout(color_layout)
        wb_layout.addWidget(self.wb_auto)
        params_layout.addLayout(wb_layout)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Flip e rotazione
        transform_group = QGroupBox("Trasformazioni")
        transform_layout = QVBoxLayout()
        
        self.hflip = QCheckBox("Flip orizzontale")
        self.vflip = QCheckBox("Flip verticale")
        self.rotation = QSlider(Qt.Horizontal)
        self.rotation.setRange(-180, 180)
        self.rotation.setValue(0)
        
        transform_layout.addWidget(self.hflip)
        transform_layout.addWidget(self.vflip)
        transform_layout.addWidget(QLabel("Rotazione:"))
        transform_layout.addWidget(self.rotation)
        
        transform_group.setLayout(transform_layout)
        layout.addWidget(transform_group)
        
        # Connetti i segnali
        self._connect_signals()
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        # Risoluzione e modalità colore
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        self.color_mode_combo.currentIndexChanged.connect(self._on_color_mode_changed)
        self.framerate_spin.valueChanged.connect(self._on_framerate_changed)
        
        # Gain e exposure
        self.gain_slider.valueChanged.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.GAIN, v)
        )
        self.gain_auto.toggled.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.AUTO_GAIN, int(v))
        )
        self.exposure_slider.valueChanged.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.EXPOSURE, v)
        )
        self.exposure_auto.toggled.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.AUTO_EXPOSURE, int(v))
        )
        
        # White balance
        for color, slider in self.wb_sliders.items():
            param = getattr(CLEyeCameraParameter, f'WHITEBALANCE_{color.upper()}')
            slider.valueChanged.connect(
                lambda v, p=param: self.camera.set_parameter(p, v)
            )
        self.wb_auto.toggled.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.AUTO_WHITEBALANCE, int(v))
        )
        
        # Flip e rotazione
        self.hflip.toggled.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.HFLIP, int(v))
        )
        self.vflip.toggled.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.VFLIP, int(v))
        )
        self.rotation.valueChanged.connect(
            lambda v: self.camera.set_parameter(CLEyeCameraParameter.ROTATION, v)
        )
    
    def _on_resolution_changed(self, index):
        resolution = CLEyeCameraResolution.VGA if index == 1 else CLEyeCameraResolution.QVGA
        # Aggiorna i frame rate disponibili
        self.framerate_spin.setRange(15, 75 if resolution == CLEyeCameraResolution.VGA else 125)
    
    def _on_color_mode_changed(self, index):
        color_mode = CLEyeCameraColorMode.COLOR if index == 0 else CLEyeCameraColorMode.GRAYSCALE
    
    def _on_framerate_changed(self, value):
        pass  # Implementato nella classe principale
