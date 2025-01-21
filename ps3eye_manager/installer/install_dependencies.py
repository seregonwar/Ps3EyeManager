"""
Installation script for PS3 Eye Manager
Installs all necessary drivers and dependencies
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
    """Check if the script is running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart the script as administrator"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('install.log'),
            logging.StreamHandler()
        ]
    )

def check_python():
    """Check if Python is installed correctly"""
    logging.info("Checking Python installation...")
    if sys.version_info < (3, 8):
        logging.error("Python 3.8 or higher is required")
        return False
    return True

def install_pip_package(package):
    """Install a pip package"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        logging.info(f"Package {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error installing {package}: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    dependencies = [
        "numpy",
        "opencv-python",
        "PyQt5",
        "comtypes",
        "pywin32"
    ]
    
    logging.info("Installing Python dependencies...")
    for dep in dependencies:
        if not install_pip_package(dep):
            return False
    return True

def download_file(url, filename):
    """Download a file from a URL"""
    try:
        logging.info(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
        return True
    except Exception as e:
        logging.error(f"Error downloading {filename}: {e}")
        return False

def install_obs():
    """Install OBS Studio with Virtual Camera"""
    logging.info("Installing OBS Studio...")
    
    # Download OBS
    obs_url = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-29.1.3-Full-Installer-x64.exe"
    obs_installer = "obs_installer.exe"
    
    if not download_file(obs_url, obs_installer):
        return False
    
    # Install OBS silently with Virtual Camera
    try:
        subprocess.run([obs_installer, "/S", "/virtual-camera"], check=True)
        logging.info("OBS Studio installed successfully")
        os.remove(obs_installer)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error installing OBS: {e}")
        return False

def install_unity_capture():
    """Install Unity Capture as a backup"""
    logging.info("Installing Unity Capture...")
    
    # Download Unity Capture
    unity_url = "https://github.com/schellingb/UnityCapture/releases/download/v1.0.4/UnityCaptureDriver64.zip"
    unity_zip = "unity_capture.zip"
    
    if not download_file(unity_url, unity_zip):
        return False
    
    try:
        # Extract the driver
        with zipfile.ZipFile(unity_zip, 'r') as zip_ref:
            zip_ref.extractall("unity_capture")

        # Install the driver
        driver_path = Path("unity_capture/UnityCaptureDriver64/Install.bat")
        if driver_path.exists():
            subprocess.run([driver_path], check=True, shell=True)
            logging.info("Unity Capture installed successfully")
            shutil.rmtree("unity_capture")
            os.remove(unity_zip)
            return True
        else:
            logging.error("Unity Capture installation file not found")
            return False
    except Exception as e:
        logging.error(f"Error installing Unity Capture: {e}")
        return False

def install_ffmpeg():
    """Install FFmpeg"""
    logging.info("Installing FFmpeg...")
    try:
        # Use winget to install FFmpeg
        subprocess.run(["winget", "install", "FFmpeg"], check=True)
        logging.info("FFmpeg installed successfully")
        return True
    except subprocess.CalledProcessError:
        # If winget fails, download manually
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        ffmpeg_zip = "ffmpeg.zip"
        
        if not download_file(ffmpeg_url, ffmpeg_zip):
            return False
        
        try:
            # Extract FFmpeg
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall("ffmpeg")
            
            # Copy necessary files to System32
            ffmpeg_dir = next(Path("ffmpeg").glob("ffmpeg-*"))
            for exe in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
                src = ffmpeg_dir / "bin" / exe
                dst = Path(os.environ["SystemRoot"]) / "System32" / exe
                shutil.copy2(src, dst)
            
            logging.info("FFmpeg installed manually successfully")
            shutil.rmtree("ffmpeg")
            os.remove(ffmpeg_zip)
            return True
        except Exception as e:
            logging.error(f"Error installing FFmpeg manually: {e}")
            return False

def main():
    """Main installation function"""
    # Check administrative privileges
    if not is_admin():
        logging.warning("Restarting as administrator...")
        run_as_admin()
        return
    
    setup_logging()
    logging.info("=== Installation of PS3 Eye Manager ===")
    
    # Check requirements
    if not check_python():
        return
    
    # Install dependencies in the correct order
    steps = [
        ("Python dependencies", install_python_dependencies),
        ("OBS Studio", install_obs),
        ("Unity Capture", install_unity_capture),
        ("FFmpeg", install_ffmpeg)
    ]
    
    success = True
    for name, func in steps:
        logging.info(f"\nInstallation of {name}...")
        if not func():
            logging.error(f"Error installing {name}")
            success = False
            break
    
    if success:
        logging.info("\n=== Installation completed successfully ===")
        logging.info("Restart the computer before using PS3 Eye Manager")
    else:
        logging.error("\n=== Installation failed ===")
        logging.error("Check the install.log file for details")

if __name__ == "__main__":
    main()
