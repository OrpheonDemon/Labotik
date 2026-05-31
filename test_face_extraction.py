"""
Test script to verify DeepFace embedding extraction
"""
import sys
import os

# Set environment variables to suppress oneDNN warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

sys.path.insert(0, 'backend')

import numpy as np
import cv2
from deepface import DeepFace

print("=== Testing DeepFace Embedding Extraction ===\n")

# Create a test image (simple white image with a face-like pattern)
# In real scenario, this would be an actual face image
test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255

# Draw a simple face-like pattern
cv2.circle(test_image, (320, 240), 100, (200, 200, 200), -1)  # Head
cv2.circle(test_image, (290, 220), 10, (0, 0, 0), -1)  # Left eye
cv2.circle(test_image, (350, 220), 10, (0, 0, 0), -1)  # Right eye
cv2.ellipse(test_image, (320, 260), (30, 20), 0, 0, 180, (0, 0, 0), 2)  # Mouth

# Save test image
test_image_path = "test_face.jpg"
cv2.imwrite(test_image_path, test_image)
print(f"✅ Created test image: {test_image_path}")

# Test 1: Try to detect faces with OpenCV
print("\n1. Testing OpenCV face detection:")
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    print(f"   Faces detected: {len(faces)}")
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            print(f"   Face at ({x}, {y}) with size {w}x{h}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Try to extract embedding with DeepFace
print("\n2. Testing DeepFace embedding extraction:")
try:
    print("   Loading model...")
    embedding_obj = DeepFace.represent(
        img_path=test_image_path,
        model_name="FaceNet",
        detector_backend="opencv",
        enforce_detection=False,
        align=True
    )
    
    if embedding_obj and len(embedding_obj) > 0:
        embedding = embedding_obj[0]["embedding"]
        print(f"   ✅ Embedding extracted successfully!")
        print(f"   Embedding size: {len(embedding)}")
        print(f"   First 10 values: {embedding[:10]}")
    else:
        print("   ❌ No embedding returned")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Try with a real image (if exists)
print("\n3. Testing with different model (VGG-Face):")
try:
    embedding_obj = DeepFace.represent(
        img_path=test_image_path,
        model_name="VGG-Face",
        detector_backend="opencv",
        enforce_detection=False,
        align=True
    )
    
    if embedding_obj and len(embedding_obj) > 0:
        embedding = embedding_obj[0]["embedding"]
        print(f"   ✅ Embedding extracted with VGG-Face!")
        print(f"   Embedding size: {len(embedding)}")
    else:
        print("   ❌ No embedding returned")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Clean up
try:
    os.remove(test_image_path)
    print(f"\n🗑️  Cleaned up test image")
except:
    pass

print("\n=== Test Complete ===")