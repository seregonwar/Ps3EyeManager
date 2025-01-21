import cv2
import numpy as np
from typing import Callable, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class EffectParams:
    """Configurable parameters for video effects"""
    intensity: float = 1.0
    kernel_size: int = 3
    threshold: int = 127
    color: tuple = (0, 0, 0)

class VideoEffect(ABC):
    """Base class for video effects"""
    
    def __init__(self):
        self.params = EffectParams()
    
    @abstractmethod
    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply the effect to the frame"""
        pass
    
    def set_params(self, **kwargs):
        """Set the effect parameters"""
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

class BlurEffect(VideoEffect):
    """Blur effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        k = self.params.kernel_size
        if k % 2 == 0:
            k += 1  # The kernel must be odd
        return cv2.GaussianBlur(frame, (k, k), self.params.intensity)

class SharpenEffect(VideoEffect):
    """Sharpen effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ]) * self.params.intensity
        return cv2.filter2D(frame, -1, kernel)

class EdgeDetectionEffect(VideoEffect):
    """Edge detection effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, self.params.threshold, self.params.threshold * 2)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

class CartoonEffect(VideoEffect):
    """Cartoon effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        # Reduce colors
        num_colors = int(256 * self.params.intensity)
        if num_colors < 2:
            num_colors = 2
        
        # Quantize colors
        data = np.float32(frame).reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
        _, labels, centers = cv2.kmeans(data, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Reconstruct the image
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()]
        quantized = quantized.reshape(frame.shape)
        
        # Add edges
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                    cv2.THRESH_BINARY, self.params.kernel_size, 2)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        return cv2.bitwise_and(quantized, edges)

class NightVisionEffect(VideoEffect):
    """Night vision effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        # Convert to grayscale and increase brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.multiply(gray, self.params.intensity)
        
        # Apply a slight blur to reduce noise
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Create the night vision effect
        result = np.zeros_like(frame)
        result[:, :, 1] = gray  # Green channel
        
        # Add some random noise
        noise = np.random.normal(0, 2, gray.shape).astype(np.uint8)
        result[:, :, 1] = cv2.add(result[:, :, 1], noise)
        
        return result

class MirrorEffect(VideoEffect):
    """Mirror effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        return cv2.flip(frame, 1)

class RotateEffect(VideoEffect):
    """Rotate effect"""
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        angle = self.params.intensity * 360
        center = tuple(np.array(frame.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(frame, rot_mat, frame.shape[1::-1], flags=cv2.INTER_LINEAR)

class VideoEffectChain:
    """
    Handles a chain of video effects that can be applied in sequence
    """
    
    def __init__(self):
        self.effects: Dict[str, VideoEffect] = {
            'blur': BlurEffect(),
            'sharpen': SharpenEffect(),
            'edge': EdgeDetectionEffect(),
            'cartoon': CartoonEffect(),
            'night_vision': NightVisionEffect(),
            'mirror': MirrorEffect(),
            'rotate': RotateEffect()
        }
        self.active_effects: Dict[str, bool] = {name: False for name in self.effects}
    
    def toggle_effect(self, effect_name: str, active: bool = True):
        """Enable or disable an effect"""
        if effect_name in self.active_effects:
            self.active_effects[effect_name] = active
    
    def set_effect_params(self, effect_name: str, **params):
        """Set the parameters for a specific effect"""
        if effect_name in self.effects:
            self.effects[effect_name].set_params(**params)
    
    def apply_effects(self, frame: np.ndarray) -> np.ndarray:
        """Apply all active effects to the frame"""
        result = frame.copy()
        for name, active in self.active_effects.items():
            if active:
                result = self.effects[name].apply(result)
        return result
