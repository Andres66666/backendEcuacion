from GuardianUnivalle_Benito_Yucra.auditoria.registro_auditoria import registrar_evento

from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        detectores = [
            "sql_attack_info",
            "xss_attack_info",
            "csrf_attack_info",
            "dos_attack_info",
            "keylogger_attack_info",
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

            # users/middleware.py (fragmento de la sección donde guardas el atacante)
            try:
                atacante_existente = Atacante.objects.filter(ip=ip).first()

                if atacante_existente:
                    if atacante_existente.bloqueado:
                        return JsonResponse({"mensaje": "Acceso bloqueado"}, status=403)
                    else:
                        atacante_existente.tipos = tipos_str
                        atacante_existente.descripcion = descripcion_str
                        atacante_existente.payload = (payload or "")[:2000]  # truncar si es muy grande
                        atacante_existente.user_agent = request.META.get("HTTP_USER_AGENT", "")
                        atacante_existente.bloqueado = True
                        # actualizar url si viene
                        atacante_existente.url = ataque_detectado.get("url", atacante_existente.url)
                        atacante_existente.fecha = now()
                        atacante_existente.save()
                        print(f"[AuditoriaMiddleware] Ataque actualizado y bloqueado para IP {ip} (tipo: {tipos_str})")
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
                    print(f"[AuditoriaMiddleware] Ataque registrado y bloqueado desde IP {ip} (tipo: {tipos_str})")

                # ✅ Registrar el evento en el log de auditoría
                registrar_evento(
                    tipo="Bloqueo",
                    descripcion=f"Ataque {tipos_str} bloqueado desde IP {ip}",
                    severidad="ALTA",
                    extra={"descripcion": descripcion_str, "payload": payload},
                )

            except Exception as e:
                print(f"[AuditoriaMiddleware] Error guardando ataque: {e}")

            return JsonResponse(
                {"mensaje": "Ataque detectado", "tipo": tipos_str}, status=403
            )

        # No se detectó ataque → continuar normal 
        response = self.get_response(request)
        return response
# aqui se realiza cambios nuevos