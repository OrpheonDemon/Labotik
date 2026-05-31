"""
Servicio de reconocimiento facial V2 - Método profesional.
Usa DeepFace.verify() para comparación directa de imágenes,
sin necesidad de manejar embeddings manualmente.
También usa retinaface o mtcnn para detección más precisa.
"""
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
import base64
import io
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
    import cv2
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("DeepFace V2 disponible")
except ImportError as e:
    logger.warning(f"DeepFace no disponible: {e}")
    FACE_RECOGNITION_AVAILABLE = False

class FaceServiceV2:
    """
    Versión profesional del servicio de reconocimiento facial.
    Características:
    - DeepFace.verify() para comparación directa
    - Detección con OpenCV (más compatible)
    - Almacenamiento de imágenes codificadas en base64
    - Matching robusto
    """
    
    # Umbral de similitud (cosine similarity)
    DEFAULT_THRESHOLD = 0.4  # Más permisivo
    
    # Número máximo de intentos fallidos antes de bloqueo temporal
    MAX_FAILED_ATTEMPTS = 5
    
    # Tiempo de bloqueo después de máximos intentos fallidos (minutos)
    LOCKOUT_DURATION_MINUTES = 15
    
    # Modelo de DeepFace
    DEFAULT_MODEL = "Facenet"  # 128 dimensiones, rápido y preciso
    
    @staticmethod
    def is_available() -> bool:
        return FACE_RECOGNITION_AVAILABLE
    
    @staticmethod
    def decode_base64_image(image_base64: str) -> Optional[np.ndarray]:
        try:
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            image_data = base64.b64decode(image_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decodificando imagen: {e}")
            return None
    
    @staticmethod
    def detect_faces(image: np.ndarray) -> List[tuple]:
        """Detecta rostros usando OpenCV Haar Cascade."""
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Parámetros más estrictos para evitar falsos positivos
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.3,  # Más exigente
            minNeighbors=7,   # Más vecinos requeridos
            minSize=(100, 100)  # Rostro debe ser al menos 100x100
        )
        return [(x, y, w, h) for (x, y, w, h) in faces]
    
    @staticmethod
    def extract_embedding(image: np.ndarray) -> Optional[List[float]]:
        """Extrae embedding usando DeepFace."""
        import tempfile
        import os
        
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            cv2.imwrite(temp_path, image)
            
            embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name=FaceServiceV2.DEFAULT_MODEL,
                detector_backend="opencv",
                enforce_detection=False,
                align=True
            )
            
            if embedding_obj and len(embedding_obj) > 0:
                return embedding_obj[0]["embedding"]
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo embedding: {e}")
            return None
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    @staticmethod
    def compare_embeddings(emb1: List[float], emb2: List[float]) -> Tuple[bool, float]:
        """Compara dos embeddings usando distancia coseno."""
        try:
            if len(emb1) != len(emb2):
                logger.error(f"Tamaños diferentes: {len(emb1)} vs {len(emb2)}")
                return False, 1.0
            
            emb1_np = np.array(emb1, dtype=np.float64)
            emb2_np = np.array(emb2, dtype=np.float64)
            
            # Distancia coseno
            dot_product = np.dot(emb1_np, emb2_np)
            norm1 = np.linalg.norm(emb1_np)
            norm2 = np.linalg.norm(emb2_np)
            
            if norm1 == 0 or norm2 == 0:
                return False, 1.0
            
            cosine_similarity = dot_product / (norm1 * norm2)
            distance = 1.0 - cosine_similarity
            
            match = distance < FaceServiceV2.DEFAULT_THRESHOLD
            
            logger.info(f"Comparación: distancia_coseno={distance:.4f}, "
                       f"similitud={cosine_similarity:.4f}, "
                       f"umbral={FaceServiceV2.DEFAULT_THRESHOLD}, "
                       f"match={match}")
            
            return match, float(distance)
            
        except Exception as e:
            logger.error(f"Error comparando embeddings: {e}")
            return False, 1.0
    
    @staticmethod
    def process_and_extract(image_data: str) -> Dict[str, Any]:
        """
        Procesa imagen y extrae embedding.
        Método profesional con mejor detección.
        """
        result = {
            "success": False,
            "embeddings": [],
            "face_count": 0,
            "error": None,
            "quality_scores": [],
            "face_images": []  # Almacena imágenes de rostros recortados
        }
        
        try:
            if not FACE_RECOGNITION_AVAILABLE:
                result["error"] = "DeepFace no disponible"
                return result
            
            image = FaceServiceV2.decode_base64_image(image_data)
            if image is None:
                result["error"] = "No se pudo decodificar la imagen"
                return result
            
            # Redimensionar si es muy grande
            h, w = image.shape[:2]
            if max(h, w) > 800:
                scale = 800 / max(h, w)
                image = cv2.resize(image, (int(w * scale), int(h * scale)))
            
            # Detectar rostros con mejor precisión
            faces = FaceServiceV2.detect_faces(image)
            result["face_count"] = len(faces)
            
            if result["face_count"] == 0:
                result["error"] = "No se detectó ningún rostro"
                return result
            
            if result["face_count"] > 1:
                result["error"] = "Múltiples rostros detectados"
                return result
            
            # Extraer embedding del rostro
            embedding = FaceServiceV2.extract_embedding(image)
            
            if embedding is not None:
                result["embeddings"].append(embedding)
                
                # Calcular calidad
                x, y, w, h = faces[0]
                quality = min(1.0, (w * h) / 50000)
                result["quality_scores"].append(quality)
                result["success"] = True
            else:
                result["error"] = "No se pudo extraer el embedding"
            
            return result
            
        except Exception as e:
            logger.error(f"Error en process_and_extract: {e}")
            result["error"] = str(e)
            return result
    
    @staticmethod
    def find_best_match(query_embedding: List[float],
                       candidates: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], float]:
        """Encuentra el mejor match entre candidatos."""
        best_match = None
        best_distance = 1.0  # Distancia coseno (0=idéntico, 1=diferente)
        
        for candidate in candidates:
            candidate_embedding = candidate.get("embedding")
            if candidate_embedding is None:
                continue
            
            match, distance = FaceServiceV2.compare_embeddings(
                query_embedding,
                candidate_embedding
            )
            
            if match and distance < best_distance:
                best_match = candidate
                best_distance = distance
        
        return best_match, best_distance
    
    @staticmethod
    def should_allow_attempt(last_failed_attempt: datetime = None,
                            failed_attempts: int = 0) -> Tuple[bool, str]:
        """Verifica si se debe permitir un intento de autenticación."""
        if failed_attempts >= FaceServiceV2.MAX_FAILED_ATTEMPTS:
            if last_failed_attempt:
                time_since_last = datetime.now() - last_failed_attempt
                lockout_duration = timedelta(minutes=FaceServiceV2.LOCKOUT_DURATION_MINUTES)
                if time_since_last < lockout_duration:
                    remaining = lockout_duration - time_since_last
                    return False, f"Demasiados intentos fallidos. Espere {remaining.seconds // 60} minutos."
            return True, "OK"
        return True, "OK"
    
    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        return {
            "available": FACE_RECOGNITION_AVAILABLE,
            "model": FaceServiceV2.DEFAULT_MODEL,
            "threshold": FaceServiceV2.DEFAULT_THRESHOLD,
            "method": "cosine_similarity",
            "version": "2.0"
        }