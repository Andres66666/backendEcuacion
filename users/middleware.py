import json
import logging
from django.http import JsonResponse
from django.utils.timezone import now
from django.utils.deprecation import MiddlewareMixin
from users.models import Atacante
from GuardianUnivalle_Benito_Yucra.auditoria.registro_auditoria import registrar_evento

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

                blocked = bool(info.get("blocked", False))
                score = info.get("score", 0) or 0
                try:
                    score = float(score)
                except Exception:
                    score = 0.0

                hallazgos.append((blocked, score, info))

        if not hallazgos:
            return None

        hallazgos.sort(key=lambda x: (x[0], x[1]), reverse=True)
        blocked, score, ataque_detectado = hallazgos[0]

        if not blocked:
            return None

        ip = ataque_detectado.get("ip") or request.META.get("REMOTE_ADDR", "0.0.0.0")
        fingerprint = ataque_detectado.get("fingerprint", "")
        tipos = ataque_detectado.get("tipos", [])
        descripcion = ataque_detectado.get("descripcion", [])
        payload = ataque_detectado.get("payload", "")
        url = ataque_detectado.get("url", "")

        if isinstance(tipos, (list, tuple)):
            tipos_str = ",".join(map(str, tipos))
        else:
            tipos_str = str(tipos or "")

        if isinstance(descripcion, (list, tuple)):
            descripcion_str = "; ".join(map(str, descripcion))
        else:
            descripcion_str = str(descripcion or "")

        atacante_existente = None
        if fingerprint:
            atacante_existente = Atacante.objects.filter(fingerprint=fingerprint).first()
        if not atacante_existente:
            atacante_existente = Atacante.objects.filter(ip=ip).first()

        if atacante_existente:
            atacante_existente.ip = ip
            atacante_existente.fingerprint = fingerprint or atacante_existente.fingerprint
            atacante_existente.tipos = tipos_str
            atacante_existente.descripcion = descripcion_str
            atacante_existente.payload = (payload or "")[:2000]
            atacante_existente.user_agent = request.META.get("HTTP_USER_AGENT", "")
            atacante_existente.bloqueado = True
            atacante_existente.url = url or atacante_existente.url
            atacante_existente.fecha = now()
            atacante_existente.save()
            logger.warning(f"[AuditoriaMiddleware] Bloqueo actualizado Fingerprint={fingerprint} IP={ip} Tipos={tipos_str}")
        else:
            Atacante.objects.create(
                ip=ip,
                fingerprint=fingerprint,
                tipos=tipos_str,
                descripcion=descripcion_str,
                payload=(payload or "")[:2000],
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                bloqueado=True,
                fecha=now(),
                url=url,
            )
            logger.warning(f"[AuditoriaMiddleware] Bloqueo creado Fingerprint={fingerprint} IP={ip} Tipos={tipos_str}")

        registrar_evento(
            tipo="Bloqueo",
            descripcion=f"Ataque {tipos_str} bloqueado desde Fingerprint={fingerprint} IP={ip}",
            severidad="ALTA",
            extra={"descripcion": descripcion_str, "payload": payload},
        )

        if hasattr(request, "sql_block") and request.sql_block:
            return request.sql_block_response
        if hasattr(request, "sql_challenge") and request.sql_challenge:
            return request.sql_challenge_response
        if hasattr(request, "xss_block") and request.xss_block:
            return request.xss_block_response
        if hasattr(request, "csrf_block") and request.csrf_block:
            return request.csrf_block_response
        if hasattr(request, "dos_block") and request.dos_block:
            return request.dos_block_response

        return JsonResponse({"mensaje": "Ataque bloqueado", "tipo": tipos_str}, status=403)