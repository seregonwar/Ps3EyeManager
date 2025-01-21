"""
Script di avvio automatico per PS3 Eye Manager
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

import logging
import subprocess
import time
import traceback

def setup_logging():
    """Configure basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ps3eye_manager.log')
        ]
    )

def main():
    """Main function"""
    try:
        # Configure logging
        setup_logging()
        
        # Get the path of the script
        script_dir = Path(__file__).parent
        
        # Check if Python is in the PATH
        python_path = sys.executable
        if not python_path:
            raise RuntimeError("Python not found in PATH")
        
        logging.info(f"Python path: {python_path}")
        logging.info(f"Directory di lavoro: {script_dir}")
        logging.info(f"PYTHONPATH: {sys.path}")
        
        # Start the application
        main_script = Path(src_path) / "main.py"
        if not main_script.exists():
            raise FileNotFoundError(f"Main script not found: {main_script}")
        
        logging.info("Starting the application...")
        
        # Run the main module directly
        try:
            import runpy
            runpy.run_path(str(main_script))
        except Exception as e:
            logging.error("Error during execution of the main script:")
            logging.error(traceback.format_exc())
            raise
        
    except Exception as e:
        logging.error(f"Error during startup: {e}")
        logging.error(traceback.format_exc())
        input("Press ENTER to close...")
        sys.exit(1)

if __name__ == '__main__':
    main()
