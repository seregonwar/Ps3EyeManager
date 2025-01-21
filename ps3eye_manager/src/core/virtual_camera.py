"""
Module for managing the virtual camera driver
"""
import os
import sys
import time
import logging
import threading
import numpy as np
import cv2
import mmap
import ctypes
from ctypes import wintypes
import win32api
import win32con
import win32security
from pathlib import Path
from typing import Optional

class BITMAPINFOHEADER(ctypes.Structure):
    """Windows structure for image information"""
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]

class VirtualCamera:
    """Manages the virtual camera driver"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self._frame_callback = None
        self._lock = threading.Lock()
        self._shared_memory = None
        self._map_name = "PS3EyeVirtualCamera_SharedMem"
        
    def start(self, width: int = 640, height: int = 480, fps: int = 30, frame_callback=None) -> bool:
        """
        Start the virtual camera
        
        Args:
            width: Frame width
            height: Frame height
            fps: Frame rate
            frame_callback: Callback called when a new frame is needed
            
        Returns:
            bool: True if the start is successful
        """
        try:
            self._frame_callback = frame_callback
            
            # Shared memory buffer size
            buffer_size = width * height * 3  # BGR 24-bit
            
            try:
                # Create/open shared memory
                security_attributes = win32security.SECURITY_ATTRIBUTES()
                security_attributes.bInheritHandle = True
                
                self._shared_memory = mmap.mmap(
                    -1,  # Create new mapping
                    buffer_size,
                    self._map_name,
                    mmap.ACCESS_WRITE
                )
                
                logging.info(f"Shared memory created: {width}x{height}@{fps}fps")
                
                # Start frame sending thread
                self.running = True
                self.thread = threading.Thread(target=self._stream_loop)
                self.thread.daemon = True
                self.thread.start()
                
                return True
                
            except Exception as e:
                logging.error(f"Error creating shared memory: {e}")
                return False
            
        except Exception as e:
            logging.error(f"Error starting virtual camera: {e}")
            self.cleanup()
            return False
            
    def _stream_loop(self):
        """Main loop for streaming frames"""
        last_frame_time = time.time()
        frame_interval = 1.0 / 30  # 30 FPS
        
        while self.running and self._shared_memory:
            try:
                current_time = time.time()
                
                # Respect the frame rate
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue
                
                # Get the frame from the callback
                if self._frame_callback:
                    frame = self._frame_callback()
                    if frame is not None:
                        # The frame is already in BGR format, write it directly
                        with self._lock:
                            self._shared_memory.seek(0)
                            self._shared_memory.write(frame.tobytes())
                
                last_frame_time = current_time
                
            except Exception as e:
                logging.error(f"Error streaming frame: {e}")
                time.sleep(0.1)
                
    def stop(self):
        """Stop the virtual camera"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        self.cleanup()
        
    def cleanup(self):
        """Clean up resources"""
        if self._shared_memory:
            try:
                self._shared_memory.close()
                # Ensure the shared memory is removed
                try:
                    import win32file
                    win32file.CloseHandle(int(self._shared_memory.fileno()))
                except:
                    pass
            except Exception as e:
                logging.error(f"Error closing shared memory: {e}")
            finally:
                self._shared_memory = None
            
    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.stop()
