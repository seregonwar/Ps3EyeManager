"""
Server per la gestione della telecamera PS3 Eye
"""
import socket
import struct
import json
import logging
import threading
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
import time

# Logger specifico per il server
logger = logging.getLogger('ps3eye.server')

class CameraServer:
    """Server per la gestione della telecamera PS3 Eye"""
    
    def __init__(self, camera_service):
        self.camera_service = camera_service
        self.socket = None
        self.clients: List[Tuple[socket.socket, str]] = []
        self.running = False
        self.accept_thread = None
        self._lock = threading.Lock()
        self._frame_lock = threading.Lock()  # Add dedicated lock for frame operations
        self._current_frame = None
        self._client_threads = []  # Keep track of client threads
        logger.debug("Server inizializzato")
    
    def start(self, host: str = 'localhost', port: int = 50000) -> bool:
        """
        Avvia il server
        
        Args:
            host: Host su cui avviare il server
            port: Porta su cui avviare il server
        
        Returns:
            bool: True se il server è stato avviato con successo
        """
        try:
            # Verifica se il server è già in esecuzione
            if self.running:
                logger.warning("Il server è già in esecuzione")
                return True
                
            # Crea il socket con gestione errori
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Imposta timeout per evitare blocchi
                self.socket.settimeout(5.0)  # 5 secondi di timeout
                logger.debug("Socket creato con successo")
                
                # Prova a fare il bind con retry
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        self.socket.bind((host, port))
                        logger.debug(f"Bind effettuato su {host}:{port}")
                        break
                    except OSError as e:
                        if e.errno == 10048:  # Porta già in uso
                            retry_count += 1
                            if retry_count == max_retries:
                                logger.error(f"Porta {port} occupata dopo {max_retries} tentativi")
                                raise
                            logger.warning(f"Porta {port} occupata, riprovo tra 1 secondo...")
                            time.sleep(1)
                        else:
                            logger.error(f"Errore nel bind del socket: {e}")
                            raise
                
                self.socket.listen(5)
                logger.debug("Server in ascolto")
            except Exception as e:
                logger.error(f"Errore nella creazione del socket: {e}", exc_info=True)
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                raise RuntimeError(f"Errore nella creazione del socket: {e}")
            
            # Avvia il thread di accettazione
            try:
                self.running = True
                self.accept_thread = threading.Thread(target=self._accept_clients)
                self.accept_thread.daemon = True
                self.accept_thread.start()
                logger.debug("Thread di accettazione avviato")
            except Exception as e:
                self.running = False
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                logger.error(f"Errore nell'avvio del thread di accettazione: {e}", exc_info=True)
                raise RuntimeError(f"Errore nell'avvio del thread di accettazione: {e}")
            
            logger.info(f"Server avviato su {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'avvio del server: {e}", exc_info=True)
            self.stop()
            return False
    
    def stop(self):
        """Ferma il server"""
        with self._lock:
            if not self.running:
                logger.debug("Server già arrestato")
                return
            
            logger.info("Arresto del server in corso...")
            self.running = False
            
            # Chiudi tutte le connessioni client
            for client, addr in self.clients:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                    client.close()
                    logger.debug(f"Connessione client chiusa: {addr}")
                except Exception as e:
                    logger.warning(f"Errore nella chiusura del client {addr}: {e}")
            self.clients.clear()
            
            # Chiudi il socket principale
            if self.socket:
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    logger.debug("Socket principale chiuso")
                except Exception as e:
                    logger.warning(f"Errore nella chiusura del socket principale: {e}")
                self.socket = None
            
            # Aspetta che tutti i thread client terminino
            for thread in self._client_threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)
            self._client_threads.clear()
            
            # Aspetta che il thread di accettazione termini
            if self.accept_thread and self.accept_thread.is_alive():
                self.accept_thread.join(timeout=1.0)
                if self.accept_thread.is_alive():
                    logger.warning("Thread di accettazione non terminato nel timeout")
                else:
                    logger.debug("Thread di accettazione terminato")
                self.accept_thread = None
            
            logger.info("Server arrestato con successo")
    
    def broadcast_frame(self, frame: np.ndarray):
        """
        Invia il frame a tutti i client connessi
        
        Args:
            frame: Frame da inviare
        """
        if not frame.size or not self.clients:
            return
            
        try:
            # Prepara il messaggio una sola volta per tutti i client
            message = {
                'type': 'frame',
                'shape': frame.shape,
                'data': frame.tobytes().decode('latin-1')
            }
            
            # Serializza il messaggio
            json_data = json.dumps(message).encode('utf-8')
            message_size = struct.pack('!I', len(json_data))
            
            # Prepara il buffer completo una sola volta
            full_message = message_size + json_data
            
            # Invia a tutti i client connessi
            with self._lock:
                disconnected_clients = []
                for client, addr in self.clients:
                    try:
                        # Imposta un timeout più breve per l'invio
                        client.settimeout(1.0)
                        client.sendall(full_message)
                    except Exception as e:
                        logger.error(f"Errore nell'invio del frame al client {addr}: {e}")
                        disconnected_clients.append((client, addr))
                
                # Rimuovi i client disconnessi
                for client, addr in disconnected_clients:
                    self.clients.remove((client, addr))
                    try:
                        client.shutdown(socket.SHUT_RDWR)
                        client.close()
                    except:
                        pass
                    logger.info(f"Client {addr} rimosso per errori di comunicazione")
                    
        except Exception as e:
            logger.error(f"Errore nel broadcast del frame: {e}", exc_info=True)

    def _accept_clients(self):
        """Thread per accettare nuove connessioni client"""
        logger.debug("Avvio thread di accettazione client")
        while self.running:
            try:
                if not self.socket:
                    logger.error("Socket non inizializzato")
                    break
                    
                try:
                    client, addr = self.socket.accept()
                    logger.info(f"Nuova connessione da {addr}")
                    
                    # Imposta timeout per il client
                    client.settimeout(5.0)  # 5 secondi di timeout
                    
                    with self._lock:
                        self.clients.append((client, addr))
                        
                    # Avvia thread per gestire il client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    logger.debug(f"Thread client avviato per {addr}")
                    self._client_threads.append(client_thread)
                    
                except socket.timeout:
                    continue
                    
            except Exception as e:
                if self.running:
                    logger.error(f"Errore nell'accettazione client: {e}", exc_info=True)
                continue
    
    def _handle_client(self, client: socket.socket, addr: str):
        """
        Gestisce una connessione client
        
        Args:
            client: Socket del client
            addr: Indirizzo del client
        """
        logger.info(f"Nuova connessione client da {addr}")
        
        # Imposta timeout sul socket
        client.settimeout(5.0)  # 5 secondi di timeout
        
        # Buffer per i dati ricevuti
        buffer = b""
        message_size = None
        MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB limite massimo
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 3
        
        try:
            while self.running:
                try:
                    # Prima leggiamo la dimensione del messaggio (4 byte)
                    if message_size is None:
                        size_data = client.recv(4)
                        if not size_data or len(size_data) != 4:
                            logger.debug(f"Client {addr} disconnesso (dati dimensione invalidi)")
                            break
                            
                        message_size = struct.unpack('!I', size_data)[0]
                        if message_size > MAX_MESSAGE_SIZE:
                            logger.error(f"Dimensione messaggio troppo grande da {addr}: {message_size} bytes")
                            break
                        
                    # Poi leggiamo il messaggio con timeout
                    start_time = time.time()
                    while len(buffer) < message_size:
                        if time.time() - start_time > 5.0:  # Timeout lettura messaggio
                            logger.error(f"Timeout lettura messaggio da {addr}")
                            raise socket.timeout()
                            
                        remaining = message_size - len(buffer)
                        chunk = client.recv(min(4096, remaining))
                        if not chunk:
                            logger.debug(f"Client {addr} disconnesso durante la lettura")
                            return
                        buffer += chunk
                    
                    # Decodifica il messaggio JSON
                    try:
                        message = json.loads(buffer.decode())
                        buffer = b""
                        message_size = None
                        consecutive_errors = 0  # Reset contatore errori
                    except json.JSONDecodeError as e:
                        logger.error(f"Errore nel parsing JSON da {addr}: {e}")
                        buffer = b""  # Reset buffer su errore
                        message_size = None
                        consecutive_errors += 1
                        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                            logger.error(f"Troppi errori consecutivi da {addr}, chiusura connessione")
                            break
                        continue
                    
                    # Gestisci il comando
                    try:
                        response = self._handle_command(message)
                    except Exception as e:
                        logger.error(f"Errore nella gestione del comando da {addr}: {e}")
                        response = {"status": "error", "message": str(e)}
                    
                    # Invia la risposta
                    try:
                        response_data = json.dumps(response).encode()
                        size_data = struct.pack('!I', len(response_data))
                        client.sendall(size_data + response_data)
                    except socket.error as e:
                        logger.error(f"Errore nell'invio della risposta a {addr}: {e}")
                        break
                        
                except socket.timeout:
                    consecutive_errors += 1
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.error(f"Troppi timeout consecutivi da {addr}, chiusura connessione")
                        break
                    continue
                except socket.error as e:
                    if self.running:
                        logger.error(f"Errore nella comunicazione con {addr}: {e}")
                    break
                    
        except Exception as e:
            if self.running:
                logger.error(f"Errore nella gestione del client {addr}: {e}")
        finally:
            # Cleanup del client
            try:
                client.close()
            except:
                pass
                
            with self._lock:
                # Rimuovi il client dalla lista
                self.clients = [(c, a) for (c, a) in self.clients if a != addr]
            
            logger.info(f"Client {addr} disconnesso")

    def _handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gestisce un comando ricevuto da un client
        
        Args:
            command: Comando ricevuto
            
        Returns:
            Dict[str, Any]: Risposta al comando
        """
        try:
            cmd = command.get('cmd')
            if not cmd:
                return {'status': 'error', 'error': 'Comando mancante'}
            
            if cmd == 'get_frame':
                frame = self._current_frame
                if frame is None:
                    return {'status': 'error', 'error': 'Frame non disponibile'}
                
                if not frame.flags['C_CONTIGUOUS']:
                    frame = np.ascontiguousarray(frame)
                
                frame_data = frame.tobytes()
                return {
                    'status': 'ok',
                    'data': {
                        'shape': frame.shape,
                        'size': len(frame_data),
                        'binary': frame_data
                    }
                }
            
            elif cmd == 'get_info':
                return {
                    'status': 'ok',
                    'data': {
                        'camera_connected': self.camera_service.camera is not None,
                        'frame_size': (640, 480),
                        'color_mode': 'RGBA'
                    }
                }
            
            else:
                return {'status': 'error', 'error': f'Comando sconosciuto: {cmd}'}
            
        except Exception as e:
            logger.error(f"Errore nell'elaborazione del comando: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def cleanup(self):
        """Esegue la pulizia delle risorse del server"""
        self.stop()
        logger.debug("Pulizia server completata")

    def __del__(self):
        """Cleanup quando l'oggetto viene distrutto"""
        self.cleanup()
