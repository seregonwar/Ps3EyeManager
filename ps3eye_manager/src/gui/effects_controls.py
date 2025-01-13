"""
Widget per il controllo degli effetti video
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QSlider, QSpinBox, QGroupBox,
    QPushButton, QColorDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import logging

from effects.video_effects import VideoEffectChain

class EffectsControlWidget(QWidget):
    """Widget per il controllo degli effetti video"""
    
    def __init__(self, effect_chain: VideoEffectChain, parent=None):
        super().__init__(parent)
        self.effect_chain = effect_chain
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Crea un gruppo per ogni effetto
        effects_data = {
            'blur': {
                'name': 'Sfocatura',
                'params': ['intensity', 'kernel_size']
            },
            'sharpen': {
                'name': 'Nitidezza',
                'params': ['intensity']
            },
            'edge': {
                'name': 'Bordi',
                'params': ['intensity', 'threshold']
            },
            'cartoon': {
                'name': 'Cartone',
                'params': ['intensity', 'kernel_size']
            },
            'night_vision': {
                'name': 'Visione Notturna',
                'params': ['intensity', 'gain']
            },
            'mirror': {
                'name': 'Specchio',
                'params': ['horizontal', 'vertical']
            },
            'rotate': {
                'name': 'Rotazione',
                'params': ['angle']
            },
            'denoise': {
                'name': 'Riduzione Rumore',
                'params': ['intensity', 'kernel_size']
            },
            'hdr': {
                'name': 'HDR',
                'params': ['intensity']
            },
            'beauty': {
                'name': 'Bellezza',
                'params': ['intensity', 'smoothing']
            }
        }
        
        for effect_id, effect_info in effects_data.items():
            group = QGroupBox(effect_info['name'])
            effect_layout = QVBoxLayout()
            
            # Checkbox per attivare/disattivare l'effetto
            enable = QCheckBox("Attiva")
            enable.toggled.connect(lambda v, eid=effect_id: self.effect_chain.toggle_effect(eid, v))
            effect_layout.addWidget(enable)
            
            # Parametri specifici per ogni effetto
            for param in effect_info['params']:
                if param == 'intensity':
                    # Slider per l'intensità (0-200%)
                    intensity = QSlider(Qt.Horizontal)
                    intensity.setRange(0, 200)
                    intensity.setValue(100)
                    intensity.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'intensity', v/100.0
                        )
                    )
                    effect_layout.addWidget(QLabel("Intensità:"))
                    effect_layout.addWidget(intensity)
                
                elif param == 'kernel_size':
                    # SpinBox per la dimensione del kernel (3-15, solo dispari)
                    kernel = QSpinBox()
                    kernel.setRange(3, 15)
                    kernel.setSingleStep(2)
                    kernel.setValue(3)
                    kernel.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'kernel_size', v
                        )
                    )
                    effect_layout.addWidget(QLabel("Dimensione kernel:"))
                    effect_layout.addWidget(kernel)
                
                elif param == 'threshold':
                    # Slider per la soglia (0-255)
                    threshold = QSlider(Qt.Horizontal)
                    threshold.setRange(0, 255)
                    threshold.setValue(127)
                    threshold.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'threshold', v
                        )
                    )
                    effect_layout.addWidget(QLabel("Soglia:"))
                    effect_layout.addWidget(threshold)
                
                elif param == 'gain':
                    # Slider per il guadagno (1-10)
                    gain = QSlider(Qt.Horizontal)
                    gain.setRange(10, 100)
                    gain.setValue(20)
                    gain.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'gain', v/10.0
                        )
                    )
                    effect_layout.addWidget(QLabel("Guadagno:"))
                    effect_layout.addWidget(gain)
                
                elif param in ['horizontal', 'vertical']:
                    # Checkbox per flip orizzontale/verticale
                    flip = QCheckBox("Flip " + param)
                    flip.toggled.connect(
                        lambda v, eid=effect_id, p=param: self.effect_chain.set_effect_param(
                            eid, p, v
                        )
                    )
                    effect_layout.addWidget(flip)
                
                elif param == 'angle':
                    # Slider per l'angolo di rotazione (-180 a 180)
                    angle = QSlider(Qt.Horizontal)
                    angle.setRange(-180, 180)
                    angle.setValue(0)
                    angle.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'angle', v
                        )
                    )
                    effect_layout.addWidget(QLabel("Angolo:"))
                    effect_layout.addWidget(angle)
                
                elif param == 'smoothing':
                    # Slider per lo smoothing (0-100)
                    smoothing = QSlider(Qt.Horizontal)
                    smoothing.setRange(0, 100)
                    smoothing.setValue(50)
                    smoothing.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'smoothing', v/100.0
                        )
                    )
                    effect_layout.addWidget(QLabel("Smoothing:"))
                    effect_layout.addWidget(smoothing)
            
            group.setLayout(effect_layout)
            layout.addWidget(group)
        
        # Pulsanti di preset
        presets_group = QGroupBox("Preset")
        presets_layout = QHBoxLayout()
        
        presets = [
            ("Naturale", self._preset_natural),
            ("Vivido", self._preset_vivid),
            ("Bianco e Nero", self._preset_bw),
            ("Vintage", self._preset_vintage),
            ("Notte", self._preset_night)
        ]
        
        for name, callback in presets:
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            presets_layout.addWidget(btn)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        # Pulsante reset
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_effects)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _preset_natural(self):
        """Preset per colori naturali"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('sharpen', 'intensity', 0.3)
        self.effect_chain.set_effect_param('denoise', 'intensity', 0.2)
    
    def _preset_vivid(self):
        """Preset per colori vividi"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('sharpen', 'intensity', 0.6)
        self.effect_chain.set_effect_param('hdr', 'intensity', 0.4)
    
    def _preset_bw(self):
        """Preset per bianco e nero"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('edge', 'intensity', 0.5)
        self.effect_chain.set_effect_param('denoise', 'intensity', 0.3)
    
    def _preset_vintage(self):
        """Preset per effetto vintage"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('cartoon', 'intensity', 0.3)
        self.effect_chain.set_effect_param('blur', 'intensity', 0.2)
    
    def _preset_night(self):
        """Preset per visione notturna"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('night_vision', 'intensity', 0.7)
        self.effect_chain.set_effect_param('denoise', 'intensity', 0.4)
    
    def _reset_effects(self):
        """Resetta tutti gli effetti"""
        self.effect_chain.reset_all()
