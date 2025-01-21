"""
Widget for controlling video effects
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
    """Widget for controlling video effects"""
    
    def __init__(self, effect_chain: VideoEffectChain, parent=None):
        super().__init__(parent)
        self.effect_chain = effect_chain
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Create a group for each effect
        effects_data = {
            'blur': {
                'name': 'Blur',
                'params': ['intensity', 'kernel_size']
            },
            'sharpen': {
                'name': 'Sharpen',
                'params': ['intensity']
            },
            'edge': {
                'name': 'Edges',
                'params': ['intensity', 'threshold']
            },
            'cartoon': {
                'name': 'Cartoon',
                'params': ['intensity', 'kernel_size']
            },
            'night_vision': {
                'name': 'Night Vision',
                'params': ['intensity', 'gain']
            },
            'mirror': {
                'name': 'Mirror',
                'params': ['horizontal', 'vertical']
            },
            'rotate': {
                'name': 'Rotation',
                'params': ['angle']
            },
            'denoise': {
                'name': 'Denoise',
                'params': ['intensity', 'kernel_size']
            },
            'hdr': {
                'name': 'HDR',
                'params': ['intensity']
            },
            'beauty': {
                'name': 'Beauty',
                'params': ['intensity', 'smoothing']
            }
        }
        
        for effect_id, effect_info in effects_data.items():
            group = QGroupBox(effect_info['name'])
            effect_layout = QVBoxLayout()
            
            # Checkbox to enable/disable the effect
            enable = QCheckBox("Enable")
            enable.toggled.connect(lambda v, eid=effect_id: self.effect_chain.toggle_effect(eid, v))
            effect_layout.addWidget(enable)
            
            # Specific parameters for each effect
            for param in effect_info['params']:
                if param == 'intensity':
                    # Slider for intensity (0-200%)
                    intensity = QSlider(Qt.Horizontal)
                    intensity.setRange(0, 200)
                    intensity.setValue(100)
                    intensity.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'intensity', v/100.0
                        )
                    )
                    effect_layout.addWidget(QLabel("Intensity:"))
                    effect_layout.addWidget(intensity)
                
                elif param == 'kernel_size':
                    # SpinBox for kernel size (3-15, only odd numbers)
                    kernel = QSpinBox()
                    kernel.setRange(3, 15)
                    kernel.setSingleStep(2)
                    kernel.setValue(3)
                    kernel.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'kernel_size', v
                        )
                    )
                    effect_layout.addWidget(QLabel("Kernel size:"))
                    effect_layout.addWidget(kernel)
                
                elif param == 'threshold':
                    # Slider for threshold (0-255)
                    threshold = QSlider(Qt.Horizontal)
                    threshold.setRange(0, 255)
                    threshold.setValue(127)
                    threshold.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'threshold', v
                        )
                    )
                    effect_layout.addWidget(QLabel("Threshold:"))
                    effect_layout.addWidget(threshold)
                
                elif param == 'gain':
                    # Slider for gain (1-10)
                    gain = QSlider(Qt.Horizontal)
                    gain.setRange(10, 100)
                    gain.setValue(20)
                    gain.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'gain', v/10.0
                        )
                    )
                    effect_layout.addWidget(QLabel("Gain:"))
                    effect_layout.addWidget(gain)
                
                elif param in ['horizontal', 'vertical']:
                    # Checkbox for horizontal/vertical flip
                    flip = QCheckBox("Flip " + param)
                    flip.toggled.connect(
                        lambda v, eid=effect_id, p=param: self.effect_chain.set_effect_param(
                            eid, p, v
                        )
                    )
                    effect_layout.addWidget(flip)
                
                elif param == 'angle':
                    # Slider for rotation angle (-180 to 180)
                    angle = QSlider(Qt.Horizontal)
                    angle.setRange(-180, 180)
                    angle.setValue(0)
                    angle.valueChanged.connect(
                        lambda v, eid=effect_id: self.effect_chain.set_effect_param(
                            eid, 'angle', v
                        )
                    )
                    effect_layout.addWidget(QLabel("Angle:"))
                    effect_layout.addWidget(angle)
                
                elif param == 'smoothing':
                    # Slider for smoothing (0-100)
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
        
        # Preset buttons
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
        
        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_effects)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _preset_natural(self):
        """Natural colors preset"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('sharpen', 'intensity', 0.3)
        self.effect_chain.set_effect_param('denoise', 'intensity', 0.2)
    
    def _preset_vivid(self):
        """Vivid colors preset"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('sharpen', 'intensity', 0.6)
        self.effect_chain.set_effect_param('hdr', 'intensity', 0.4)
    
    def _preset_bw(self):
        """Black and white preset"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('edge', 'intensity', 0.5)
        self.effect_chain.set_effect_param('denoise', 'intensity', 0.3)
    
    def _preset_vintage(self):
        """Vintage effect preset"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('cartoon', 'intensity', 0.3)
        self.effect_chain.set_effect_param('blur', 'intensity', 0.2)
    
    def _preset_night(self):
        """Night vision preset"""
        self.effect_chain.reset_all()
        self.effect_chain.set_effect_param('night_vision', 'intensity', 0.7)
        self.effect_chain.set_effect_param('denoise', 'intensity', 0.4)
    
    def _reset_effects(self):
        """Reset all effects"""
        self.effect_chain.reset_all()
