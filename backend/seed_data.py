import asyncio
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Ajustar PYTHONPATH para poder importar app
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import Base
from app.utils import hash_password
from app.models import (
    AreaLaboratorio, Prueba, Paciente, Medico, Laboratorista, Administrador,
    Solicitud, DetalleSolicitud, Resultado, Factura, DetalleFactura, Pago
)

async def seed():
    print("Conectando a la base de datos para sembrar datos clínicos...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 1. Asegurar que las tablas existan (limpiando datos anteriores para evitar conflictos)
    async with engine.begin() as conn:
        print("Eliminando tablas anteriores si existen...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creando tablas limpias...")
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        # 2. Verificar si ya existen los datos para evitar duplicados
        stmt = select(Paciente).where(Paciente.email == "paciente@labotik.com")
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            print("Los datos de demostración ya existen en la base de datos. Saltando siembra.")
            await engine.dispose()
            return
            
        print("Sembrando departamentos clínicos (Áreas)...")
        # Áreas
        area_hem = AreaLaboratorio(id_area="HEM", nombre="Hematología", descripcion="Análisis de células sanguíneas y coagulación", activo=1)
        area_bio = AreaLaboratorio(id_area="BIO", nombre="Bioquímica Clínica", descripcion="Estudios de componentes químicos en fluidos biológicos", activo=1)
        db.add_all([area_hem, area_bio])
        await db.commit()
        
        print("Sembrando catálogo de pruebas...")
        # Pruebas
        p_hem = Prueba(id_prueba=1, id_area="HEM", nombre="Hemograma Completo", descripcion="Recuento de glóbulos rojos, blancos y plaquetas", valor_referencia="4.5 - 11.0", unidad="10^3/µL", precio=4500.0, tiempo_estimado_minutos=60, activo=1)
        p_lip = Prueba(id_prueba=2, id_area="BIO", nombre="Perfil Lipídico Completo", descripcion="Medición de colesterol total, HDL, LDL y triglicéridos", valor_referencia="< 200", unidad="mg/dL", precio=9900.0, tiempo_estimado_minutos=120, activo=1)
        p_glu = Prueba(id_prueba=3, id_area="BIO", nombre="Glucosa en Ayunas", descripcion="Nivel de azúcar en sangre después de ayuno", valor_referencia="70 - 100", unidad="mg/dL", precio=2500.0, tiempo_estimado_minutos=30, activo=1)
        p_pcr = Prueba(id_prueba=4, id_area="BIO", nombre="Proteína C Reactiva (PCR)", descripcion="Marcador de inflamación general en el organismo", valor_referencia="< 5.0", unidad="mg/L", precio=5500.0, tiempo_estimado_minutos=45, activo=1)
        db.add_all([p_hem, p_lip, p_glu, p_pcr])
        await db.commit()
        
        print("Sembrando perfiles de usuarios de prueba (Paciente, Médico, Laboratorista)...")
        # Usuarios (Paciente, Médico, Laboratorista)
        pass_hashed = hash_password("password")
        
        paciente = Paciente(
            id_paciente="P-JUAN123",
            nombre="Juan Carlos",
            apellido_paterno="Pérez",
            apellido_materno="Galdames",
            fecha_nacimiento=date(1990, 5, 15),
            genero="M",
            telefono="+56912345678",
            email="paciente@labotik.com",
            direccion="Av. Providencia 1245, Santiago",
            tipo_sangre="O+",
            alergias="Penicilina",
            password=pass_hashed,
            activo=1
        )
        
        medico = Medico(
            id_medico="M-ANDREA87",
            nombre="Andrea Belén",
            apellido_paterno="Mendoza",
            apellido_materno="Silva",
            fecha_nacimiento=date(1980, 11, 20),
            especialidad="Cardiología Clínica",
            telefono="+56987654321",
            email="medico@labotik.com",
            password=pass_hashed,
            activo=1
        )
        
        laboratorista = Laboratorista(
            id_laboratorista="L-CARLOS98",
            nombre="Carlos Esteban",
            apellido_paterno="Gómez",
            apellido_materno="Ríos",
            fecha_nacimiento=date(1988, 4, 12),
            email="laboratorista@labotik.com",
            password=pass_hashed,
            telefono="+56955544433",
            id_area="BIO",
            activo=1
        )
        
        superadmin = Administrador(
            id_admin="ADM-SUPER01",
            nombre="Super Administrador",
            apellido_paterno="Administrador",
            apellido_materno="Principal",
            fecha_nacimiento=date(1985, 1, 1),
            email="admin@labotik.com",
            password=pass_hashed,
            telefono="+56900000000",
            rol="super_admin",
            activo=1
        )
        
        db.add_all([paciente, medico, laboratorista, superadmin])
        await db.commit()
        
        print("Sembrando datos clínicos históricos (Solicitudes, Facturas y Resultados)...")
        
        # 1. Solicitud ya completada para demostración de informes de examen
        solicitud_completada = Solicitud(
            id_solicitud=101,
            fecha_solicitud=datetime(2026, 5, 14, 10, 30),
            fecha_toma_muestra=datetime(2026, 5, 14, 11, 0),
            id_paciente="P-JUAN123",
            id_medico="M-ANDREA87",
            id_laboratorista="L-CARLOS98",
            estado="completado",
            prioridad="media",
            observaciones="Paciente refiere fatiga inusual e inflamación en articulaciones.",
            estado_pago="pagado_total",
            fecha_inicio_procesamiento=datetime(2026, 5, 14, 12, 0),
            fecha_fin_procesamiento=datetime(2026, 5, 14, 14, 30),
            activo=1
        )
        db.add(solicitud_completada)
        await db.commit()
        
        # Detalles de la solicitud completada
        det_hem = DetalleSolicitud(id_detalle=201, id_solicitud=101, id_prueba=1, cantidad=1, activo=1)
        det_pcr = DetalleSolicitud(id_detalle=202, id_solicitud=101, id_prueba=4, cantidad=1, activo=1)
        db.add_all([det_hem, det_pcr])
        await db.commit()
        
        # Resultados asociados
        res_hem = Resultado(
            id_resultado=301,
            id_detalle=201,
            resultado="6.2",
            observacion="Recuento eritrocitario y leucocitario dentro de rangos normales de control.",
            validado_por="L-CARLOS98",
            fecha_validacion=datetime(2026, 5, 14, 14, 30),
            es_anormal=0,
            activo=1
        )
        res_pcr = Resultado(
            id_resultado=302,
            id_detalle=202,
            resultado="12.5",
            observacion="Nivel de PCR elevado. Sugiere proceso inflamatorio o infeccioso agudo.",
            validado_por="L-CARLOS98",
            fecha_validacion=datetime(2026, 5, 14, 14, 30),
            es_anormal=1, # Fuera de rango de referencia
            activo=1
        )
        db.add_all([res_hem, res_pcr])
        await db.commit()
        
        # Factura asociada
        factura = Factura(
            id_factura=401,
            id_solicitud=101,
            id_paciente="P-JUAN123",
            fecha_emision=datetime(2026, 5, 14, 10, 45),
            fecha_vencimiento=date(2026, 5, 24),
            subtotal=10000.0, # 4500 + 5500
            impuesto=1900.0,  # 19% IVA
            descuento=0.0,
            total=11900.0,
            estado_factura="pagada_total",
            tipo_comprobante="boleta",
            nro_comprobante="B-2026-0001",
            activo=1
        )
        db.add(factura)
        await db.commit()
        
        # Detalles de la factura
        det_fact_hem = DetalleFactura(id_detalle_factura=501, id_factura=401, id_prueba=1, id_detalle_solicitud=201, cantidad=1, precio_unitario=4500.0, descuento_item=0.0, total_item=4500.0, activo=1)
        det_fact_pcr = DetalleFactura(id_detalle_factura=502, id_factura=401, id_prueba=4, id_detalle_solicitud=202, cantidad=1, precio_unitario=5500.0, descuento_item=0.0, total_item=5500.0, activo=1)
        db.add_all([det_fact_hem, det_fact_pcr])
        await db.commit()
        
        # Pago asociado
        pago = Pago(
            id_pago=601,
            id_factura=401,
            monto=11900.0,
            fecha_pago=datetime(2026, 5, 14, 10, 48),
            metodo_pago="transferencia",
            referencia_pago="TX-99882233",
            estado_pago="completado",
            activo=1
        )
        db.add(pago)
        await db.commit()
        
        # 2. Solicitud PENDIENTE para demostración de procesamiento en laboratorista
        solicitud_pendiente = Solicitud(
            id_solicitud=102,
            fecha_solicitud=datetime(2026, 5, 16, 15, 0),
            id_paciente="P-JUAN123",
            id_medico="M-ANDREA87",
            estado="pendiente",
            prioridad="alta", # Prioridad alta para que resalte
            observaciones="Urgente. Sospecha de descompensación diabética.",
            estado_pago="no_pagado",
            activo=1
        )
        db.add(solicitud_pendiente)
        await db.commit()
        
        det_glu = DetalleSolicitud(id_detalle=203, id_solicitud=102, id_prueba=3, cantidad=1, activo=1)
        db.add(det_glu)
        await db.commit()
        
        print("¡Siembra de datos de demostración clínicos completada con éxito!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
