
# Ps3EyeManager

**Ps3EyeManager** is a program that allows you to use the **PS3 Eye** peripheral on any Windows PC.  
It has been tested with the **AY0140890** and is fully functional.

---

## 🛠️ **Requirements**

### Drivers and Libraries Required
- **CL-Eye Test Driver**  
  Already included in the programme in the `drivers` folder.
  
- **Custom Driver: ps3eye_virtual_camera.dll**  
  Essential to virtualise the camera for third-party applications such as Discord.

- **OpenCV**  
  An essential library for image and video management.

### Versions of Python
- **Python 3.11 (32-bit)**  
  This specific version is required to ensure compatibility with CL-Eye drivers, which are about two decades old.  
  > ⚠️ Note: For full 64-bit compatibility, it would be necessary to rewrite all drivers from scratch.

- **Python 3.12+ (64-bit)**  
  Used for the main programme.

### Dependencies
- The required dependencies are specified in the `requirements.txt` file, available in the `src` folder.

---

## ⚙️ **Installation**

1. **Inclusions in the package  
   Most of the elements listed above are already present within the source code or can be installed automatically.

2. **Integrated installer:**  
   You can use the preconfigured installer in the `src/installer` folder.

## What is missing/implemented?
- Use with third-party applications needs to be implemented (working on it)
- Stabilised fps reception, it goes up and down randomly, which is normal, but I want to understand if the problem is due to the implementation or to the camera
- Adapted video settings, currently the webcam makes all the people it shoots blue, I don't think it's appropriate to go into calls like that.
- A quality upscale system, having native access you could work on some values to upscale the quality, using your video card for example.


