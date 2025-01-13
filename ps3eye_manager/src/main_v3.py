"""
Punto di ingresso principale dell'applicazione
"""
import os
import sys
from pathlib import Path

# Aggiungi il path della directory src al PYTHONPATH
src_dir = Path(__file__).parent
project_root = src_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
import subprocess
import time
import socket
import signal
import atexit
from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from gui.main_window import MainWindow
from core.camera_service import CLEyeService
from utils.logging_config import setup_logging

def is_port_in_use(port: int) -> bool:
    """Verifica se una porta è in uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def start_camera_service() -> Optional[CLEyeService]:
    """Avvia il servizio camera"""
    try:
        # Verifica se la porta è già in uso
        if is_port_in_use(50000):
            logging.error("La porta 50000 è già in uso")
            return None
        
        # Crea e avvia il servizio
        service = CLEyeService()
        if not service.start():
            logging.error("Impossibile avviare il servizio camera")
            return None
        
        return service
        
    except FileNotFoundError as e:
        # Driver non trovato - mostra un messaggio all'utente
        logging.error(f"Errore nell'avvio del servizio: {e}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Driver PS3 Eye Camera non trovato")
        msg.setText(str(e))
        msg.setInformativeText(
            "L'applicazione funzionerà in modalità limitata senza accesso alla camera.\n"
            "Installa i driver e riavvia l'applicazione per utilizzare la camera."
        )
        msg.exec_()
        return None
    except Exception as e:
        # Altri errori
        logging.error(f"Errore nell'avvio del servizio: {e}")
        return None

def stop_camera_service(service: Optional[CLEyeService]):
    """Ferma il servizio della telecamera"""
    if service:
        try:
            service.cleanup()
        except Exception as e:
            logging.error(f"Errore nell'arresto del servizio: {e}")

def create_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    return palette

def main():
    """Funzione principale"""
    try:
        # Configura il logging
        setup_logging()
        logging.info("=== PS3 Eye Manager ===")
        logging.info("Versione: 1.0.0")
        logging.info(f"Directory base: {src_dir}")
        
        # Crea l'applicazione Qt
        app = QApplication(sys.argv)
        
        # Imposta il tema scuro
        app.setStyle('Fusion')
        app.setPalette(create_dark_palette())
        logging.info("Tema scuro applicato")
        logging.info("Applicazione Qt configurata con successo")
        
        # Crea e mostra la finestra principale
        window = MainWindow()
        window.show()
        
        # Esegui l'applicazione
        return app.exec_()
        
    except Exception as e:
        logging.error(f"ERRORE: {str(e)}")
        QMessageBox.critical(None, "Errore", f"L'applicazione si è chiusa con un errore\n{str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
