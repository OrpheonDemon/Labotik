import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

def send_result_email(email_to: str, patient_name: str, patient_id: str, test_name: str, result_value: str, is_anormal: int, observations: str, solicitud_id: int):
    """
    Envía una notificación por correo electrónico real utilizando un servidor SMTP.
    Si no está configurado, realiza un fallback elegante imprimiendo la notificación
    con un formato premium en la consola de FastAPI.
    """
    subject = f"🔬 Resultados de Examen Disponibles: {test_name} (Orden #{solicitud_id}) - LaboTik"
    
    # Interpretación de anomalía
    interpretation = "🚨 RESULTADO ANORMAL - Requiere atención médica" if is_anormal else "✅ Dentro de rangos normales de referencia"
    obs_text = observations if observations else "Sin observaciones adicionales."
    
    # Cuerpo del correo HTML
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333333; background-color: #f4f6f9; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 1px solid #e1e8ed; }}
            .header {{ background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); color: #ffffff; padding: 25px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 30px; line-height: 1.6; }}
            .greeting {{ font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 0; }}
            .intro-text {{ margin-bottom: 20px; font-size: 15px; color: #475569; }}
            .summary-box {{ background-color: #f8fafc; border-left: 4px solid #4f46e5; border-radius: 4px; padding: 20px; margin-bottom: 25px; }}
            .summary-box.anormal {{ border-left-color: #ef4444; background-color: #fef2f2; }}
            .summary-title {{ font-weight: 700; font-size: 15px; color: #1e293b; margin-top: 0; margin-bottom: 12px; text-transform: uppercase; }}
            .summary-item {{ display: flex; margin-bottom: 8px; font-size: 14px; }}
            .summary-label {{ font-weight: 600; width: 140px; color: #64748b; flex-shrink: 0; }}
            .summary-value {{ color: #1e293b; }}
            .summary-value.anormal {{ color: #dc2626; font-weight: 700; }}
            .btn-wrapper {{ text-align: center; margin: 30px 0 10px 0; }}
            .btn-portal {{ background-color: #4f46e5; color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: 600; font-size: 14px; display: inline-block; transition: background-color 0.2s; }}
            .btn-portal:hover {{ background-color: #4338ca; }}
            .footer {{ background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
            .footer p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>LaboTik</h1>
                <p>Portal Clínico & Central de Diagnóstico</p>
            </div>
            <div class="content">
                <p class="greeting">Estimado(a) {patient_name},</p>
                <p class="intro-text">Le informamos que un nuevo resultado de su examen clínico ha sido ingresado y validado en nuestro sistema. Ya puede descargar su informe completo y certificado digital desde su portal web.</p>
                
                <div class="summary-box {'anormal' if is_anormal else ''}">
                    <p class="summary-title">Resumen del Informe</p>
                    <div class="summary-item">
                        <span class="summary-label">Examen:</span>
                        <span class="summary-value" style="font-weight: 600;">{test_name}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Resultado:</span>
                        <span class="summary-value {'anormal' if is_anormal else ''}">{result_value}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Interpretación:</span>
                        <span class="summary-value {'anormal' if is_anormal else ''}" style="font-weight: 600;">{interpretation}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Observaciones:</span>
                        <span class="summary-value">{obs_text}</span>
                    </div>
                </div>
                
                <div class="btn-wrapper">
                    <a href="http://127.0.0.1:8001/login/" class="btn-portal" target="_blank">Ingresar al Portal del Paciente</a>
                </div>
            </div>
            <div class="footer">
                <p>Este es un correo automático. Por favor no responda directamente a este mensaje.</p>
                <p>&copy; 2026 LaboTik S.A. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Verificar si el servidor SMTP está configurado en el archivo .env
    if settings.SMTP_HOST and settings.SMTP_USER:
        try:
            # Crear el objeto de correo
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM if settings.SMTP_FROM else settings.SMTP_USER
            msg['To'] = email_to
            
            # Adjuntar cuerpo HTML
            msg.attach(MIMEText(html_body, 'html'))
            
            # Conexión SMTP
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.ehlo()
            server.starttls()  # Conexión TLS segura
            server.ehlo()
            
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
            server.sendmail(msg['From'], email_to, msg.as_string())
            server.quit()
            print(f"\n[SMTP] ✅ ¡Correo electrónico real enviado exitosamente a {email_to}!")
            return True
        except Exception as e:
            print(f"\n[SMTP] ❌ Error al enviar correo real (re-intentando en modo Consola): {e}")
            # Si falla, hacemos fallback a la consola
    
    # Fallback elegante a la consola con formato Premium ASCII
    print("\n" + "="*80)
    print(" " * 20 + "📬 NUEVA NOTIFICACIÓN DE RESULTADOS - LABOTIK")
    print("="*80)
    print(f"| DE:      {settings.SMTP_FROM if settings.SMTP_FROM else 'noreply@labotik.com'}")
    print(f"| PARA:    {email_to}")
    print(f"| PACIENTE: {patient_name} (ID: {patient_id})")
    print(f"| ASUNTO:  {subject}")
    print("-"*80)
    print(f"| Estimado(a) {patient_name},")
    print("|")
    print(f"| Le informamos que los resultados del examen clínico '{test_name}'")
    print(f"| correspondientes a la orden #{solicitud_id} ya se encuentran disponibles.")
    print("|")
    print(f"| DETALLE DE RESULTADO:")
    print(f"| - Examen:         {test_name}")
    print(f"| - Resultado:      {result_value}")
    print(f"| - Diagnóstico:    {interpretation}")
    print(f"| - Observaciones:  {obs_text}")
    print("|")
    print("| Puede descargar su reporte oficial en: http://127.0.0.1:8001/dashboard/")
    print("="*80)
    print(" " * 25 + "✅ NOTIFICACIÓN IMPRESA EN CONSOLA")
    print("="*80 + "\n")
    return True
