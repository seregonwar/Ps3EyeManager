"""
Script di installazione per PS3 Eye Manager
Installa tutti i driver e le dipendenze necessarie
"""
import os
import sys
import subprocess
import winreg
import ctypes
import urllib.request
import zipfile
import shutil
import logging
from pathlib import Path

def is_admin():
    """Verifica se lo script è in esecuzione come amministratore"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Riavvia lo script come amministratore"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )

def setup_logging():
    """Configura il logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('install.log'),
            logging.StreamHandler()
        ]
    )

def check_python():
    """Verifica che Python sia installato correttamente"""
    logging.info("Verifica installazione Python...")
    if sys.version_info < (3, 8):
        logging.error("Python 3.8 o superiore è richiesto")
        return False
    return True

def install_pip_package(package):
    """Installa un pacchetto pip"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        logging.info(f"Pacchetto {package} installato con successo")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore nell'installazione di {package}: {e}")
        return False

def install_python_dependencies():
    """Installa le dipendenze Python"""
    dependencies = [
        "numpy",
        "opencv-python",
        "PyQt5",
        "comtypes",
        "pywin32"
    ]
    
    logging.info("Installazione dipendenze Python...")
    for dep in dependencies:
        if not install_pip_package(dep):
            return False
    return True

def download_file(url, filename):
    """Scarica un file da un URL"""
    try:
        logging.info(f"Download di {filename}...")
        urllib.request.urlretrieve(url, filename)
        return True
    except Exception as e:
        logging.error(f"Errore nel download di {filename}: {e}")
        return False

def install_obs():
    """Installa OBS Studio con Virtual Camera"""
    logging.info("Installazione OBS Studio...")
    
    # Download OBS
    obs_url = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-29.1.3-Full-Installer-x64.exe"
    obs_installer = "obs_installer.exe"
    
    if not download_file(obs_url, obs_installer):
        return False
    
    # Installa OBS silenziosamente con Virtual Camera
    try:
        subprocess.run([obs_installer, "/S", "/virtual-camera"], check=True)
        logging.info("OBS Studio installato con successo")
        os.remove(obs_installer)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore nell'installazione di OBS: {e}")
        return False

def install_unity_capture():
    """Installa Unity Capture come backup"""
    logging.info("Installazione Unity Capture...")
    
    # Download Unity Capture
    unity_url = "https://github.com/schellingb/UnityCapture/releases/download/v1.0.4/UnityCaptureDriver64.zip"
    unity_zip = "unity_capture.zip"
    
    if not download_file(unity_url, unity_zip):
        return False
    
    try:
        # Estrai il driver
        with zipfile.ZipFile(unity_zip, 'r') as zip_ref:
            zip_ref.extractall("unity_capture")
        
        # Installa il driver
        driver_path = Path("unity_capture/UnityCaptureDriver64/Install.bat")
        if driver_path.exists():
            subprocess.run([driver_path], check=True, shell=True)
            logging.info("Unity Capture installato con successo")
            shutil.rmtree("unity_capture")
            os.remove(unity_zip)
            return True
        else:
            logging.error("File di installazione Unity Capture non trovato")
            return False
    except Exception as e:
        logging.error(f"Errore nell'installazione di Unity Capture: {e}")
        return False

def install_ffmpeg():
    """Installa FFmpeg"""
    logging.info("Installazione FFmpeg...")
    try:
        # Usa winget per installare FFmpeg
        subprocess.run(["winget", "install", "FFmpeg"], check=True)
        logging.info("FFmpeg installato con successo")
        return True
    except subprocess.CalledProcessError:
        # Se winget fallisce, scarica manualmente
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        ffmpeg_zip = "ffmpeg.zip"
        
        if not download_file(ffmpeg_url, ffmpeg_zip):
            return False
        
        try:
            # Estrai FFmpeg
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall("ffmpeg")
            
            # Copia i file necessari in System32
            ffmpeg_dir = next(Path("ffmpeg").glob("ffmpeg-*"))
            for exe in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
                src = ffmpeg_dir / "bin" / exe
                dst = Path(os.environ["SystemRoot"]) / "System32" / exe
                shutil.copy2(src, dst)
            
            logging.info("FFmpeg installato manualmente con successo")
            shutil.rmtree("ffmpeg")
            os.remove(ffmpeg_zip)
            return True
        except Exception as e:
            logging.error(f"Errore nell'installazione manuale di FFmpeg: {e}")
            return False

def main():
    """Funzione principale di installazione"""
    # Verifica privilegi amministrativi
    if not is_admin():
        logging.warning("Riavvio come amministratore...")
        run_as_admin()
        return
    
    setup_logging()
    logging.info("=== Installazione PS3 Eye Manager ===")
    
    # Verifica requisiti
    if not check_python():
        return
    
    # Installa le dipendenze nell'ordine corretto
    steps = [
        ("Dipendenze Python", install_python_dependencies),
        ("OBS Studio", install_obs),
        ("Unity Capture", install_unity_capture),
        ("FFmpeg", install_ffmpeg)
    ]
    
    success = True
    for name, func in steps:
        logging.info(f"\nInstallazione {name}...")
        if not func():
            logging.error(f"Errore nell'installazione di {name}")
            success = False
            break
    
    if success:
        logging.info("\n=== Installazione completata con successo ===")
        logging.info("Riavvia il computer prima di usare PS3 Eye Manager")
    else:
        logging.error("\n=== Installazione fallita ===")
        logging.error("Controlla il file install.log per i dettagli")

if __name__ == "__main__":
    main()
