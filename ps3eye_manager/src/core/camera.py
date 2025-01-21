"""
Modulo per l'interfacciamento con la PS3 Eye Camera
"""
import os
import sys
import ctypes
import logging
from pathlib import Path
from enum import IntEnum, auto
import platform
import numpy as np
from typing import Tuple, Optional, Dict, Any



class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8)
    ]

class CLEyeCameraResolution(IntEnum):
    """Supported resolutions for PS3 Eye"""
    QVGA = 0    # 320x240
    VGA = 1     # 640x480

class CLEyeCameraColorMode(IntEnum):
    """Supported color modes"""
    GRAYSCALE = 0
    COLOR = 1

class CLEyeCameraParameter(IntEnum):
    """Configurable camera parameters"""
    GAIN = 0
    EXPOSURE = 1
    ZOOM = 2
    AUTO_GAIN = 3
    AUTO_EXPOSURE = 4
    AUTO_WHITEBALANCE = 5
    WHITEBALANCE_RED = 6
    WHITEBALANCE_GREEN = 7
    WHITEBALANCE_BLUE = 8
    HFLIP = 9
    VFLIP = 10
    ROTATION = 11

class CameraError(Exception):
    """Exception for camera errors"""
    pass

class PS3EyeCamera:
    """Class for controlling the PS3 Eye Camera"""
    
    def __init__(self, settings=None):
        """Initialize the camera"""
        self.settings = settings
        self._frame_buffer = None
        self._frame_dimensions = (0, 0)
        self._setup_camera()
    
    def _setup_camera(self):
        """Configure the camera"""
        try:
            if not self._client.connect():
                raise CameraError("Unable to connect to camera server")
            
            # Set the callbacks
            self._client.set_frame_callback(self._on_frame)
            self._client.set_error_callback(self._on_error)
            
            # Send initial settings
            config = {
                'resolution': CLEyeCameraResolution.VGA,
                'color_mode': CLEyeCameraColorMode.COLOR,
                'framerate': 60
            }
            
            if self.settings and hasattr(self.settings, 'camera'):
                camera_settings = self.settings.camera
                if isinstance(camera_settings, dict):
                    if camera_settings.get('resolution') == "QVGA":
                        config['resolution'] = CLEyeCameraResolution.QVGA
                    if camera_settings.get('color_mode') == "GRAYSCALE":
                        config['color_mode'] = CLEyeCameraColorMode.GRAYSCALE
                    config['framerate'] = camera_settings.get('fps', 60)
            
            if not self._client.send_command('configure', config):
                raise CameraError("Unable to configure camera")
            
            logging.info("Camera configured successfully")
            
        except Exception as e:
            raise CameraError(f"Error configuring camera: {e}")
    
    def _on_frame(self, frame_data: Dict[str, Any]):
        """Callback for video frames"""
        try:
            if 'data' in frame_data and 'shape' in frame_data:
                shape = tuple(frame_data['shape'])
                self._frame_buffer = np.frombuffer(
                    frame_data['data'], 
                    dtype=np.uint8
                ).reshape(shape)
                self._frame_dimensions = (shape[1], shape[0])  # width, height
        except Exception as e:
            logging.error(f"Error handling frame: {e}")
    
    def _on_error(self, error_info: Dict[str, Any]):
        """Callback for errors"""
        logging.error(f"Camera error: {error_info}")
    
    def start_camera(self) -> bool:
        """Start video capture"""
        return self._client.send_command('start')
    
    def stop_camera(self) -> bool:
        """Stop video capture"""
        return self._client.send_command('stop')
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Capture a frame from the camera"""
        return self._frame_buffer.copy() if self._frame_buffer is not None else None
    
    def set_parameter(self, param: CLEyeCameraParameter, value: int) -> bool:
        """Set a camera parameter"""
        return self._client.send_command('set_parameter', {
            'parameter': param,
            'value': value
        })
    
    def get_parameter(self, param: CLEyeCameraParameter) -> Optional[int]:
        """Read a camera parameter"""
        # TODO: implement reading parameters
        return None
    
    @property
    def frame_dimensions(self) -> Tuple[int, int]:
        """Returns the frame dimensions (width, height)"""
        return self._frame_dimensions
    
    def __del__(self):
        """Cleanup when the object is destroyed"""
        if hasattr(self, '_client'):
            self._client.disconnect()