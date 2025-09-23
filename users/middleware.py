from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 🔹 Revisar si SQLIDefenseMiddleware marcó un ataque
        if hasattr(request, "sql_attack_info"):
            ataque = request.sql_attack_info
            ip = ataque.get("ip", "desconocida")

            try:
                # Buscar registro existente del atacante
                atacante = Atacante.objects.filter(ip=ip).first()

                if atacante:
                    # Si ya estaba bloqueado, retornar 403
                    if atacante.bloqueado:
                        return JsonResponse({"mensaje": "Acceso bloqueado"}, status=403)

                    # Actualizar información del ataque
                    atacante.tipos = ",".join(ataque.get("tipos", []))
                    atacante.descripcion = "; ".join(ataque.get("descripcion", []))
                    atacante.payload = ataque.get("payload", "")
                    atacante.user_agent = request.META.get("HTTP_USER_AGENT", "")
                    atacante.bloqueado = True
                    atacante.fecha = now()
                    atacante.save()
                    print(
                        f"[AuditoriaMiddleware] Ataque actualizado y bloqueado para IP {ip}"
                    )

                else:
                    # Crear un nuevo registro para la IP atacante
                    Atacante.objects.create(
                        ip=ip,
                        tipos=",".join(ataque.get("tipos", [])),
                        descripcion="; ".join(ataque.get("descripcion", [])),
                        payload=ataque.get("payload", ""),
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                        bloqueado=True,
                        fecha=now(),
                    )
                    print(
                        f"[AuditoriaMiddleware] Ataque registrado y bloqueado desde {ip}"
                    )

            except Exception as e:
                print(f"[AuditoriaMiddleware] Error guardando ataque: {e}")

            # 🔹 Retornar 403 siempre que se detecte un ataque
            return JsonResponse({"mensaje": "Ataque detectado"}, status=403)

        # 🔹 Si no hay ataque, continuar normalmente
        return self.get_response(request)
