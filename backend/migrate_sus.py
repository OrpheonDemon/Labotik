

"""
Migración: Agregar soporte para pacientes SUS (Sistema Único de Salud) vs Privados
Base de datos: MySQL
Ejecutar: cd backend && python migrate_sus.py
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Conexión a MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rfcm1123581321',
    'database': 'laboratorio',
    'port': 3306,
    'charset': 'utf8mb4'
}

def migrate():
    print("=" * 60)
    print("  MIGRACIÓN: Soporte SUS vs Privado en Labotik")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Conectado a MySQL exitosamente")
    except Exception as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return
    
    # ============================================
    # 1. Migrar tabla PACIENTES
    # ============================================
    print("\n📋 Migrando tabla 'pacientes'...")
    
    # Verificar si ya existe la columna tipo_afiliacion
    cursor.execute("SHOW COLUMNS FROM pacientes LIKE 'tipo_afiliacion'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'tipo_afiliacion'...")
        cursor.execute("ALTER TABLE pacientes ADD COLUMN tipo_afiliacion ENUM('SUS','Privado') DEFAULT 'Privado'")
        print("   ✅ Columna 'tipo_afiliacion' agregada (valores: 'SUS', 'Privado')")
    else:
        print("   ⏭️  Columna 'tipo_afiliacion' ya existe")
    
    cursor.execute("SHOW COLUMNS FROM pacientes LIKE 'numero_afiliado_sus'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'numero_afiliado_sus'...")
        cursor.execute("ALTER TABLE pacientes ADD COLUMN numero_afiliado_sus VARCHAR(50)")
        print("   ✅ Columna 'numero_afiliado_sus' agregada")
    else:
        print("   ⏭️  Columna 'numero_afiliado_sus' ya existe")
    
    cursor.execute("SHOW COLUMNS FROM pacientes LIKE 'entidad_aseguradora'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'entidad_aseguradora'...")
        cursor.execute("ALTER TABLE pacientes ADD COLUMN entidad_aseguradora VARCHAR(100)")
        print("   ✅ Columna 'entidad_aseguradora' agregada")
    else:
        print("   ⏭️  Columna 'entidad_aseguradora' ya existe")
    
    # ============================================
    # 2. Migrar tabla FACTURAS
    # ============================================
    print("\n📋 Migrando tabla 'facturas'...")
    
    cursor.execute("SHOW COLUMNS FROM facturas LIKE 'tipo_pago_fuente'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'tipo_pago_fuente'...")
        cursor.execute("ALTER TABLE facturas ADD COLUMN tipo_pago_fuente ENUM('paciente','SUS','ministerio_salud') DEFAULT 'paciente'")
        print("   ✅ Columna 'tipo_pago_fuente' agregada")
    else:
        print("   ⏭️  Columna 'tipo_pago_fuente' ya existe")
    
    cursor.execute("SHOW COLUMNS FROM facturas LIKE 'monto_paciente'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'monto_paciente'...")
        cursor.execute("ALTER TABLE facturas ADD COLUMN monto_paciente FLOAT DEFAULT 0.0")
        print("   ✅ Columna 'monto_paciente' agregada")
    else:
        print("   ⏭️  Columna 'monto_paciente' ya existe")
    
    cursor.execute("SHOW COLUMNS FROM facturas LIKE 'monto_sus'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'monto_sus'...")
        cursor.execute("ALTER TABLE facturas ADD COLUMN monto_sus FLOAT DEFAULT 0.0")
        print("   ✅ Columna 'monto_sus' agregada")
    else:
        print("   ⏭️  Columna 'monto_sus' ya existe")
    
    cursor.execute("SHOW COLUMNS FROM facturas LIKE 'estado_reembolso_sus'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'estado_reembolso_sus'...")
        cursor.execute("ALTER TABLE facturas ADD COLUMN estado_reembolso_sus ENUM('no_aplica','pendiente','enviado','reembolsado') DEFAULT 'no_aplica'")
        print("   ✅ Columna 'estado_reembolso_sus' agregada")
    else:
        print("   ⏭️  Columna 'estado_reembolso_sus' ya existe")
    
    cursor.execute("SHOW COLUMNS FROM facturas LIKE 'numero_reclamacion_sus'")
    if cursor.fetchone() is None:
        print("   ✅ Agregando columna 'numero_reclamacion_sus'...")
        cursor.execute("ALTER TABLE facturas ADD COLUMN numero_reclamacion_sus VARCHAR(50)")
        print("   ✅ Columna 'numero_reclamacion_sus' agregada")
    else:
        print("   ⏭️  Columna 'numero_reclamacion_sus' ya existe")
    
    conn.commit()
    
    # ============================================
    # 3. Verificar resultados
    # ============================================
    print("\n📊 Verificación de la migración:")
    
    cursor.execute("SELECT COUNT(*) FROM pacientes WHERE tipo_afiliacion = 'SUS'")
    sus_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pacientes WHERE tipo_afiliacion = 'Privado'")
    priv_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM facturas WHERE tipo_pago_fuente = 'SUS'")
    fac_sus = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM facturas WHERE tipo_pago_fuente = 'paciente'")
    fac_pac = cursor.fetchone()[0]
    
    print(f"   Pacientes SUS: {sus_count}")
    print(f"   Pacientes Privados: {priv_count}")
    print(f"   Facturas al SUS: {fac_sus}")
    print(f"   Facturas a pacientes: {fac_pac}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("  ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\nNuevos campos en 'pacientes':")
    print("  - tipo_afiliacion: 'SUS' o 'Privado' (default: 'Privado')")
    print("  - numero_afiliado_sus: Número de afiliación al SUS")
    print("  - entidad_aseguradora: Entidad aseguradora (privados)")
    print("\nNuevos campos en 'facturas':")
    print("  - tipo_pago_fuente: 'paciente', 'SUS', 'ministerio_salud'")
    print("  - monto_paciente: Monto que paga el paciente")
    print("  - monto_sus: Monto que cubre el SUS")
    print("  - estado_reembolso_sus: Estado del reembolso del SUS")
    print("  - numero_reclamacion_sus: Número de reclamación")


if __name__ == "__main__":
    migrate()