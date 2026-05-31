"""
Script de migración para agregar tablas de autenticación facial.
Este script crea las tablas face_embeddings y face_auth_logs sin afectar las tablas existentes.
"""

import asyncio
import sys
from sqlalchemy import text

async def migrate_face_auth():
    """
    Crea las tablas de autenticación facial si no existen.
    Usa CREATE TABLE IF NOT EXISTS para ser idempotente.
    """
    from app.database import engine
    
    print("🚀 Iniciando migración de autenticación facial...")
    
    try:
        async with engine.begin() as conn:
            # Verificar tablas existentes
            result = await conn.execute(text("SHOW TABLES"))
            existing_tables = [row[0] for row in result.fetchall()]
            
            # Crear tabla face_embeddings si no existe
            if "face_embeddings" not in existing_tables:
                print("📝 Creando tabla face_embeddings...")
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS face_embeddings (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        id_usuario VARCHAR(50) NOT NULL,
                        tabla_usuario ENUM('pacientes', 'medicos', 'laboratoristas', 'administradores') NOT NULL,
                        embedding_data JSON NOT NULL,
                        modelo_version VARCHAR(20) DEFAULT 'deepface_v1',
                        calidad_promedio FLOAT DEFAULT 0.0,
                        activo BOOLEAN DEFAULT TRUE,
                        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                        actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        intentos_fallidos INT DEFAULT 0,
                        ultimo_intento_fallido DATETIME NULL,
                        notas TEXT NULL,
                        INDEX idx_id_usuario (id_usuario),
                        INDEX idx_activo (activo)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                print("✅ Tabla face_embeddings creada exitosamente")
            else:
                print("ℹ️  Tabla face_embeddings ya existe")
            
            # Crear tabla face_auth_logs si no existe
            if "face_auth_logs" not in existing_tables:
                print("📝 Creando tabla face_auth_logs...")
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS face_auth_logs (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        id_usuario VARCHAR(50) NULL,
                        tabla_usuario ENUM('pacientes', 'medicos', 'laboratoristas', 'administradores') NULL,
                        exito BOOLEAN NOT NULL,
                        score_similitud FLOAT NULL,
                        umbral_utilizado FLOAT DEFAULT 0.6,
                        ip_address VARCHAR(45) NULL,
                        user_agent TEXT NULL,
                        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                        notas TEXT NULL,
                        INDEX idx_id_usuario (id_usuario),
                        INDEX idx_exito (exito),
                        INDEX idx_creado_en (creado_en)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                print("✅ Tabla face_auth_logs creada exitosamente")
            else:
                print("ℹ️  Tabla face_auth_logs ya existe")
            
            print("\n✅ Migración de autenticación facial completada exitosamente!")
            print("📊 Resumen:")
            print("   - Tabla face_embeddings: Almacena embeddings faciales de usuarios")
            print("   - Tabla face_auth_logs: Registra todos los intentos de autenticación")
            print("\n🔄 Los usuarios ahora pueden registrar su rostro para autenticación biométrica.")
            
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(migrate_face_auth())
    if not success:
        sys.exit(1)