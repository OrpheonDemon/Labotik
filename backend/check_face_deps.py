"""
Script para verificar que las dependencias de reconocimiento facial estén instaladas.
"""

import sys

def check_dependencies():
    print("Verificando dependencias de reconocimiento facial...")
    
    # Verificar numpy
    try:
        import numpy
        print(f"✅ numpy {numpy.__version__}")
    except ImportError:
        print("❌ numpy no está instalado")
        return False
    
    # Verificar opencv
    try:
        import cv2
        print(f"✅ opencv-python {cv2.__version__}")
    except ImportError:
        print("❌ opencv-python no está instalado")
        return False
    
    # Verificar deepface
    try:
        import deepface
        from deepface import DeepFace
        print(f"✅ deepface instalado")
    except ImportError:
        print("❌ deepface no está instalado")
        print("   Instala con: pip install deepface tf-keras")
        return False
    
    # Verificar tensorflow/keras (requerido por deepface)
    try:
        import tensorflow
        print(f"✅ tensorflow {tensorflow.__version__}")
    except ImportError:
        try:
            import tf_keras
            print(f"✅ tf-keras instalado")
        except ImportError:
            print("⚠️ tensorflow o tf-keras no está instalado (requerido por deepface)")
            print("   Instala con: pip install tf-keras")
            return False
    
    print("\n✅ Todas las dependencias están instaladas correctamente")
    return True

if __name__ == "__main__":
    success = check_dependencies()
    if not success:
        print("\nPara instalar las dependencias faltantes:")
        print("  pip install -r requirements.txt")
        sys.exit(1)