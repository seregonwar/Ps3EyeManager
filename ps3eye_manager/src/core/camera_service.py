"""
Service for managing the PS3 Eye camera
"""
import os
import time
import ctypes
import logging
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import cv2

from core.ps3eye_camera import PS3EyeCamera, CLEyeCameraColorMode, CLEyeCameraResolution, CLEyeCameraParameter
from core.virtual_camera import VirtualCamera

class CLEyeService:
    """Service for managing the PS3 Eye camera"""
    
    def __init__(self):
        self.camera = PS3EyeCamera()
        self.virtual_camera = VirtualCamera()
        self.running = False
        self.capture_thread = None
        self._lock = threading.Lock()
        self._frame_lock = threading.Lock()
        self._current_frame = None
        self._frame_count = 0
        self._start_time = None
        self._frame_callback = None
        self._virtual_camera_enabled = False
        
    def start(self, frame_callback=None, enable_virtual_camera=True) -> bool:
        """
        Start the service
        
        Args:
            frame_callback: Function to call when a new frame is received
            enable_virtual_camera: If True, also start the virtual camera
            
        Returns:
            bool: True if the service was started successfully
        """
        try:
            self._frame_callback = frame_callback
            self._virtual_camera_enabled = enable_virtual_camera
            
            # Search for cameras
            camera_count = self.camera.get_camera_count()
            if camera_count == 0:
                raise RuntimeError("No camera found")
            logging.info(f"Cameras found: {camera_count}")
            
            # Get the UUID of the first camera
            uuid = self.camera.get_camera_uuid(0)
            logging.info(f"Camera UUID: {uuid.Data1:08x}-{uuid.Data2:04x}-{uuid.Data3:04x}-{''.join([f'{b:02x}' for b in uuid.Data4])}")
            
            # Initialize the camera
            success = self.camera.create_camera(
                uuid,
                CLEyeCameraColorMode.CLEYE_COLOR,
                CLEyeCameraResolution.CLEYE_VGA,
                30  # 30 FPS
            )
            if not success:
                raise RuntimeError("Unable to initialize the camera")
            logging.info("Camera initialized")
            
            # Configure parameters
            self._configure_camera_parameters()
            
            # Start capture
            if not self.camera.start_camera():
                raise RuntimeError("Unable to start capture")
                
            # Start virtual camera if requested
            if self._virtual_camera_enabled:
                if not self.virtual_camera.start(
                    width=640,
                    height=480,
                    fps=30,
                    frame_callback=self.get_frame
                ):
                    logging.error("Unable to start virtual camera")
                    self._virtual_camera_enabled = False
            
            # Start capture thread
            self.running = True
            self._start_time = time.time()
            self._frame_count = 0
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            logging.info("Capture started")
            return True
            
        except Exception as e:
            logging.error(f"Error starting service: {e}")
            self.cleanup()
            return False

    def _capture_loop(self):
        """Capture loop for frames"""
        frame_count = 0
        last_fps_time = time.time()
        last_frame_time = time.time()
        error_count = 0
        consecutive_null_frames = 0
        MIN_FRAME_INTERVAL = 1.0 / 60  # Max 60 FPS
        MAX_ERRORS = 10  # Maximum number of consecutive errors
        MAX_NULL_FRAMES = 30  # Maximum number of consecutive null frames
        
        while self.running:
            try:
                current_time = time.time()
                
                # Limit frame rate
                if current_time - last_frame_time < MIN_FRAME_INTERVAL:
                    time.sleep(0.001)  # Short pause
                    continue
                
                # Capture frame
                try:
                    frame = self.camera.get_frame(timeout=100)
                except Exception as e:
                    logging.error(f"Error during frame capture: {e}")
                    error_count += 1
                    if error_count > MAX_ERRORS:
                        logging.error("Too many consecutive errors in frame capture. Restarting camera...")
                        self._restart_camera()
                        error_count = 0
                    continue
                
                if frame is None:
                    consecutive_null_frames += 1
                    if consecutive_null_frames > MAX_NULL_FRAMES:
                        logging.error("Too many consecutive null frames. Restarting camera...")
                        self._restart_camera()
                        consecutive_null_frames = 0
                    continue
                
                consecutive_null_frames = 0  # Reset contatore frame nulli
                error_count = 0  # Reset del contatore errori
                    
                # Update current frame and notify
                with self._frame_lock:
                    self._current_frame = frame
                    if self._frame_callback:
                        try:    
                            self._frame_callback(frame)
                        except Exception as e:
                            logging.error(f"Error in frame callback: {e}")
                    
                # Update FPS statistics
                frame_count += 1
                if current_time - last_fps_time >= 2.0:
                    fps = frame_count / (current_time - last_fps_time)
                    logging.info(f"Frames captured: {self._frame_count}, Average FPS: {fps:.2f}")
                    frame_count = 0
                    last_fps_time = current_time
                    
                self._frame_count += 1
                last_frame_time = current_time
                
            except Exception as e:
                logging.error(f"Error in capture loop: {e}")
                error_count += 1
                if error_count > MAX_ERRORS:
                    logging.error("Too many consecutive errors in loop. Restarting camera...")
                    self._restart_camera()
                    error_count = 0

    def _restart_camera(self):
        """Restart the camera in case of errors"""
        try:
            # Stop virtual camera if active
            if self._virtual_camera_enabled:
                self.virtual_camera.stop()
            
            # Stop and destroy the camera
            self.camera.stop_camera()
            self.camera.destroy_camera()
            
            # Recreate the camera
            uuid = self.camera.get_camera_uuid(0)
            success = self.camera.create_camera(
                uuid,
                CLEyeCameraColorMode.CLEYE_COLOR,
                CLEyeCameraResolution.CLEYE_VGA,
                30
            )
            if not success:
                raise RuntimeError("Unable to reinitialize the camera")
                
            # Reconfigure and restart
            self._configure_camera_parameters()
            if not self.camera.start_camera():
                raise RuntimeError("Unable to restart capture")
            
            # Restart virtual camera if active
            if self._virtual_camera_enabled:
                if not self.virtual_camera.start(
                    width=640,
                    height=480,
                    fps=30,
                    frame_callback=self.get_frame
                ):
                    logging.error("Unable to restart virtual camera")
                    self._virtual_camera_enabled = False
                
            logging.info("Camera restarted successfully")
            
        except Exception as e:
            logging.error(f"Error restarting camera: {e}")
            # In case of fatal error, stop the service
            self.running = False

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the last available frame
        
        Returns:
            Optional[np.ndarray]: The frame if available, None otherwise
        """
        with self._frame_lock:
            if self._current_frame is not None:
                if self._virtual_camera_enabled:
                    # For virtual camera, BGR format is required
                    return self._current_frame
                else:
                    # For display, we use RGBA
                    return cv2.cvtColor(self._current_frame, cv2.COLOR_BGR2RGBA)
            return None

    def stop(self):
        """Stop the service"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        
        # Stop virtual camera
        if self._virtual_camera_enabled:
            self.virtual_camera.stop()
            
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.camera:
            self.camera.stop_camera()
            self.camera.destroy_camera()
            
        if self.virtual_camera:
            self.virtual_camera.cleanup()

    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.stop()

    def _configure_camera_parameters(self):
        """Configure camera parameters with error handling"""
        params = [
            (CLEyeCameraParameter.CLEYE_AUTO_GAIN, 0),
            (CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE, 0),
            (CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE, 0),
            (CLEyeCameraParameter.CLEYE_GAIN, 30),  # Increased for better brightness
            (CLEyeCameraParameter.CLEYE_EXPOSURE, 50),  # Reduced to avoid overexposure
            (CLEyeCameraParameter.CLEYE_WHITEBALANCE_RED, 60),  # Improved white balance
            (CLEyeCameraParameter.CLEYE_WHITEBALANCE_GREEN, 55),
            (CLEyeCameraParameter.CLEYE_WHITEBALANCE_BLUE, 65),
            (CLEyeCameraParameter.CLEYE_HFLIP, 0),  # No horizontal flip
            (CLEyeCameraParameter.CLEYE_VFLIP, 0),  # No vertical flip
            (CLEyeCameraParameter.CLEYE_HKEYSTONE, 0),  # No keystone correction
            (CLEyeCameraParameter.CLEYE_VKEYSTONE, 0),
            (CLEyeCameraParameter.CLEYE_LENSCORRECTION1, 0),  # No lens correction
            (CLEyeCameraParameter.CLEYE_LENSCORRECTION2, 0),
            (CLEyeCameraParameter.CLEYE_LENSCORRECTION3, 0),
            (CLEyeCameraParameter.CLEYE_LENSBRIGHTNESS, 20)  # Lens brightness moderate
        ]
        
        for param, value in params:
            if not self.camera.set_parameter(param, value):
                logging.warning(f"Unable to set parameter {param.name} to {value}")
        
        logging.info("Camera parameters configured")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the service
        
        Returns:
            Dict[str, Any]: Service status
        """
        status = {
            'running': self.running,
            'camera_connected': self.camera and self.camera._camera is not None,
            'frame_count': self._frame_count,
            'last_error': None,
            'uptime': time.time() - self._start_time if self._start_time else 0,
            'fps': self._frame_count / (time.time() - self._start_time) if self._start_time else 0
        }
        
        if self.camera and self.camera._camera:
            status.update({
                'connected': True,
                'resolution': (640, 480),
                'color_mode': 'RGBA',
                'framerate': 30,
                'parameters': {
                    'gain': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_GAIN),
                    'exposure': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_EXPOSURE),
                    'wb_red': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_WHITEBALANCE_RED),
                    'wb_green': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_WHITEBALANCE_GREEN),
                    'wb_blue': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_WHITEBALANCE_BLUE),
                    'auto_gain': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_AUTO_GAIN),
                    'auto_exposure': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE),
                    'auto_wb': self.camera.get_parameter(CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE)
                }
            })
        
        return status
