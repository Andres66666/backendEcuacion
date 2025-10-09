import os
import sendgrid
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@mallafinitasrl.com")

def enviar_correo_sendgrid(destinatario, asunto, contenido_html):
    """
    Envía un correo usando SendGrid API.
    """
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    mensaje = Mail(
        from_email=DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        html_content=contenido_html,
    )

    try:
        respuesta = sg.send(mensaje)
        print("✅ Correo enviado con código:", respuesta.status_code)
        return True
    except Exception as e:
        print("❌ Error al enviar correo:", str(e))
        return False
