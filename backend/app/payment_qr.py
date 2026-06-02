"""
Utilidad de pago: generación de QR y referencias
"""
import qrcode
import qrcode.constants
import io
import base64


def generate_payment_qr(
    invoice_id: int,
    amount: float,
    patient_id: str,
    patient_email: str = "no@especificado.com",
    currency: str = "BOB",
    description: str = "Pago de factura"
):
    """
    Genera QR con datos de pago en texto plano.
    Retorna: (base64_qr, png_bytes)
    """
    payment_data = (
        f"FACTURA:{invoice_id}|"
        f"MONTO:{amount:.2f}|"
        f"MONEDA:{currency}|"
        f"PACIENTE:{patient_id}|"
        f"EMAIL:{patient_email}|"
        f"DESC:{description}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payment_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    png_data = img_bytes.getvalue()
    base64_qr = base64.b64encode(png_data).decode('utf-8')

    return base64_qr, png_data


def generate_qr_reference(invoice_id: int, amount: float) -> str:
    """
    Genera referencia única para el pago.
    Formato: INV{id:06d}-{centavos:08d}
    Ejemplo: INV000123-00025050  (factura #123, Bs 250.50)
    """
    return f"INV{invoice_id:06d}-{int(amount * 100):08d}"