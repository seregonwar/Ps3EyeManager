"""
Modulo per la gestione della telecamera PS3 Eye
"""
import ctypes
from ctypes import wintypes
from enum import IntEnum
import numpy as np
import os
import sys
from pathlib import Path
import logging

try:
    import cv2
except ImportError:
    cv2 = None
    logging.warning("OpenCV non trovato. La conversione del colore sarà limitata.")

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8)
    ]

class CLEyeCameraColorMode(IntEnum):
    CLEYE_GRAYSCALE = 0
    CLEYE_COLOR = 1

class CLEyeCameraResolution(IntEnum):
    CLEYE_QVGA = 0  # 320x240
    CLEYE_VGA = 1   # 640x480

class CLEyeCameraParameter(IntEnum):
    # Camera sensor parameters
    CLEYE_AUTO_GAIN = 0
    CLEYE_GAIN = 1
    CLEYE_AUTO_EXPOSURE = 2
    CLEYE_EXPOSURE = 3
    CLEYE_AUTO_WHITEBALANCE = 4
    CLEYE_WHITEBALANCE_RED = 5
    CLEYE_WHITEBALANCE_GREEN = 6
    CLEYE_WHITEBALANCE_BLUE = 7
    # Camera linear transform parameters
    CLEYE_HFLIP = 8
    CLEYE_VFLIP = 9
    CLEYE_HKEYSTONE = 10
    CLEYE_VKEYSTONE = 11
    CLEYE_XOFFSET = 12
    CLEYE_YOFFSET = 13
    CLEYE_ROTATION = 14
    CLEYE_ZOOM = 15
    # Camera non-linear transform parameters
    CLEYE_LENSCORRECTION1 = 16
    CLEYE_LENSCORRECTION2 = 17
    CLEYE_LENSCORRECTION3 = 18
    CLEYE_LENSBRIGHTNESS = 19

class PS3EyeCamera:
    def __init__(self):
        self._dll = None
        self._camera = None
        self._load_dll()
        
    def _load_dll(self):
        """Carica la DLL CLEyeMulticam"""
        try:
            # Determina se stiamo eseguendo Python a 32 o 64 bit
            is_64bits = sys.maxsize > 2**32
            
            # Cerca prima nella cartella drivers
            dll_path = str(Path(__file__).parent.parent / 'drivers' / 'CLEyeMulticam.dll')
            if not os.path.exists(dll_path):
                # Se non trovata, cerca in System32/SysWOW64
                if is_64bits:
                    system_dirs = [
                        os.path.join(os.environ['SystemRoot'], 'SysWOW64'),  # 32-bit DLLs su sistema 64-bit
                        os.path.join(os.environ['SystemRoot'], 'System32')
                    ]
                else:
                    system_dirs = [os.path.join(os.environ['SystemRoot'], 'System32')]
                
                dll_found = False
                for system_dir in system_dirs:
                    dll_path = os.path.join(system_dir, 'CLEyeMulticam.dll')
                    if os.path.exists(dll_path):
                        break
                else:
                    raise FileNotFoundError("CLEyeMulticam.dll non trovata")
            
            # Carica la DLL
            if is_64bits:
                self._dll = ctypes.WinDLL(dll_path, use_last_error=True, winmode=0)
            else:
                self._dll = ctypes.WinDLL(dll_path, use_last_error=True)
            
            # Definizione dei tipi per le funzioni della DLL
            self._dll.CLEyeGetCameraCount.restype = ctypes.c_int
            self._dll.CLEyeGetCameraUUID.argtypes = [ctypes.c_int]
            self._dll.CLEyeGetCameraUUID.restype = GUID
            
            self._dll.CLEyeCreateCamera.argtypes = [
                GUID,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int
            ]
            self._dll.CLEyeCreateCamera.restype = ctypes.c_void_p
            
            self._dll.CLEyeDestroyCamera.argtypes = [ctypes.c_void_p]
            self._dll.CLEyeDestroyCamera.restype = ctypes.c_bool
            
            self._dll.CLEyeCameraStart.argtypes = [ctypes.c_void_p]
            self._dll.CLEyeCameraStart.restype = ctypes.c_bool
            
            self._dll.CLEyeCameraStop.argtypes = [ctypes.c_void_p]
            self._dll.CLEyeCameraStop.restype = ctypes.c_bool
            
            self._dll.CLEyeSetCameraParameter.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_int
            ]
            self._dll.CLEyeSetCameraParameter.restype = ctypes.c_bool
            
            self._dll.CLEyeGetCameraParameter.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int
            ]
            self._dll.CLEyeGetCameraParameter.restype = ctypes.c_int
            
            self._dll.CLEyeCameraGetFrame.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_byte),
                ctypes.c_int
            ]
            self._dll.CLEyeCameraGetFrame.restype = ctypes.c_bool
            
            self._dll.CLEyeCameraGetFrameDimensions.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_int)
            ]
            self._dll.CLEyeCameraGetFrameDimensions.restype = ctypes.c_bool
            
        except Exception as e:
            raise RuntimeError(f"Errore nel caricamento della DLL CLEyeMulticam: {e}")

    def get_camera_count(self) -> int:
        """Restituisce il numero di telecamere PS3 Eye collegate"""
        return self._dll.CLEyeGetCameraCount()

    def get_camera_uuid(self, camera_index: int) -> GUID:
        """Restituisce l'UUID della telecamera all'indice specificato"""
        return self._dll.CLEyeGetCameraUUID(camera_index)

    def create_camera(self, uuid: GUID, color_mode: CLEyeCameraColorMode,
                     resolution: CLEyeCameraResolution, framerate: int) -> bool:
        """Crea un'istanza della telecamera con i parametri specificati"""
        self._camera = self._dll.CLEyeCreateCamera(uuid, color_mode, resolution, framerate)
        self._color_mode = color_mode
        return self._camera is not None

    def destroy_camera(self) -> bool:
        """Distrugge l'istanza della telecamera"""
        if self._camera:
            result = self._dll.CLEyeDestroyCamera(self._camera)
            self._camera = None
            return result
        return False

    def start_camera(self) -> bool:
        """Avvia la cattura video"""
        if self._camera:
            return self._dll.CLEyeCameraStart(self._camera)
        return False

    def stop_camera(self) -> bool:
        """Ferma la cattura video"""
        if self._camera:
            return self._dll.CLEyeCameraStop(self._camera)
        return False

    def set_parameter(self, param: CLEyeCameraParameter, value: int) -> bool:
        """Imposta un parametro della telecamera"""
        if self._camera:
            return self._dll.CLEyeSetCameraParameter(self._camera, param, value)
        return False

    def get_parameter(self, param: CLEyeCameraParameter) -> int:
        """Legge un parametro della telecamera"""
        if self._camera:
            return self._dll.CLEyeGetCameraParameter(self._camera, param)
        return -1

    def get_frame(self, timeout: int = 2000) -> np.ndarray:
        """
        Cattura un frame dalla telecamera
        
        Args:
            timeout: Timeout in millisecondi (default 2000ms)
            
        Returns:
            numpy.ndarray: Frame catturato come array numpy
        """
        if not self._camera:
            raise RuntimeError("Camera non inizializzata")
        
        # Alloca il buffer per il frame
        width = ctypes.c_int()
        height = ctypes.c_int()
        self._dll.CLEyeCameraGetFrameDimensions(self._camera, 
                                              ctypes.byref(width), 
                                              ctypes.byref(height))
        
        # Determina la dimensione del buffer in base al color mode
        channels = 1  # Default per grayscale
        if hasattr(self, '_color_mode') and self._color_mode == CLEyeCameraColorMode.CLEYE_COLOR:
            channels = 4  # RGBA per color mode
        
        buffer_size = width.value * height.value * channels
        buffer = (ctypes.c_byte * buffer_size)()
        
        if self._dll.CLEyeCameraGetFrame(self._camera, buffer, timeout):
            try:
                # Converti il buffer in numpy array
                frame = np.frombuffer(buffer, dtype=np.uint8)
                
                if channels == 1:
                    # Grayscale
                    frame = frame.reshape((height.value, width.value))
                    if cv2 is not None:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    else:
                        # Fallback senza OpenCV
                        frame = np.stack((frame,) * 3, axis=-1)
                else:
                    # RGBA -> BGR
                    frame = frame.reshape((height.value, width.value, channels))
                    if cv2 is not None:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    else:
                        # Fallback senza OpenCV - prendi solo i canali BGR
                        frame = frame[:, :, :3]
                    
                return frame
                
            except Exception as e:
                logging.error(f"Errore nell'elaborazione del frame: {str(e)}, shape: {frame.shape if 'frame' in locals() else 'N/A'}")
                raise RuntimeError(f"Errore nell'elaborazione del frame: {str(e)}")
        else:
            raise RuntimeError("Errore nella cattura del frame")

    def __del__(self):
        """Cleanup quando l'oggetto viene distrutto"""
        self.destroy_camera()

def main():
    """Test di funzionamento base della telecamera"""
    try:
        camera = PS3EyeCamera()
        count = camera.get_camera_count()
        print(f"Trovate {count} telecamere PS3 Eye")
        
        if count > 0:
            # Prendi la prima telecamera
            uuid = camera.get_camera_uuid(0)
            print(f"UUID telecamera: {uuid}")
            
            # Crea l'istanza della telecamera
            if camera.create_camera(uuid, CLEyeCameraColorMode.CLEYE_COLOR,
                                  CLEyeCameraResolution.CLEYE_VGA, 60):
                print("Telecamera creata con successo")
                
                # Imposta alcuni parametri
                camera.set_parameter(CLEyeCameraParameter.CLEYE_AUTO_GAIN, 1)
                camera.set_parameter(CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE, 1)
                camera.set_parameter(CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE, 1)
                
                # Avvia la telecamera
                if camera.start_camera():
                    print("Cattura video avviata")
                    
                    # Cattura un frame
                    try:
                        frame = camera.get_frame()
                        print(f"Frame catturato: {frame.shape}")
                    except Exception as e:
                        print(f"Errore nella cattura del frame: {e}")
                    
                    # Ferma la telecamera
                    camera.stop_camera()
                else:
                    print("Errore nell'avvio della telecamera")
            else:
                print("Errore nella creazione della telecamera")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
