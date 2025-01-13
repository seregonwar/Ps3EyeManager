"""
Configurazione centralizzata del logging per PS3 Eye Manager
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: str = None, debug: bool = False) -> None:
    """
    Configura il sistema di logging per l'applicazione
    
    Args:
        log_dir: Directory dove salvare i file di log. Se None, usa la directory predefinita
        debug: Se True, imposta il livello di logging a DEBUG
    """
    if log_dir is None:
        log_dir = Path.home() / "PS3EyeManager" / "logs"
    
    # Crea la directory dei log se non esiste
    os.makedirs(log_dir, exist_ok=True)
    
    # Genera il nome del file di log con data
    log_file = Path(log_dir) / f"ps3eye_manager_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configura il formato del log
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # Handler per il file
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    
    # Handler per la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    
    # Configura il logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Rimuovi handler esistenti
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Aggiungi i nuovi handler
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Logger specifici per componenti
    loggers = {
        'camera': logging.getLogger('ps3eye.camera'),
        'server': logging.getLogger('ps3eye.server'),
        'ui': logging.getLogger('ps3eye.ui'),
        'driver': logging.getLogger('ps3eye.driver'),
    }
    
    # Configura i logger specifici
    for name, logger in loggers.items():
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
    logging.info("Sistema di logging configurato con successo")
    if debug:
        logging.debug("Modalità debug attivata")
