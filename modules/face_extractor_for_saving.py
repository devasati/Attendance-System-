import cv2
import numpy as np
import io
from PIL import Image


def extract_face_from_image(image_file, padding_percentage=0.2):
    try:
        # Read the image file
        img_array = np.frombuffer(image_file.read(), np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        img_height, img_width = img.shape[:2]

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Load the Haar Cascade classifier for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            return None  # No faces detected

        # Get the first face (assuming only one face is needed)
        (x, y, w, h) = faces[0]

        # Calculate padding amount based on face width/height
        padding_x = int(w * padding_percentage)
        padding_y = int(h * padding_percentage)

        # Apply padding to the coordinates (ensure they don't go beyond image boundaries)
        x1 = max(0, x - padding_x)
        y1 = max(0, y - padding_y)
        x2 = min(img_width, x + w + padding_x)
        y2 = min(img_height, y + h + padding_y)

        # Crop the face region with padding
        face_img = img[y1:y2, x1:x2]

        # Convert the OpenCV image (numpy array) to bytes that can be used by save_image
        # First convert BGR to RGB (OpenCV uses BGR, PIL uses RGB)
        face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_img = Image.fromarray(face_img_rgb)

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        return img_bytes

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None