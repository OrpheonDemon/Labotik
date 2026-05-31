"""
Script para verificar el estado del sistema de registro facial.
Ejecutar con: python -m app.check_face_registration
"""

import sys
import os

# Agregar backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Verifica que las dependencias necesarias estén instaladas."""
    print("=== Verificando dependencias ===")
    
    missing = []
    try:
        import cv2
        print("✓ OpenCV disponible")
    except ImportError:
        missing.append("opencv-python")
        print("✗ OpenCV NO disponible")
    
    try:
        from deepface import DeepFace
        print("✓ DeepFace disponible")
    except ImportError:
        missing.append("deepface")
        print("✗ DeepFace NO disponible")
    
    try:
        import numpy as np
        print("✓ NumPy disponible")
    except ImportError:
        missing.append("numpy")
        print("✗ NumPy NO disponible")
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy disponible")
    except ImportError:
        missing.append("sqlalchemy")
        print("✗ SQLAlchemy NO disponible")
    
    if missing:
        print(f"\n⚠ Faltan dependencias: {', '.join(missing)}")
        print("Instale con: pip install " + " ".join(missing))
        return False
    
    print("\n✓ Todas las dependencias están disponibles")
    return True

def check_face_service():
    """Verifica que el servicio facial esté disponible."""
    print("\n=== Verificando servicio facial ===")
    
    try:
        from app.services.face_service import FaceService
        
        if FaceService.is_available():
            print("✓ Servicio facial disponible")
            info = FaceService.get_model_info()
            print(f"  Modelo: {info['default_model']}")
            print(f"  Umbral: {info['default_threshold']}")
            return True
        else:
            print("✗ Servicio facial NO disponible")
            return False
    except Exception as e:
        print(f"✗ Error al verificar servicio facial: {e}")
        return False

def check_database():
    """Verifica que la base de datos y tablas existan."""
    print("\n=== Verificando base de datos ===")
    
    try:
        import asyncio
        from app.database import engine, Base, get_db
        from app.models_face import FaceEmbedding, FaceAuthLog
        from sqlalchemy import text, inspect
        
        async def check():
            async with engine.connect() as conn:
                # Verificar conexión
                await conn.execute(text("SELECT 1"))
                print("✓ Conexión a base de datos exitosa")
                
                # Verificar tablas
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
                if 'face_embeddings' in tables:
                    print("✓ Tabla face_embeddings existe")
                else:
                    print("✗ Tabla face_embeddings NO existe")
                    return False
                
                if 'face_auth_logs' in tables:
                    print("✓ Tabla face_auth_logs existe")
                else:
                    print("✗ Tabla face_auth_logs NO existe")
                    return False
                
                return True
        
        result = asyncio.run(check())
        return result
        
    except Exception as e:
        print(f"✗ Error al verificar base de datos: {e}")
        return False

def check_face_cascade():
    """Verifica que el clasificador de caras de OpenCV esté disponible."""
    print("\n=== Verificando clasificador de caras ===")
    
    try:
        import cv2
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            print("✗ Clasificador de caras NO cargado correctamente")
            return False
        else:
            print("✓ Clasificador de caras disponible")
            return True
    except Exception as e:
        print(f"✗ Error al verificar clasificador: {e}")
        return False

def main():
    print("=" * 50)
    print("VERIFICACIÓN DEL SISTEMA DE REGISTRO FACIAL")
    print("=" * 50)
    
    checks = [
        ("Dependencias", check_dependencies),
        ("Servicio facial", check_face_service),
        ("Base de datos", check_database),
        ("Clasificador de caras", check_face_cascade),
    ]
    
    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ Todos los checks pasaron. El sistema está listo.")
    else:
        print("❌ Algunos checks fallaron. Revise los errores arriba.")
        print("\nPara instalar dependencias faltantes:")
        print("  pip install deepface opencv-python numpy")
        print("\nPara crear las tablas en la base de datos:")
        print("  Ejecute: python migrate_face_auth.py")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())