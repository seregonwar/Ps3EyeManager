"""
Client per la ricezione dei frame dalla telecamera PS3 Eye
"""
import socket
import struct
import logging
import threading
import numpy as np
import json
import time
from typing import Optional, Callable

class CameraClient:
    """Client per la ricezione dei frame dalla telecamera PS3 Eye"""
    
    def __init__(self):
        self.socket = None
        self.running = False
        self.receive_thread = None
        self.frame_callback = None
        self.error_callback = None
        self._lock = threading.Lock()
    
    def start(
        self,
        frame_callback: Optional[Callable[[np.ndarray], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        host: str = 'localhost',
        port: int = 50000
    ) -> bool:
        """
        Avvia il client
        
        Args:
            frame_callback: Callback per i frame ricevuti
            error_callback: Callback per gli errori
            host: Host del server
            port: Porta del server
        
        Returns:
            bool: True se il client è stato avviato con successo
        """
        try:
            # Salva i callback
            self.frame_callback = frame_callback
            self.error_callback = error_callback
            
            # Crea il socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.socket.settimeout(5.0)  # Match server timeout
            
            # Avvia il thread di ricezione
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
            
        except Exception as e:
            logging.error(f"Errore nella connessione al server: {str(e)}")
            self.stop()
            return False
    
    def stop(self):
        """Ferma il client"""
        with self._lock:
            if not self.running:
                return
            
            self.running = False
            
            # Chiudi il socket
            if self.socket:
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            # Aspetta che il thread termini
            if self.receive_thread and self.receive_thread.is_alive():
                if self.receive_thread != threading.current_thread():
                    self.receive_thread.join(timeout=1.0)
                self.receive_thread = None
    
    def _receive_loop(self):
        """Loop di ricezione dei frame"""
        buffer = bytearray()
        message_size = None
        MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB limite massimo
        
        while self.running:
            try:
                # Prima leggiamo la dimensione del messaggio (4 byte)
                if message_size is None:
                    if len(buffer) < 4:
                        chunk = self.socket.recv(4 - len(buffer))
                        if not chunk:
                            if self.error_callback:
                                self.error_callback("Connessione persa")
                            break
                        buffer.extend(chunk)
                        continue
                        
                    message_size = struct.unpack('!I', buffer[:4])[0]
                    if message_size > MAX_MESSAGE_SIZE:
                        if self.error_callback:
                            self.error_callback(f"Dimensione messaggio troppo grande: {message_size} bytes")
                        break
                    buffer = buffer[4:]
                
                # Poi leggiamo il resto del messaggio
                if len(buffer) < message_size:
                    try:
                        chunk = self.socket.recv(min(8192, message_size - len(buffer)))
                        if not chunk:
                            if self.error_callback:
                                self.error_callback("Connessione persa durante la lettura")
                            break
                        buffer.extend(chunk)
                        continue
                    except socket.timeout:
                        continue
                
                # Processa il messaggio completo
                try:
                    # Decodifica il messaggio JSON
                    message = json.loads(buffer[:message_size].decode('utf-8'))
                    
                    if message.get('type') == 'frame':
                        frame_data = np.frombuffer(
                            message['data'].encode('latin-1'), 
                            dtype=np.uint8
                        ).reshape(message['shape'])
                        
                        if self.frame_callback:
                            self.frame_callback(frame_data)
                    
                    # Reset per il prossimo messaggio
                    buffer = buffer[message_size:]
                    message_size = None
                    
                except Exception as e:
                    logging.error(f"Errore nel processare il messaggio: {e}", exc_info=True)
                    # Reset in caso di errore
                    buffer.clear()
                    message_size = None
                
            except socket.timeout:
                continue
                
            except Exception as e:
                logging.error(f"Errore nella ricezione: {e}", exc_info=True)
                if self.error_callback:
                    self.error_callback(f"Errore di comunicazione: {e}")
                break

    def __del__(self):
        """Cleanup quando l'oggetto viene distrutto"""
        self.stop()
