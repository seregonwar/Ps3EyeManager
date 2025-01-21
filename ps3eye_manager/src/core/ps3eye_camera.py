"""
Module for managing the PS3 Eye camera
"""
import ctypes
from ctypes import wintypes
from enum import IntEnum
import numpy as np
import os
import sys
import cv2
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self._using_uvc = False
        self._frame_buffer = None
        self._frame_dimensions = None
        self._load_dll()
        
    def _load_dll(self):
        """Carica la DLL CLEyeMulticam"""
        try:
            # Determine if we are running Python in 32 or 64 bit
            is_64bits = sys.maxsize > 2**32
            logging.info(f"Python architecture: {'64-bit' if is_64bits else '32-bit'}")
            
            # Search first in the drivers folder
            dll_path = str(Path(__file__).parent.parent / 'drivers' / 'CLEyeMulticam.dll')
            logging.info(f"Searching DLL in: {dll_path}")
            
            if not os.path.exists(dll_path):
                logging.info("DLL not found in the drivers folder")
                # If not found, search in System32/SysWOW64
                if is_64bits:
                    system_dirs = [
                        os.path.join(os.environ['SystemRoot'], 'SysWOW64'),  # 32-bit DLLs on 64-bit system
                        os.path.join(os.environ['SystemRoot'], 'System32')
                    ]
                else:
                    system_dirs = [os.path.join(os.environ['SystemRoot'], 'System32')]
                
                logging.info(f"Searching DLL in system directories: {system_dirs}")
                
                dll_found = False
                for system_dir in system_dirs:
                    dll_path = os.path.join(system_dir, 'CLEyeMulticam.dll')
                    if os.path.exists(dll_path):
                        dll_found = True
                        logging.info(f"DLL found in: {dll_path}")
                        break
                
                if not dll_found:
                    logging.warning("CLEyeMulticam.dll not found, trying UVC generic driver")
                    return self._try_uvc_driver()
            else:
                logging.info("DLL found in the drivers folder")
            
            # Load the DLL
            logging.info(f"Attempting to load DLL from: {dll_path}")
            if is_64bits:
                self._dll = ctypes.WinDLL(dll_path, use_last_error=True, winmode=0)
            else:
                self._dll = ctypes.WinDLL(dll_path, use_last_error=True)
            
            logging.info("DLL loaded successfully")
            
            # Define types for DLL functions
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
            
            logging.info("DLL function types configured")
            
            # Verify the number of cameras
            count = self._dll.CLEyeGetCameraCount()
            logging.info(f"Number of cameras found: {count}")
            
            if count == 0:
                logging.warning("No camera found with CLEye driver, trying UVC generic driver")
                return self._try_uvc_driver()
            
            return True
            
        except Exception as e:
            error_code = ctypes.get_last_error() if self._dll else None
            logging.error(f"Error loading DLL CLEyeMulticam: {e} (error code: {error_code})")
            logging.info("Trying UVC generic driver")
            return self._try_uvc_driver()

    def _try_uvc_driver(self):
        """Prova a usare il driver UVC generico"""
        try:
            # Search for PS3 Eye among available webcams
            index = 0
            while index < 10:  # Try first 10 webcams
                cap = cv2.VideoCapture(index)
                if not cap.isOpened():
                    index += 1
                    continue
                
                # Read webcam properties
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                # Verify if it's a PS3 Eye (640x480 or 320x240)
                if (width == 640 and height == 480) or (width == 320 and height == 240):
                    vendor_id = None
                    product_id = None
                    
                    # Try to read vendor ID and product ID
                    try:
                        import pyudev
                        context = pyudev.Context()
                        for device in context.list_devices(subsystem='video4linux'):
                            if device.get('ID_V4L_PRODUCT') and 'PS3' in device.get('ID_V4L_PRODUCT'):
                                vendor_id = device.get('ID_VENDOR_ID')
                                product_id = device.get('ID_MODEL_ID')
                                break
                    except:
                        pass
                    
                    # If we can't verify the ID, assume it's a PS3 Eye
                    # if it has the correct resolutions
                    if vendor_id == '1415' and product_id == '2000':
                        logging.info(f"PS3 Eye found with UVC driver (index: {index})")
                        self._camera = cap
                        self._using_uvc = True
                        return True
                
                cap.release()
                index += 1
            
            logging.error("No PS3 Eye found with UVC driver")
            return False
            
        except Exception as e:
            logging.error(f"Error using UVC driver: {e}")
            return False

    def get_camera_count(self) -> int:
        """Returns the number of connected PS3 Eye cameras"""
        if self._using_uvc:
            return 1
        return self._dll.CLEyeGetCameraCount()

    def get_camera_uuid(self, camera_index: int) -> GUID:
        """Returns the UUID of the camera at the specified index"""
        if self._using_uvc:
            raise RuntimeError("The UVC driver does not support UUIDs")
        return self._dll.CLEyeGetCameraUUID(camera_index)

    def create_camera(self, uuid: GUID, color_mode: CLEyeCameraColorMode,
                     resolution: CLEyeCameraResolution, framerate: int) -> bool:
        """Create a camera instance with the specified parameters"""
        try:
            if self._using_uvc:
                raise RuntimeError("The UVC driver does not support camera creation")
            
            # Create the camera
            self._camera = self._dll.CLEyeCreateCamera(uuid, color_mode, resolution, framerate)
            if not self._camera:
                logging.error("Error creating camera")
                return False
                
            # Get frame dimensions
            width = ctypes.c_int()
            height = ctypes.c_int()
            if not self._dll.CLEyeCameraGetFrameDimensions(self._camera, 
                                                         ctypes.byref(width), 
                                                         ctypes.byref(height)):
                logging.error("Error getting frame dimensions")
                self.destroy_camera()
                return False
                
            # Allocate buffer for frame
            buffer_size = width.value * height.value * 4  # RGBA
            try:
                self._frame_buffer = (ctypes.c_byte * buffer_size)()
                self._frame_dimensions = (width.value, height.value)
                logging.info(f"Buffer allocated for frame {width.value}x{height.value}")
            except Exception as e:
                logging.error(f"Error allocating buffer: {e}")
                self.destroy_camera()
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error creating camera: {e}")
            if self._camera:
                self.destroy_camera()
            return False

    def destroy_camera(self):
        """Destroy the camera instance"""
        try:
            if self._using_uvc:
                if self._camera:
                    self._camera.release()
                return True
                
            if self._camera:
                # Stop capture before destroying
                self.stop_camera()
                
                # Destroy the camera
                result = self._dll.CLEyeDestroyCamera(self._camera)
                self._camera = None
                
                # Free the buffer
                self._frame_buffer = None
                self._frame_dimensions = None
                
                return result
                
            return False
            
        except Exception as e:
            logging.error(f"Error destroying camera: {e}")
            return False

    def start_camera(self) -> bool:
        """Start video capture"""
        if self._using_uvc:
            return True
        if self._camera:
            return self._dll.CLEyeCameraStart(self._camera)
        return False

    def stop_camera(self) -> bool:
        """Stop video capture"""
        if self._using_uvc:
            return True
        if self._camera:
            return self._dll.CLEyeCameraStop(self._camera)
        return False

    def set_parameter(self, param: CLEyeCameraParameter, value: int) -> bool:
        """Set a camera parameter"""
        if self._using_uvc:
            raise RuntimeError("The UVC driver does not support parameter modification")
        if self._camera:
            return self._dll.CLEyeSetCameraParameter(self._camera, param, value)
        return False

    def get_parameter(self, param: CLEyeCameraParameter) -> int:
        """Read a camera parameter"""
        if self._using_uvc:
            raise RuntimeError("The UVC driver does not support parameter reading")
        if self._camera:
            return self._dll.CLEyeGetCameraParameter(self._camera, param)
        return -1

    def get_frame(self, timeout: int = 2000) -> np.ndarray:
        """
        Capture a frame from the camera
        
        Args:
            timeout: Timeout in milliseconds (default 2000ms)
            
        Returns:
            numpy.ndarray: Frame captured as numpy array in BGR format
        """
        try:
            if self._using_uvc:
                ret, frame = self._camera.read()
                if not ret:
                    logging.error("Error capturing frame with UVC driver")
                    return None
                return frame
                
            if not self._camera or not self._frame_buffer or not self._frame_dimensions:
                logging.error("Camera not initialized correctly")
                return None
                
            # Capture frame in pre-allocated buffer
            if not self._dll.CLEyeCameraGetFrame(self._camera, self._frame_buffer, timeout):
                logging.error("Error capturing frame")
                return None
                
            try:
                # Convert buffer to numpy array
                frame = np.frombuffer(self._frame_buffer, dtype=np.uint8)
                frame = frame.reshape((self._frame_dimensions[1], self._frame_dimensions[0], 4))
                
                # Convert to RGB and keep values in the correct range
                frame_rgb = frame[..., :3].copy()  # Take only RGB channels
                
                # Apply a slight brightness correction safely
                frame_rgb = frame_rgb.astype(np.float32)
                frame_rgb = np.clip(frame_rgb * 1.2, 0, 255)  # Slightly increase brightness
                frame_rgb = frame_rgb.astype(np.uint8)
                
                # Convert to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                
                return frame_bgr
                
            except Exception as e:
                logging.error(f"Error converting frame: {e}")
                return None
                
        except Exception as e:
            logging.error(f"General error capturing frame: {e}")
            return None

    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.destroy_camera()

def main():
    """Test of basic camera functionality"""
    try:
        camera = PS3EyeCamera()
        count = camera.get_camera_count()
        print(f"Found {count} PS3 Eye cameras")
        
        if count > 0:
            # Take the first camera
            if not camera._using_uvc:
                uuid = camera.get_camera_uuid(0)
                print(f"Camera UUID: {uuid}")
            
            # Create the camera instance
            if not camera._using_uvc and not camera.create_camera(uuid, CLEyeCameraColorMode.CLEYE_COLOR,
                                  CLEyeCameraResolution.CLEYE_VGA, 60):
                print("Error creating camera")
                return
            
            print("Camera created successfully")
            
            # Set some parameters
            if not camera._using_uvc:
                camera.set_parameter(CLEyeCameraParameter.CLEYE_AUTO_GAIN, 1)
                camera.set_parameter(CLEyeCameraParameter.CLEYE_AUTO_EXPOSURE, 1)
                camera.set_parameter(CLEyeCameraParameter.CLEYE_AUTO_WHITEBALANCE, 1)
            
            # Start the camera
            if not camera.start_camera():
                print("Error starting camera")
                return
            
            print("Video capture started")
            
            # Capture a frame
            try:
                frame = camera.get_frame()
                print(f"Frame captured: {frame.shape}")
            except Exception as e:
                print(f"Error capturing frame: {e}")
            
            # Stop the camera
            camera.stop_camera()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
