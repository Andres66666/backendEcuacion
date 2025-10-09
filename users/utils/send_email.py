import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

def enviar_correo_sendgrid(destinatario, asunto, contenido_html):
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    mensaje = Mail(
        from_email=DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        html_content=contenido_html,
    )
    try:
        respuesta = sg.send(mensaje)
        print("✅ Correo enviado, status code:", respuesta.status_code)
        return True
    except Exception as e:
        print("❌ Error al enviar correo:", str(e))
        return False
