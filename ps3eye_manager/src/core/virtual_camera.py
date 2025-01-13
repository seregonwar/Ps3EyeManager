"""
Modulo per la gestione del driver della webcam virtuale
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
    """Struttura Windows per le informazioni dell'immagine"""
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
    """Gestisce il driver della webcam virtuale"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self._frame_callback = None
        self._lock = threading.Lock()
        self._shared_memory = None
        self._map_name = "PS3EyeVirtualCamera_SharedMem"
        
    def start(self, width: int = 640, height: int = 480, fps: int = 30, frame_callback=None) -> bool:
        """
        Avvia la webcam virtuale
        
        Args:
            width: Larghezza del frame
            height: Altezza del frame
            fps: Frame rate
            frame_callback: Callback chiamato quando serve un nuovo frame
            
        Returns:
            bool: True se l'avvio è riuscito
        """
        try:
            self._frame_callback = frame_callback
            
            # Dimensione del buffer condiviso
            buffer_size = width * height * 3  # BGR 24-bit
            
            try:
                # Crea/apri la memoria condivisa
                security_attributes = win32security.SECURITY_ATTRIBUTES()
                security_attributes.bInheritHandle = True
                
                self._shared_memory = mmap.mmap(
                    -1,  # Crea nuovo mapping
                    buffer_size,
                    self._map_name,
                    mmap.ACCESS_WRITE
                )
                
                logging.info(f"Memoria condivisa creata: {width}x{height}@{fps}fps")
                
                # Avvia il thread di invio frame
                self.running = True
                self.thread = threading.Thread(target=self._stream_loop)
                self.thread.daemon = True
                self.thread.start()
                
                return True
                
            except Exception as e:
                logging.error(f"Errore nella creazione della memoria condivisa: {e}")
                return False
            
        except Exception as e:
            logging.error(f"Errore nell'avvio della webcam virtuale: {e}")
            self.cleanup()
            return False
            
    def _stream_loop(self):
        """Loop principale per lo streaming dei frame"""
        last_frame_time = time.time()
        frame_interval = 1.0 / 30  # 30 FPS
        
        while self.running and self._shared_memory:
            try:
                current_time = time.time()
                
                # Rispetta il frame rate
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue
                
                # Ottieni il frame dal callback
                if self._frame_callback:
                    frame = self._frame_callback()
                    if frame is not None:
                        # Copia il frame nella memoria condivisa
                        with self._lock:
                            self._shared_memory.seek(0)
                            self._shared_memory.write(frame.tobytes())
                
                last_frame_time = current_time
                
            except Exception as e:
                logging.error(f"Errore nello streaming del frame: {e}")
                time.sleep(0.1)
                
    def stop(self):
        """Ferma la webcam virtuale"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.cleanup()
        
    def cleanup(self):
        """Pulisce le risorse"""
        if self._shared_memory:
            try:
                self._shared_memory.close()
            except Exception as e:
                logging.error(f"Errore nella chiusura della memoria condivisa: {e}")
            finally:
                self._shared_memory = None
            
    def __del__(self):
        """Cleanup quando l'oggetto viene distrutto"""
        self.stop()
