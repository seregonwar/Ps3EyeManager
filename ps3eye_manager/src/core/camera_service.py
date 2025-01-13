"""
Servizio per la gestione della telecamera PS3 Eye
"""
import os
import time
import ctypes
import logging
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from core.ps3eye_camera import PS3EyeCamera, CLEyeCameraColorMode, CLEyeCameraResolution, CLEyeCameraParameter
from core.virtual_camera import VirtualCamera

class CLEyeService:
    """Servizio per la gestione della telecamera PS3 Eye"""
    
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
        Avvia il servizio
        
        Args:
            frame_callback: Funzione da chiamare quando arriva un nuovo frame
            enable_virtual_camera: Se True, avvia anche la webcam virtuale
            
        Returns:
            bool: True se il servizio è stato avviato con successo
        """
        try:
            self._frame_callback = frame_callback
            self._virtual_camera_enabled = enable_virtual_camera
            
            # Cerca le telecamere
            camera_count = self.camera.get_camera_count()
            if camera_count == 0:
                raise RuntimeError("Nessuna telecamera trovata")
            logging.info(f"Telecamere trovate: {camera_count}")
            
            # Ottieni l'UUID della prima telecamera
            uuid = self.camera.get_camera_uuid(0)
            if uuid.Data1 == 0 and uuid.Data2 == 0 and uuid.Data3 == 0 and all(b == 0 for b in uuid.Data4):
                raise RuntimeError("UUID telecamera non valido")
            logging.info(f"UUID della telecamera: {uuid.Data1:08x}-{uuid.Data2:04x}-{uuid.Data3:04x}-{''.join([f'{b:02x}' for b in uuid.Data4])}")
            
            # Inizializza la telecamera
            success = self.camera.create_camera(
                uuid,
                CLEyeCameraColorMode.CLEYE_COLOR,
                CLEyeCameraResolution.CLEYE_VGA,
                30  # 30 FPS
            )
            if not success:
                raise RuntimeError("Impossibile inizializzare la telecamera")
            logging.info("Telecamera inizializzata")
            
            # Configura i parametri
            self._configure_camera_parameters()
            
            # Avvia la cattura
            if not self.camera.start_camera():
                raise RuntimeError("Impossibile avviare la cattura")
                
            # Avvia la webcam virtuale se richiesto
            if self._virtual_camera_enabled:
                if not self.virtual_camera.start(
                    width=640,
                    height=480,
                    fps=30,
                    frame_callback=self.get_frame
                ):
                    logging.error("Impossibile avviare la webcam virtuale")
                    self._virtual_camera_enabled = False
            
            # Avvia il thread di cattura
            self.running = True
            self._start_time = time.time()
            self._frame_count = 0
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            logging.info("Cattura avviata")
            return True
            
        except Exception as e:
            logging.error(f"Errore nell'avvio del servizio: {e}")
            self.cleanup()
            return False

    def _capture_loop(self):
        """Loop di cattura dei frame"""
        frame_count = 0
        last_fps_time = time.time()
        last_frame_time = time.time()
        error_count = 0
        MIN_FRAME_INTERVAL = 1.0 / 60  # Max 60 FPS
        MAX_ERRORS = 10  # Numero massimo di errori consecutivi
        
        while self.running:
            try:
                current_time = time.time()
                
                # Limita il frame rate
                if current_time - last_frame_time < MIN_FRAME_INTERVAL:
                    time.sleep(0.001)  # Breve pausa
                    continue
                
                # Cattura il frame
                frame = self.camera.get_frame(timeout=100)
                if frame is None:
                    error_count += 1
                    if error_count > MAX_ERRORS:
                        logging.error("Troppi errori consecutivi nella cattura dei frame. Riavvio della telecamera...")
                        self._restart_camera()
                        error_count = 0
                    continue
                
                error_count = 0  # Reset del contatore errori
                    
                # Aggiorna il frame corrente e notifica
                with self._frame_lock:
                    self._current_frame = frame
                    if self._frame_callback:
                        self._frame_callback(frame)
                    
                # Aggiorna statistiche FPS
                frame_count += 1
                if current_time - last_fps_time >= 2.0:
                    fps = frame_count / (current_time - last_fps_time)
                    logging.info(f"Frame catturati: {self._frame_count}, FPS medio: {fps:.2f}")
                    frame_count = 0
                    last_fps_time = current_time
                    
                self._frame_count += 1
                last_frame_time = current_time
                
            except Exception as e:
                error_count += 1
                logging.error(f"Errore nella cattura del frame: {e}")
                if error_count > MAX_ERRORS:
                    logging.error("Troppi errori consecutivi. Riavvio della telecamera...")
                    self._restart_camera()
                    error_count = 0
                else:
                    time.sleep(0.1)

    def _restart_camera(self):
        """Riavvia la telecamera in caso di errori"""
        try:
            self.camera.stop_camera()
            self.camera.destroy_camera()
            
            # Ricrea la telecamera
            uuid = self.camera.get_camera_uuid(0)
            success = self.camera.create_camera(
                uuid,
                CLEyeCameraColorMode.CLEYE_COLOR,
                CLEyeCameraResolution.CLEYE_VGA,
                30
            )
            if not success:
                raise RuntimeError("Impossibile reinizializzare la telecamera")
                
            # Riconfigura e riavvia
            self._configure_camera_parameters()
            if not self.camera.start_camera():
                raise RuntimeError("Impossibile riavviare la cattura")
                
            logging.info("Telecamera riavviata con successo")
            
        except Exception as e:
            logging.error(f"Errore nel riavvio della telecamera: {e}")
            # In caso di errore fatale, fermiamo il servizio
            self.running = False

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Ottiene l'ultimo frame disponibile
        
        Returns:
            Optional[np.ndarray]: Il frame se disponibile, None altrimenti
        """
        with self._frame_lock:
            return self._current_frame.copy() if self._current_frame is not None else None

    def stop(self):
        """Ferma il servizio"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        
        # Ferma la webcam virtuale
        if self._virtual_camera_enabled:
            self.virtual_camera.stop()
            
        self.cleanup()

    def cleanup(self):
        """Esegue la pulizia delle risorse"""
        if self.camera:
            self.camera.stop_camera()
            self.camera.destroy_camera()
            
        if self.virtual_camera:
            self.virtual_camera.cleanup()

    def __del__(self):
        """Cleanup quando l'oggetto viene distrutto"""
        self.stop()

    def _configure_camera_parameters(self):
        """Configura i parametri della telecamera con gestione errori"""
        params = [
            (CLEyeCameraParameter.CLEYE_AUTO_GAIN, 0),
            (CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE, 0),
            (CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE, 0),
            (CLEyeCameraParameter.CLEYE_GAIN, 30),  # Aumentato per migliore luminosità
            (CLEyeCameraParameter.CLEYE_EXPOSURE, 50),  # Ridotto per evitare sovraesposizione
            (CLEyeCameraParameter.CLEYE_WHITEBALANCE_RED, 60),  # Bilanciamento del bianco migliorato
            (CLEyeCameraParameter.CLEYE_WHITEBALANCE_GREEN, 55),
            (CLEyeCameraParameter.CLEYE_WHITEBALANCE_BLUE, 65),
            (CLEyeCameraParameter.CLEYE_HFLIP, 0),  # No flip orizzontale
            (CLEyeCameraParameter.CLEYE_VFLIP, 0),  # No flip verticale
            (CLEyeCameraParameter.CLEYE_HKEYSTONE, 0),  # No correzione keystone
            (CLEyeCameraParameter.CLEYE_VKEYSTONE, 0),
            (CLEyeCameraParameter.CLEYE_LENSCORRECTION1, 0),  # No correzione lente
            (CLEyeCameraParameter.CLEYE_LENSCORRECTION2, 0),
            (CLEyeCameraParameter.CLEYE_LENSCORRECTION3, 0),
            (CLEyeCameraParameter.CLEYE_LENSBRIGHTNESS, 20)  # Luminosità lente moderata
        ]
        
        for param, value in params:
            if not self.camera.set_parameter(param, value):
                logging.warning(f"Impossibile impostare il parametro {param.name} a {value}")
        
        logging.info("Parametri della telecamera configurati")

    def get_status(self) -> Dict[str, Any]:
        """
        Ottiene lo stato corrente del servizio
        
        Returns:
            Dict[str, Any]: Stato del servizio
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
