"""
Script di avvio automatico per PS3 Eye Manager
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
import time
import traceback

def setup_logging():
    """Configura il logging di base"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ps3eye_manager.log')
        ]
    )

def main():
    """Funzione principale"""
    try:
        # Configura il logging
        setup_logging()
        
        # Ottieni il path dello script
        script_dir = Path(__file__).parent
        src_dir = script_dir / "src"
        
        # Aggiungi src al PYTHONPATH
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        # Verifica che Python sia nel PATH
        python_path = sys.executable
        if not python_path:
            raise RuntimeError("Python non trovato nel PATH")
        
        logging.info(f"Python path: {python_path}")
        logging.info(f"Directory di lavoro: {script_dir}")
        logging.info(f"PYTHONPATH: {sys.path}")
        
        # Avvia l'applicazione
        main_script = src_dir / "main_v3.py"
        if not main_script.exists():
            raise FileNotFoundError(f"Script principale non trovato: {main_script}")
        
        logging.info("Avvio dell'applicazione...")
        
        # Esegui direttamente il modulo main
        try:
            import runpy
            runpy.run_path(str(main_script))
        except Exception as e:
            logging.error("Errore durante l'esecuzione dello script principale:")
            logging.error(traceback.format_exc())
            raise
        
    except Exception as e:
        logging.error(f"Errore durante l'avvio: {e}")
        logging.error(traceback.format_exc())
        input("Premi INVIO per chiudere...")
        sys.exit(1)

if __name__ == '__main__':
    main()
