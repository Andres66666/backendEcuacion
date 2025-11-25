# E:\EcuacionPotosi\backendEcuacion\users\middleware.py
import base64
from functools import cache  # Nota: 'cache' es de functools, pero no se usa aquí; puedes quitarlo si no lo necesitas
import json
import time
from GuardianUnivalle_Benito_Yucra.detectores.detector_csrf import encrypt_csrf_token, decrypt_csrf_token  # Importa solo lo que usas en test_crypto
from GuardianUnivalle_Benito_Yucra.auditoria.registro_auditoria import registrar_evento
from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante
from django.utils.deprecation import MiddlewareMixin
import logging
logger = logging.getLogger(__name__)

class AuditoriaMiddleware(MiddlewareMixin):
    def process_request(self, request):
        detectores = [
            "sql_attack_info",
            "xss_attack_info",
            "csrf_attack_info",
            "dos_attack_info",
        ]
        hallazgos = []
        for attr in detectores:
            if hasattr(request, attr):
                info = getattr(request, attr)
                if not isinstance(info, dict):
                    continue
                score = info.get("score", 0) or 0
                try:
                    score = float(score)
                except Exception:
                    score = 0.0
                hallazgos.append((score, info))
        ataque_detectado = None
        if hallazgos:
            hallazgos.sort(key=lambda x: x[0], reverse=True)
            ataque_detectado = hallazgos[0][1]

        if ataque_detectado:
            ip = ataque_detectado.get("ip", request.META.get("REMOTE_ADDR", "0.0.0.0"))
            tipos = ataque_detectado.get("tipos", [])
            descripcion = ataque_detectado.get("descripcion", [])
            payload = ataque_detectado.get("payload", "")
            if isinstance(tipos, (list, tuple)):
                tipos_str = ",".join(map(str, tipos))
            else:
                tipos_str = str(tipos or "")
            if isinstance(descripcion, (list, tuple)):
                descripcion_str = "; ".join(map(str, descripcion))
            else:
                descripcion_str = str(descripcion or "")
            try:
                atacante_existente = Atacante.objects.filter(ip=ip).first()
                if atacante_existente:
                    # Siempre actualizar el registro con nueva info del ataque y setear bloqueado=True
                    # Esto maneja reataques después de desbloqueo (cache expirado o manual)
                    atacante_existente.tipos = tipos_str
                    atacante_existente.descripcion = descripcion_str
                    atacante_existente.payload = (payload or "")[:2000]
                    atacante_existente.user_agent = request.META.get("HTTP_USER_AGENT", "")
                    atacante_existente.bloqueado = True  # Siempre bloquear en reataques
                    atacante_existente.url = ataque_detectado.get("url", atacante_existente.url)
                    atacante_existente.fecha = now()
                    atacante_existente.save()
                    # Nuevo: mensaje de logging para reataque
                    logger.warning(f"[AuditoriaMiddleware] Reataque detectado y bloqueado nuevamente para IP {ip} (tipo: {tipos_str}) - Registro actualizado en DB")
                else:
                    Atacante.objects.create(
                        ip=ip,
                        tipos=tipos_str,
                        descripcion=descripcion_str,
                        payload=(payload or "")[:2000],
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                        bloqueado=True,
                        fecha=now(),
                        url=ataque_detectado.get("url", ""),
                    )
                    # Nuevo: mensaje de logging para creación
                    logger.info(f"[AuditoriaMiddleware] Ataque registrado y bloqueado desde IP {ip} (tipo: {tipos_str}) - Datos guardados en DB")
                registrar_evento(
                    tipo="Bloqueo",
                    descripcion=f"Ataque {tipos_str} bloqueado desde IP {ip}",
                    severidad="ALTA",
                    extra={"descripcion": descripcion_str, "payload": payload},
                )
            except Exception as e:
                # Nuevo: mensaje de logging para error
                logger.error(f"[AuditoriaMiddleware] Error guardando ataque en DB: {e}")
                return JsonResponse({"mensaje": "Error interno al procesar ataque"}, status=500)
            # Nuevo: manejo de flags de bloqueo después de guardar
            if hasattr(request, 'sql_block') and request.sql_block:
                # Nuevo: mensaje de logging para bloqueo
                logger.warning(f"[AuditoriaMiddleware] Bloqueando solicitud para IP {ip} después de guardar en DB")
                return request.sql_block_response
            if hasattr(request, 'sql_challenge') and request.sql_challenge:
                # Nuevo: mensaje de logging para challenge
                logger.info(f"[AuditoriaMiddleware] Enviando challenge para IP {ip}")
                return request.sql_challenge_response
            if hasattr(request, 'xss_block') and request.xss_block:
                logger.warning(f"[AuditoriaMiddleware] Bloqueando solicitud para IP {ip} con mensaje del detector")
                return request.xss_block_response
            # Si no hay bloqueo, retorna JsonResponse como antes
            return JsonResponse({"mensaje": "Ataque detectado", "tipo": tipos_str}, status=403)
        # No se detectó ataque → continuar normal
        return None

    def test_crypto(self, request):  # Nueva función para probar cifrado/descifrado
        try:
            token = "test_token_csrf"
            logger.info(f"[AuditoriaMiddleware:Crypto] Iniciando prueba de cifrado/descifrado con token: {token}")
            encrypted = encrypt_csrf_token(token)
            logger.info(f"[AuditoriaMiddleware:Crypto] CIFRADO EXITOSO: Token cifrado (len={len(encrypted)})")
            decrypted = decrypt_csrf_token(encrypted)
            if decrypted == token:
                logger.info(f"[AuditoriaMiddleware:Crypto] DESCIFRADO EXITOSO: Token descifrado correctamente ({decrypted})")
                return JsonResponse({"mensaje": "Cifrado y descifrado exitosos", "original": token, "encrypted": encrypted, "decrypted": decrypted})
            else:
                logger.error(f"[AuditoriaMiddleware:Crypto] DESCIFRADO FALLÓ: Token no coincide (esperado: {token}, obtenido: {decrypted})")
                return JsonResponse({"mensaje": "Descifrado falló", "original": token, "encrypted": encrypted, "decrypted": decrypted}, status=500)
        except Exception as e:
            logger.error(f"[AuditoriaMiddleware:Crypto] Error en prueba de cifrado/descifrado: {e}")
            return JsonResponse({"mensaje": "Error en cifrado/descifrado", "error": str(e)}, status=500)
