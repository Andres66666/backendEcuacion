from GuardianUnivalle_Benito_Yucra.auditoria.registro_auditoria import registrar_evento
from GuardianUnivalle_Benito_Yucra.auditoria.utils_auditoria import obtener_datos_maquina
from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante

class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- Obtener datos de la máquina cliente ---
        datos_cliente = obtener_datos_maquina(request)

        # --- Detección de ataques existentes ---
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
                if isinstance(info, dict):
                    score = float(info.get("score", 0) or 0)
                    hallazgos.append((score, info))

        ataque_detectado = None
        if hallazgos:
            hallazgos.sort(key=lambda x: x[0], reverse=True)
            ataque_detectado = hallazgos[0][1]

        # --- Si se detectó ataque ---
        if ataque_detectado:
            ip = ataque_detectado.get("ip", datos_cliente["ip"])
            tipos = ataque_detectado.get("tipos", [])
            descripcion = ataque_detectado.get("descripcion", [])
            payload = ataque_detectado.get("payload", "")

            tipos_str = ",".join(map(str, tipos)) if isinstance(tipos, (list, tuple)) else str(tipos)
            descripcion_str = "; ".join(map(str, descripcion)) if isinstance(descripcion, (list, tuple)) else str(descripcion)

            try:
                atacante = Atacante.objects.filter(ip=ip).first()
                if atacante:
                    atacante.tipos = tipos_str
                    atacante.descripcion = descripcion_str
                    atacante.payload = payload[:2000]
                    atacante.user_agent = datos_cliente["user_agent"]
                    atacante.bloqueado = True
                    atacante.fecha = now()
                    atacante.save()
                else:
                    Atacante.objects.create(
                        ip=ip,
                        tipos=tipos_str,
                        descripcion=descripcion_str,
                        payload=payload[:2000],
                        user_agent=datos_cliente["user_agent"],
                        bloqueado=True,
                        fecha=now(),
                        url=datos_cliente["url"],
                    )

                registrar_evento(
                    tipo="Ataque detectado",
                    descripcion=f"Ataque {tipos_str} desde IP {ip}",
                    severidad="ALTA",
                    extra={**datos_cliente, "descripcion": descripcion_str, "payload": payload},
                )

            except Exception as e:
                print(f"[AuditoriaMiddleware] Error guardando ataque: {e}")

            return JsonResponse({"mensaje": "Ataque detectado", "tipo": tipos_str}, status=403)

        # --- Si no hay ataque: registrar acceso normal ---
        registrar_evento(
            tipo="Acceso normal",
            descripcion=f"Acceso legítimo desde {datos_cliente['ip']} ({datos_cliente['navegador']})",
            severidad="BAJA",
            extra=datos_cliente,
        )

        return self.get_response(request)
