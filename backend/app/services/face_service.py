"""
Servicio de reconocimiento facial para autenticación biométrica.
Proporciona funciones para extracción, comparación y gestión de embeddings faciales.
Usa deepface como backend (compatible con Windows sin necesidad de dlib).
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, Any
import base64
import io
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Importación condicional para manejar errores de instalación
try:
    from deepface import DeepFace
    import cv2
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("DeepFace disponible para reconocimiento facial")
except ImportError as e:
    logger.warning(f"DeepFace no disponible: {e}")
    FACE_RECOGNITION_AVAILABLE = False


class FaceService:
    """
    Servicio para operaciones de reconocimiento facial.
    Usa DeepFace como backend (más compatible con Windows).
    """
    
    # Umbral por defecto para matching facial (0.6 es estricto, 0.8 es más flexible)
    DEFAULT_THRESHOLD = 0.8
    
    # Umbral de calidad mínima para registro
    MIN_QUALITY_THRESHOLD = 0.3
    
    # Tamaño máximo de imagen (en bytes) - 10MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    
    # Modelo de DeepFace a usar (VGG-Face es bueno para verificación)
    MODELS = {
        "facenet": "FaceNet",
        "vggface": "VGG-Face",
        "openface": "OpenFace",
        "deepface": "DeepFace",
        "deepid": "DeepID",
        "dlib": "Dlib",
        "arcface": "ArcFace",
        "ghostfacenet": "GhostFaceNet",
        "sface": "SFace",
        "buffalo_l": "Buffalo_L"
    }
    # FaceNet genera embeddings de 128 dimensiones
    DEFAULT_MODEL = "Facenet"
    
    # Backend para detección de rostros
    DETECTOR_BACKEND = "opencv"  # opencv, ssd, dlib, mtcnn, fastmtcnn, retinaface, mediapipe, yunet, centerface
    
    # Número máximo de intentos fallidos antes de bloqueo temporal
    MAX_FAILED_ATTEMPTS = 5
    
    # Tiempo de bloqueo después de máximos intentos fallidos (minutos)
    LOCKOUT_DURATION_MINUTES = 15
    
    @staticmethod
    def is_available() -> bool:
        """Verifica si las librerías de reconocimiento facial están disponibles."""
        return FACE_RECOGNITION_AVAILABLE
    
    @staticmethod
    def decode_base64_image(image_base64: str) -> Optional[np.ndarray]:
        """
        Decodifica una imagen en base64 a formato numpy array para OpenCV.
        
        Args:
            image_base64: Imagen codificada en base64
            
        Returns:
            Numpy array de la imagen o None si hay error
        """
        try:
            # Eliminar prefijo data:image si existe
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            
            # Decodificar base64
            image_data = base64.b64decode(image_base64)
            
            # Verificar tamaño
            if len(image_data) > FaceService.MAX_IMAGE_SIZE:
                logger.warning(f"Imagen demasiado grande: {len(image_data)} bytes")
                return None
            
            # Convertir a numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            
            # Decodificar imagen con OpenCV
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("No se pudo decodificar la imagen")
                return None
            
            return img
            
        except Exception as e:
            logger.error(f"Error al decodificar imagen base64: {e}")
            return None
    
    @staticmethod
    def preprocess_image(image: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para mejorar la detección facial.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen preprocesada
        """
        # Redimensionar si es demasiado grande (max 1000px en lado más largo)
        max_dim = 1000
        height, width = image.shape[:2]
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            image = cv2.resize(image, (int(width * scale), int(height * scale)))
        
        return image
    
    @staticmethod
    def extract_embedding(image_path: str = None, 
                         image_data: np.ndarray = None,
                         model_name: str = None) -> Optional[List[float]]:
        """
        Extrae el embedding facial usando DeepFace.
        
        Args:
            image_path: Ruta a la imagen (opcional)
            image_data: Imagen como numpy array (opcional)
            model_name: Modelo a usar
            
        Returns:
            Lista de floats representando el embedding, o None si falla.
        """
        temp_file = None
        try:
            if not FACE_RECOGNITION_AVAILABLE:
                logger.error("DeepFace no disponible")
                return None
            
            if model_name is None:
                model_name = FaceService.DEFAULT_MODEL
            
            # DeepFace necesita ruta o array
            if image_data is not None:
                # Guardar temporalmente para DeepFace
                import tempfile
                import os
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                cv2.imwrite(temp_path, image_data)
                image_path = temp_path
            
            if image_path is None:
                logger.error("No se proporcionó imagen")
                return None
            
            # Intentar con el modelo principal y fallbacks (Siempre el mismo que se usó para registrar)
            embedding = None
            models_to_try = [model_name, "Facenet", "ArcFace", "VGG-Face", "OpenFace", "SFace"]
            # Eliminar duplicados manteniendo orden
            seen = set()
            models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]
            
            for model in models_to_try:
                try:
                    logger.info(f"Intentando extraer embedding con modelo: {model}")
                    embedding_obj = DeepFace.represent(
                        img_path=image_path,
                        model_name=model,
                        detector_backend=FaceService.DETECTOR_BACKEND,
                        enforce_detection=False,
                        align=True
                    )
                    
                    if embedding_obj and len(embedding_obj) > 0:
                        embedding = embedding_obj[0]["embedding"]
                        logger.info(f"Embedding extraído exitosamente con modelo {model}")
                        break
                except Exception as model_error:
                    logger.warning(f"Modelo {model} falló: {model_error}")
                    continue
            
            if embedding is None:
                logger.error("Ningún modelo pudo extraer el embedding")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error al extraer embedding facial: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Siempre limpiar archivo temporal
            if temp_file is not None:
                import os
                try:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                except:
                    pass
    
    @staticmethod
    def process_and_extract(image_data: str) -> Dict[str, Any]:
        """
        Procesa una imagen base64 y extrae todos los embeddings faciales.
        
        Args:
            image_data: Imagen en base64
            
        Returns:
            Diccionario con:
            - success: bool
            - embeddings: lista de embeddings
            - face_count: número de rostros detectados
            - error: mensaje de error si aplica
            - quality_scores: lista de scores de calidad
        """
        result = {
            "success": False,
            "embeddings": [],
            "face_count": 0,
            "error": None,
            "quality_scores": []
        }
        
        try:
            if not FACE_RECOGNITION_AVAILABLE:
                result["error"] = "Servicio de reconocimiento facial no disponible. Instale deepface y opencv-python."
                return result
            
            # Decodificar imagen
            image = FaceService.decode_base64_image(image_data)
            if image is None:
                result["error"] = "No se pudo decodificar la imagen. Verifique que el formato sea válido."
                return result
            
            # Preprocesar
            image = FaceService.preprocess_image(image)
            
            # Guardar temporalmente
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                cv2.imwrite(tmp.name, image)
                temp_path = tmp.name
            
            try:
                # Detectar rostros con OpenCV para contar
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                result["face_count"] = len(faces)
                
                if result["face_count"] == 0:
                    result["error"] = "No se detectó ningún rostro en la imagen. Asegúrese de que haya suficiente iluminación y que el rostro sea visible."
                    return result
                
                # Extraer embedding con DeepFace
                embedding = FaceService.extract_embedding(image_path=temp_path)
                
                if embedding is not None:
                    result["embeddings"].append(embedding)
                    
                    # Calcular calidad basada en tamaño del rostro detectado y otras métricas
                    if len(faces) > 0:
                        x, y, w, h = faces[0]
                        face_size = w * h
                        image_area = image.shape[0] * image.shape[1]
                        
                        # Calidad basada en tamaño del rostro (0.3 a 1.0)
                        size_quality = min(1.0, face_size / 10000)
                        
                        # Calidad basada en la proporción del rostro en la imagen (ideal: 10-30%)
                        face_ratio = face_size / image_area
                        ratio_quality = min(1.0, max(0.0, (face_ratio - 0.05) / 0.15))
                        
                        # Calidad basada en la posición (centrado)
                        cx, cy = x + w/2, y + h/2
                        img_cx, img_cy = image.shape[1]/2, image.shape[0]/2
                        center_dist = ((cx - img_cx)**2 + (cy - img_cy)**2)**0.5
                        max_dist = ((img_cx)**2 + (img_cy)**2)**0.5
                        position_quality = max(0.0, 1.0 - (center_dist / max_dist))
                        
                        # Calidad combinada
                        quality = (size_quality * 0.4 + ratio_quality * 0.3 + position_quality * 0.3)
                        quality = max(0.1, min(1.0, quality))
                        
                        result["quality_scores"].append(quality)
                    else:
                        result["quality_scores"].append(0.5)
                    
                    result["success"] = True
                else:
                    result["error"] = "No se pudo extraer el embedding del rostro detectado. Intente con otra imagen."
                
            finally:
                # Limpiar archivo temporal
                import os
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error en process_and_extract: {e}")
            import traceback
            traceback.print_exc()
            result["error"] = f"Error interno: {str(e)}"
            return result
    
    @staticmethod
    def compare_embeddings(embedding1: List[float], embedding2: List[float], 
                          threshold: float = None) -> Tuple[bool, float]:
        """
        Compara dos embeddings faciales.
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
            threshold: Umbral de similitud
            
        Returns:
            Tupla (match, distance)
        """
        try:
            if threshold is None:
                threshold = FaceService.DEFAULT_THRESHOLD
            
            # Verificar que los embeddings tengan el mismo tamaño
            if len(embedding1) != len(embedding2):
                logger.error(f"Tamaños de embedding diferentes: {len(embedding1)} vs {len(embedding2)}")
                return False, float('inf')
            
            # Convertir a numpy arrays
            emb1 = np.array(embedding1, dtype=np.float64)
            emb2 = np.array(embedding2, dtype=np.float64)
            
            # Calcular distancia euclidiana
            distance = float(np.linalg.norm(emb1 - emb2))
            
            # Calcular similitud (1 - distancia normalizada)
            similarity = max(0.0, 1.0 - distance)
            
            # Match si la distancia es menor al umbral
            match = distance < threshold
            
            logger.info(f"Comparación facial: distancia={distance:.4f}, umbral={threshold}, match={match}, similitud={similarity:.4f}")
            
            return match, distance
            
        except Exception as e:
            logger.error(f"Error al comparar embeddings: {e}")
            return False, float('inf')
    
    @staticmethod
    def find_best_match(query_embedding: List[float], 
                       candidate_embeddings: List[Dict[str, Any]],
                       threshold: float = None) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Encuentra el mejor match para un embedding entre una lista de candidatos.
        
        Args:
            query_embedding: Embedding a buscar
            candidate_embeddings: Lista de diccionarios con embedding
            threshold: Umbral de similitud
            
        Returns:
            Tupla (mejor_match, distancia)
        """
        if threshold is None:
            threshold = FaceService.DEFAULT_THRESHOLD
        
        logger.info(f"Buscando mejor match entre {len(candidate_embeddings)} candidatos (umbral: {threshold})")
        logger.info(f"Tamaño del embedding de consulta: {len(query_embedding)}")
        
        best_match = None
        best_distance = float('inf')
        
        for i, candidate in enumerate(candidate_embeddings):
            candidate_embedding = candidate.get("embedding")
            if candidate_embedding is None:
                logger.warning(f"Candidato {i} no tiene embedding")
                continue
            
            logger.info(f"Candidato {i}: usuario={candidate.get('id_usuario')}, tabla={candidate.get('tabla_usuario')}, tamaño_embedding={len(candidate_embedding)}")
            
            match, distance = FaceService.compare_embeddings(
                query_embedding, 
                candidate_embedding,
                threshold
            )
            
            if match and distance < best_distance:
                best_match = candidate
                best_distance = distance
                logger.info(f"Nuevo mejor match encontrado: distancia={distance:.4f}")
        
        if best_match is None:
            logger.warning("No se encontró ningún match")
        else:
            logger.info(f"Mejor match final: usuario={best_match.get('id_usuario')}, distancia={best_distance:.4f}")
        
        return best_match, best_distance
    
    @staticmethod
    def validate_face_quality(embedding: List[float], 
                             face_location: Tuple = None) -> float:
        """
        Valida la calidad de un embedding facial.
        
        Args:
            embedding: Embedding a validar
            face_location: Ubicación del rostro (opcional)
            
        Returns:
            Score de calidad (0.0 a 1.0)
        """
        if not embedding:
            return 0.0
        
        # Verificar que no sea todo ceros
        if np.allclose(embedding, 0):
            return 0.0
        
        # Calcular magnitud
        magnitude = np.linalg.norm(embedding)
        quality = min(1.0, magnitude)
        
        return float(quality)
    
    @staticmethod
    def should_allow_attempt(last_failed_attempt: datetime = None,
                            failed_attempts: int = 0) -> Tuple[bool, str]:
        """
        Verifica si se debe permitir un intento de autenticación.
        Implementa rate limiting básico.
        
        Args:
            last_failed_attempt: Timestamp del último intento fallido
            failed_attempts: Número de intentos fallidos consecutivos
            
        Returns:
            Tupla (allowed, reason)
        """
        if failed_attempts >= FaceService.MAX_FAILED_ATTEMPTS:
            if last_failed_attempt:
                time_since_last = datetime.now() - last_failed_attempt
                lockout_duration = timedelta(minutes=FaceService.LOCKOUT_DURATION_MINUTES)
                
                if time_since_last < lockout_duration:
                    remaining = lockout_duration - time_since_last
                    return False, f"Demasiados intentos fallidos. Espere {remaining.seconds // 60} minutos."
            
            return True, "OK"
        
        return True, "OK"
    
    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        """
        Obtiene información sobre el servicio de reconocimiento facial.
        
        Returns:
            Diccionario con información del modelo
        """
        return {
            "available": FACE_RECOGNITION_AVAILABLE,
            "default_model": FaceService.DEFAULT_MODEL,
            "supported_models": list(FaceService.MODELS.keys()),
            "default_threshold": FaceService.DEFAULT_THRESHOLD,
            "embedding_size": "variable (según modelo)",
            "backend": "deepface",
            "version": "1.0.0"
        }