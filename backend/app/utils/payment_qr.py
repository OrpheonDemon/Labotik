import qrcode
import io
import base64
from typing import Optional


def generate_payment_qr(
    invoice_id: int,
    amount: float,
    patient_id: str,
    patient_email: str,
    currency: str = "BOB",
    description: str = "Pago de consultas - Laboratorio Clínico"
) -> tuple[str, bytes]:
    """
    Generates a QR code for payment processing.
    
    Returns:
        tuple: (base64_string, png_bytes)
    """
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
    
    return base64_qr, png_data


def generate_qr_reference(invoice_id: int, amount: float) -> str:
    """Generate a unique reference code for payment."""
    import hashlib
    ref_string = f"INV{invoice_id:06d}-{int(amount*100):08d}"
    return ref_string
