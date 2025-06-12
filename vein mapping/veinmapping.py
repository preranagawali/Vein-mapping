import cv2
import numpy as np
from skimage.restoration import denoise_wavelet
from skimage.morphology import skeletonize
from skimage.util import img_as_ubyte
import requests

# === CONFIGURATION ===
ESP32_CAM_URL = "http://<ESP_IP>/capture"  # Replace with your ESP32-CAM URL (e.g., http://192.168.4.1/capture)

def get_frame_from_esp32(url):
    try:
        resp = requests.get(url, stream=True, timeout=5)
        img_arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        return frame
    except:
        print("❌ Failed to get image from ESP32-CAM.")
        return None

def apply_wiener_like_denoising(gray_img):
    # Use wavelet denoising (approximate Wiener)
    denoised = denoise_wavelet(gray_img, multichannel=False, convert2ycbcr=False, rescale_sigma=True)
    return img_as_ubyte(denoised)

def apply_CLAHE(img):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(img)

def extract_veins(enhanced_img):
    # Thresholding
    _, thresh = cv2.threshold(enhanced_img, 30, 255, cv2.THRESH_BINARY)
    # Skeletonization (input needs to be binary)
    skeleton = skeletonize(thresh // 255)  # Convert to 0-1 for skimage
    return img_as_ubyte(skeleton)

def overlay_veins(original_img, vein_mask):
    overlay = original_img.copy()
    overlay[vein_mask != 0] = [0, 255, 0]  # Green overlay
    return overlay

# === MAIN FUNCTION ===
frame = get_frame_from_esp32(ESP32_CAM_URL)
if frame is not None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Step 1: Denoising (Wiener-like)
    denoised = apply_wiener_like_denoising(gray)

    # Step 2: Enhancement
    enhanced = apply_CLAHE(denoised)

    # Step 3: Feature Extraction (Threshold + Skeletonization)
    veins = extract_veins(enhanced)

    # Step 4: Overlay on original
    result = overlay_veins(frame, veins)

    # Display result
    cv2.imshow("Vein Mapping Output", result)
    cv2.imwrite("vein_map_output.jpg", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("⚠️ Could not process frame.")
