from GuardianUnivalle_Benito_Yucra.auditoria.registro_auditoria import registrar_evento
from GuardianUnivalle_Benito_Yucra.auditoria.utils_auditoria import obtener_datos_maquina
from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante


class AuditoriaMiddleware:
    """
    Middleware de Auditoría Integral:
    - Registra todas las peticiones (ataques y normales)
    - Analiza y guarda la información de la máquina cliente
    - Actualiza el registro de atacantes si corresponde
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # =====================================================
        # === 1. Capturar datos de la máquina del cliente  ===
        # =====================================================
        datos_cliente = obtener_datos_maquina(request)

        # =====================================================
        # === 2. Verificar si algún detector marcó ataque  ===
        # =====================================================
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

        # =====================================================
        # === 3. Caso A: Ataque detectado                   ===
        # =====================================================
        if ataque_detectado:
            ip = ataque_detectado.get("ip", datos_cliente["ip"])
            tipos = ataque_detectado.get("tipos", [])
            descripcion = ataque_detectado.get("descripcion", [])
            payload = ataque_detectado.get("payload", "")

            tipos_str = ",".join(map(str, tipos)) if isinstance(tipos, (list, tuple)) else str(tipos)
            descripcion_str = "; ".join(map(str, descripcion)) if isinstance(descripcion, (list, tuple)) else str(descripcion)

            try:
                atacante_existente = Atacante.objects.filter(ip=ip).first()

                if atacante_existente:
                    # Si ya existe y está bloqueado, cortar respuesta
                    if atacante_existente.bloqueado:
                        return JsonResponse({"mensaje": "Acceso bloqueado"}, status=403)
                    else:
                        # Actualizar registro existente
                        atacante_existente.tipos = tipos_str
                        atacante_existente.descripcion = descripcion_str
                        atacante_existente.payload = (payload or "")[:2000]
                        atacante_existente.user_agent = datos_cliente["user_agent"]
                        atacante_existente.bloqueado = True
                        atacante_existente.fecha = now()
                        atacante_existente.url = datos_cliente["url"]
                        atacante_existente.save()
                else:
                    # Crear nuevo registro de atacante
                    Atacante.objects.create(
                        ip=ip,
                        tipos=tipos_str,
                        descripcion=descripcion_str,
                        payload=(payload or "")[:2000],
                        user_agent=datos_cliente["user_agent"],
                        bloqueado=True,
                        fecha=now(),
                        url=datos_cliente["url"],
                    )

                # Registrar en archivo de auditoría
                registrar_evento(
                    request,
                    tipo="ATAQUE DETECTADO",
                    extra={
                        "ip": ip,
                        "descripcion": descripcion_str,
                        "payload": payload,
                        "detalles_maquina": datos_cliente,
                    },
                )

            except Exception as e:
                print(f"[AuditoriaMiddleware] Error guardando ataque: {e}")

            return JsonResponse(
                {"mensaje": "Ataque detectado y bloqueado", "tipo": tipos_str},
                status=403,
            )

        # =====================================================
        # === 4. Caso B: No hay ataque → acceso normal      ===
        # =====================================================
        registrar_evento(
            request,
            tipo="ACCESO NORMAL",
            extra={"detalles_maquina": datos_cliente},
        )

        response = self.get_response(request)
        return response
