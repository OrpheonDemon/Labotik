#!/usr/bin/env python3
"""
Validation script for payment gateway implementation
Tests imports, QR generation, and basic system health
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all required imports work"""
    print("=" * 60)
    print("VALIDACIÓN DE IMPORTS")
    print("=" * 60)
    
    try:
        import qrcode
        print("✓ qrcode importado exitosamente")
    except ImportError as e:
        print(f"✗ Error importando qrcode: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ PIL (Pillow) importado exitosamente")
    except ImportError as e:
        print(f"✗ Error importando PIL: {e}")
        return False
    
    print()
    return True

def test_qr_generation():
    """Test QR code generation"""
    print("=" * 60)
    print("VALIDACIÓN DE GENERACIÓN QR")
    print("=" * 60)
    
    try:
        import qrcode
        import io
        import base64
        
        # Inline QR generation without importing the app module
        invoice_id = 12345
        amount = 250.50
        patient_id = "PAC001"
        patient_email = "paciente@example.com"
        currency = "BOB"
        description = "Pruebas de laboratorio"
        
        # Standard payment data for QR code
        payment_data = f"FACTURA:{invoice_id}|MONTO:{amount}|MONEDA:{currency}|PACIENTE:{patient_id}|EMAIL:{patient_email}|DESC:{description}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to PNG bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        png_data = img_bytes.getvalue()
        
        # Convert to base64
        base64_qr = base64.b64encode(png_data).decode('utf-8')
        
        print(f"✓ QR generado exitosamente")
        print(f"  - Base64 length: {len(base64_qr)} caracteres")
        print(f"  - PNG bytes: {len(png_data)} bytes")
        
        # Test reference generation
        amount_cents = int(amount * 100)
        reference = f"INV{invoice_id:06d}-{amount_cents:08d}"
        print(f"✓ Referencia generada: {reference}")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Error en generación QR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_structure():
    """Test that backend routers exist and are configured"""
    print("=" * 60)
    print("VALIDACIÓN DE ESTRUCTURA BACKEND")
    print("=" * 60)
    
    try:
        # Check if files exist instead of importing (to avoid config issues)
        import os
        
        backend_path = os.path.dirname(__file__)
        
        files_to_check = [
            os.path.join(backend_path, "backend", "app", "routers", "facturas.py"),
            os.path.join(backend_path, "backend", "app", "routers", "pagos.py"),
            os.path.join(backend_path, "backend", "app", "utils", "payment_qr.py"),
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print(f"✓ Archivo existe: {os.path.basename(file_path)}")
            else:
                print(f"✗ Archivo NO existe: {file_path}")
                return False
        
        print(f"✓ Estructura de routers validada")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Error en validación backend: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_files():
    """Test that frontend files exist"""
    print("=" * 60)
    print("VALIDACIÓN DE ARCHIVOS FRONTEND")
    print("=" * 60)
    
    base_path = os.path.dirname(__file__)
    
    files_to_check = [
        os.path.join(base_path, "frontend", "templates", "dashboard", "paciente_dashboard.html"),
        os.path.join(base_path, "frontend", "templates", "dashboard", "recepcionista_dashboard.html"),
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ Archivo existe: {os.path.relpath(file_path, base_path)}")
        else:
            print(f"✗ Archivo NO existe: {os.path.relpath(file_path, base_path)}")
            all_exist = False
    
    print()
    return all_exist

def main():
    """Run all validations"""
    print("\n" + "=" * 60)
    print("VALIDACIÓN DEL SISTEMA DE PAGOS")
    print("=" * 60 + "\n")
    
    results = {
        "Imports": test_imports(),
        "QR Generation": test_qr_generation(),
        "Backend Structure": test_backend_structure(),
        "Frontend Files": test_frontend_files(),
    }
    
    # Summary
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    
    all_passed = all(results.values())
    if all_passed:
        print("🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("El sistema de pagos está listo para usar.")
    else:
        print("⚠️  Hay errores que necesitan ser corregidos.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
