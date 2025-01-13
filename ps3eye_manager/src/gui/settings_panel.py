"""
Widget per le impostazioni della telecamera
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QGroupBox, QSpinBox,
    QPushButton, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.ps3eye_camera import CLEyeCameraParameter, CLEyeCameraColorMode, CLEyeCameraResolution

class SettingsPanel(QWidget):
    """Pannello delle impostazioni della telecamera"""
    
    # Segnali per notificare i cambiamenti
    parameter_changed = pyqtSignal(CLEyeCameraParameter, int)
    resolution_changed = pyqtSignal(CLEyeCameraResolution)
    color_mode_changed = pyqtSignal(CLEyeCameraColorMode)
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        """Inizializza l'interfaccia utente"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Gruppo modalità camera
        camera_group = QGroupBox("Modalità Camera")
        camera_layout = QVBoxLayout()
        camera_group.setLayout(camera_layout)
        
        # Risoluzione
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Risoluzione:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["QVGA (320x240)", "VGA (640x480)"])
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        res_layout.addWidget(self.resolution_combo)
        camera_layout.addLayout(res_layout)
        
        # Modalità colore
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Modalità colore:"))
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Scala di grigi", "Colore"])
        self.color_mode_combo.currentIndexChanged.connect(self._on_color_mode_changed)
        color_layout.addWidget(self.color_mode_combo)
        camera_layout.addLayout(color_layout)
        
        layout.addWidget(camera_group)
        
        # Gruppo parametri sensore
        sensor_group = QGroupBox("Parametri Sensore")
        sensor_layout = QVBoxLayout()
        sensor_group.setLayout(sensor_layout)
        
        # Auto Gain
        self.auto_gain_cb = QCheckBox("Auto Gain")
        self.auto_gain_cb.stateChanged.connect(lambda state: self._on_auto_param_changed(CLEyeCameraParameter.CLEYE_AUTO_GAIN, state))
        sensor_layout.addWidget(self.auto_gain_cb)
        
        # Gain manuale
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Gain:"))
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 79)
        self.gain_slider.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_GAIN, value))
        gain_layout.addWidget(self.gain_slider)
        sensor_layout.addLayout(gain_layout)
        
        # Auto Esposizione
        self.auto_exposure_cb = QCheckBox("Auto Esposizione")
        self.auto_exposure_cb.stateChanged.connect(lambda state: self._on_auto_param_changed(CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE, state))
        sensor_layout.addWidget(self.auto_exposure_cb)
        
        # Esposizione manuale
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(QLabel("Esposizione:"))
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(0, 511)
        self.exposure_slider.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_EXPOSURE, value))
        exposure_layout.addWidget(self.exposure_slider)
        sensor_layout.addLayout(exposure_layout)
        
        # Auto Bilanciamento del bianco
        self.auto_wb_cb = QCheckBox("Auto Bilanciamento Bianco")
        self.auto_wb_cb.stateChanged.connect(lambda state: self._on_auto_param_changed(CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE, state))
        sensor_layout.addWidget(self.auto_wb_cb)
        
        # Bilanciamento del bianco manuale
        wb_layout = QHBoxLayout()
        wb_layout.addWidget(QLabel("WB:"))
        
        self.wb_red_slider = QSlider(Qt.Horizontal)
        self.wb_red_slider.setRange(0, 255)
        self.wb_red_slider.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_WHITEBALANCE_RED, value))
        wb_layout.addWidget(QLabel("R"))
        wb_layout.addWidget(self.wb_red_slider)
        
        self.wb_green_slider = QSlider(Qt.Horizontal)
        self.wb_green_slider.setRange(0, 255)
        self.wb_green_slider.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_WHITEBALANCE_GREEN, value))
        wb_layout.addWidget(QLabel("G"))
        wb_layout.addWidget(self.wb_green_slider)
        
        self.wb_blue_slider = QSlider(Qt.Horizontal)
        self.wb_blue_slider.setRange(0, 255)
        self.wb_blue_slider.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_WHITEBALANCE_BLUE, value))
        wb_layout.addWidget(QLabel("B"))
        wb_layout.addWidget(self.wb_blue_slider)
        
        sensor_layout.addLayout(wb_layout)
        layout.addWidget(sensor_group)
        
        # Gruppo trasformazioni
        transform_group = QGroupBox("Trasformazioni")
        transform_layout = QVBoxLayout()
        transform_group.setLayout(transform_layout)
        
        # Flip
        flip_layout = QHBoxLayout()
        self.hflip_cb = QCheckBox("Flip Orizzontale")
        self.hflip_cb.stateChanged.connect(lambda state: self._on_param_changed(CLEyeCameraParameter.CLEYE_HFLIP, state))
        flip_layout.addWidget(self.hflip_cb)
        
        self.vflip_cb = QCheckBox("Flip Verticale")
        self.vflip_cb.stateChanged.connect(lambda state: self._on_param_changed(CLEyeCameraParameter.CLEYE_VFLIP, state))
        flip_layout.addWidget(self.vflip_cb)
        transform_layout.addLayout(flip_layout)
        
        # Rotazione
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Rotazione:"))
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_ROTATION, value))
        rotation_layout.addWidget(self.rotation_spin)
        transform_layout.addLayout(rotation_layout)
        
        # Zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.valueChanged.connect(lambda value: self._on_param_changed(CLEyeCameraParameter.CLEYE_ZOOM, value))
        zoom_layout.addWidget(self.zoom_slider)
        transform_layout.addLayout(zoom_layout)
        
        layout.addWidget(transform_group)
        
        # Pulsante Reset
        reset_btn = QPushButton("Reset Impostazioni")
        reset_btn.clicked.connect(self._reset_settings)
        layout.addWidget(reset_btn)
        
        # Spazio elastico alla fine
        layout.addStretch()
        
    def _on_param_changed(self, param: CLEyeCameraParameter, value: int):
        """Gestisce il cambiamento di un parametro"""
        self.parameter_changed.emit(param, value)
        
    def _on_auto_param_changed(self, param: CLEyeCameraParameter, state: bool):
        """Gestisce il cambiamento di un parametro automatico"""
        value = 1 if state == Qt.Checked else 0
        self.parameter_changed.emit(param, value)
        
    def _on_resolution_changed(self, index: int):
        """Gestisce il cambiamento della risoluzione"""
        resolution = CLEyeCameraResolution.CLEYE_QVGA if index == 0 else CLEyeCameraResolution.CLEYE_VGA
        self.resolution_changed.emit(resolution)
        
    def _on_color_mode_changed(self, index: int):
        """Gestisce il cambiamento della modalità colore"""
        color_mode = CLEyeCameraColorMode.CLEYE_GRAYSCALE if index == 0 else CLEyeCameraColorMode.CLEYE_COLOR
        self.color_mode_changed.emit(color_mode)
        
    def _reset_settings(self):
        """Resetta tutte le impostazioni ai valori predefiniti"""
        # Reset checkbox
        self.auto_gain_cb.setChecked(True)
        self.auto_exposure_cb.setChecked(True)
        self.auto_wb_cb.setChecked(True)
        self.hflip_cb.setChecked(False)
        self.vflip_cb.setChecked(False)
        
        # Reset slider
        self.gain_slider.setValue(40)
        self.exposure_slider.setValue(120)
        self.wb_red_slider.setValue(128)
        self.wb_green_slider.setValue(128)
        self.wb_blue_slider.setValue(128)
        self.zoom_slider.setValue(0)
        
        # Reset altri controlli
        self.rotation_spin.setValue(0)
        self.resolution_combo.setCurrentIndex(1)  # VGA
        self.color_mode_combo.setCurrentIndex(1)  # Colore
        
    def update_from_camera(self, camera):
        """Aggiorna i controlli con i valori attuali della telecamera"""
        try:
            # Aggiorna checkbox
            self.auto_gain_cb.setChecked(camera.get_parameter(CLEyeCameraParameter.CLEYE_AUTO_GAIN) == 1)
            self.auto_exposure_cb.setChecked(camera.get_parameter(CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE) == 1)
            self.auto_wb_cb.setChecked(camera.get_parameter(CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE) == 1)
            self.hflip_cb.setChecked(camera.get_parameter(CLEyeCameraParameter.CLEYE_HFLIP) == 1)
            self.vflip_cb.setChecked(camera.get_parameter(CLEyeCameraParameter.CLEYE_VFLIP) == 1)
            
            # Aggiorna slider
            self.gain_slider.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_GAIN))
            self.exposure_slider.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_EXPOSURE))
            self.wb_red_slider.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_WHITEBALANCE_RED))
            self.wb_green_slider.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_WHITEBALANCE_GREEN))
            self.wb_blue_slider.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_WHITEBALANCE_BLUE))
            self.zoom_slider.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_ZOOM))
            
            # Aggiorna altri controlli
            self.rotation_spin.setValue(camera.get_parameter(CLEyeCameraParameter.CLEYE_ROTATION))
            
        except Exception as e:
            print(f"Errore nell'aggiornamento dei controlli: {e}")
