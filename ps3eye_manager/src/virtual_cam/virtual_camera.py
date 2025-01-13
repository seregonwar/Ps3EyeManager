import pyvirtualcam
import numpy as np
import cv2
import logging
from typing import Optional, Tuple
from threading import Thread, Event
from queue import Queue
import time

logger = logging.getLogger(__name__)

class VirtualCamera:
    """
    Gestisce l'integrazione con una webcam virtuale usando pyvirtualcam.
    Permette di utilizzare la PS3 Eye come una webcam standard di Windows.
    """
    
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30,
                 device: Optional[str] = None):
        """
        Inizializza la webcam virtuale
        
        Args:
            width: Larghezza del frame
            height: Altezza del frame
            fps: Frame rate
            device: Nome del dispositivo virtuale (opzionale)
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.device = device
        
        self._cam: Optional[pyvirtualcam.Camera] = None
        self._running = False
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._frame_queue = Queue(maxsize=2)  # Buffer minimo per evitare lag
        
        # Statistiche
        self._stats = {
            'frames_sent': 0,
            'start_time': 0,
            'actual_fps': 0
        }
    
    def start(self):
        """Avvia la webcam virtuale"""
        if self._running:
            return
        
        try:
            self._cam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                device=self.device,
                backend='obs'  # Usa OBS Virtual Camera come backend
            )
            
            logger.info(f"Webcam virtuale creata: {self._cam.device}")
            logger.info(f"Backend: {self._cam.backend}")
            logger.info(f"Formato: {self.width}x{self.height} @ {self.fps}fps")
            
            self._running = True
            self._stop_event.clear()
            self._stats['start_time'] = time.time()
            self._stats['frames_sent'] = 0
            
            # Avvia il thread di streaming
            self._thread = Thread(target=self._stream_thread, daemon=True)
            self._thread.start()
            
        except Exception as e:
            logger.error(f"Errore nell'avvio della webcam virtuale: {e}")
            raise
    
    def stop(self):
        """Ferma la webcam virtuale"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join()
        
        if self._cam:
            self._cam.close()
            self._cam = None
        
        # Calcola le statistiche finali
        duration = time.time() - self._stats['start_time']
        avg_fps = self._stats['frames_sent'] / duration if duration > 0 else 0
        logger.info(f"Streaming terminato: {self._stats['frames_sent']} frames in {duration:.1f}s "
                   f"(media: {avg_fps:.1f} fps)")
    
    def send_frame(self, frame: np.ndarray):
        """
        Invia un frame alla webcam virtuale
        
        Args:
            frame: Frame da inviare (RGB o RGBA)
        """
        if not self._running:
            return
        
        try:
            # Assicurati che il frame sia nel formato corretto
            if frame.shape[:2] != (self.height, self.width):
                frame = cv2.resize(frame, (self.width, self.height))
            
            # Converti in RGB se necessario
            if frame.shape[2] == 4:  # RGBA
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            elif frame.shape[2] == 1:  # Grayscale
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            
            # Normalizza i valori
            if frame.dtype != np.uint8:
                frame = (frame * 255).astype(np.uint8)
            
            # Metti il frame nella coda
            try:
                self._frame_queue.put_nowait(frame)
            except Queue.Full:
                # Se la coda è piena, rimuovi il frame più vecchio
                try:
                    self._frame_queue.get_nowait()
                except Queue.Empty:
                    pass
                self._frame_queue.put_nowait(frame)
            
        except Exception as e:
            logger.error(f"Errore nell'invio del frame: {e}")
    
    def _stream_thread(self):
        """Thread principale per lo streaming dei frame"""
        frame_time = 1.0 / self.fps
        last_frame_time = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Aspetta il prossimo frame
                frame = self._frame_queue.get(timeout=0.1)
                
                # Calcola il tempo di attesa per mantenere il frame rate
                current_time = time.time()
                elapsed = current_time - last_frame_time
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                
                # Invia il frame
                self._cam.send(frame)
                self._cam.sleep_until_next_frame()
                
                # Aggiorna le statistiche
                self._stats['frames_sent'] += 1
                frames_sent = self._stats['frames_sent']
                duration = current_time - self._stats['start_time']
                if frames_sent % 30 == 0:  # Aggiorna FPS ogni 30 frames
                    self._stats['actual_fps'] = frames_sent / duration
                
                last_frame_time = time.time()
                
            except Queue.Empty:
                # Nessun frame disponibile, continua
                continue
            except Exception as e:
                logger.error(f"Errore nello streaming: {e}")
                break
    
    @property
    def is_running(self) -> bool:
        """Verifica se la webcam virtuale è attiva"""
        return self._running
    
    @property
    def stats(self) -> dict:
        """Restituisce le statistiche dello streaming"""
        return self._stats.copy()
    
    def get_supported_formats(self) -> list:
        """Restituisce i formati supportati dalla webcam virtuale"""
        try:
            return pyvirtualcam.get_supported_formats()
        except Exception as e:
            logger.error(f"Errore nel recupero dei formati supportati: {e}")
            return []
    
    def __enter__(self):
        """Supporto per il context manager"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup per il context manager"""
        self.stop()
