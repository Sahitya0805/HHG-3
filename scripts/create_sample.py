"""Creates a clean synthetic test face image for unit testing and offline demo testing."""

import cv2
import numpy as np

def make_sample_face(filepath="samples/demo_face.jpg"):
    # Create a 300x300 canvas
    img = np.full((300, 300, 3), (240, 240, 240), dtype=np.uint8)

    # Face Oval (skin tone)
    cv2.ellipse(img, (150, 150), (70, 95), 0, 0, 360, (180, 210, 235), -1)
    cv2.ellipse(img, (150, 150), (70, 95), 0, 0, 360, (140, 170, 200), 2)

    # Hair
    cv2.ellipse(img, (150, 90), (75, 45), 0, 180, 360, (40, 40, 60), -1)

    # Eyes
    cv2.ellipse(img, (125, 135), (14, 8), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (125, 135), 5, (70, 50, 30), -1)
    cv2.ellipse(img, (175, 135), (14, 8), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (175, 135), 5, (70, 50, 30), -1)

    # Eyebrows
    cv2.line(img, (110, 120), (140, 122), (40, 40, 50), 3)
    cv2.line(img, (160, 122), (190, 120), (40, 40, 50), 3)

    # Nose
    pts = np.array([[150, 145], [145, 170], [155, 170]], np.int32)
    cv2.polylines(img, [pts], False, (130, 150, 180), 2)

    # Smile / Mouth
    cv2.ellipse(img, (150, 195), (28, 14), 0, 0, 180, (80, 80, 180), 3)

    cv2.imwrite(filepath, img)
    print(f"Created sample face at {filepath}")

if __name__ == "__main__":
    make_sample_face()
