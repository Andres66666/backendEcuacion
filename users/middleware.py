from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si viene marcado un ataque desde SQLIDefenseMiddleware
        if hasattr(request, "sql_attack_info"):
            ataque = request.sql_attack_info
            ip = ataque["ip"]

            try:
                # Buscar si ya existe la IP en la base de datos
                atacante_existente = Atacante.objects.filter(ip=ip).first()

                if atacante_existente:
                    if atacante_existente.bloqueado:
                        # Si ya estaba bloqueado, no permite nada
                        return JsonResponse({"mensaje": "Acceso bloqueado"}, status=403)
                    else:
                        # Si existe pero no estaba bloqueado, actualizar información
                        atacante_existente.tipos = ",".join(ataque["tipos"])
                        atacante_existente.descripcion = "; ".join(
                            ataque.get("descripcion", [])
                        )
                        atacante_existente.payload = ataque["payload"]
                        atacante_existente.user_agent = request.META.get(
                            "HTTP_USER_AGENT", ""
                        )
                        atacante_existente.bloqueado = True
                        atacante_existente.fecha = now()
                        atacante_existente.save()
                        print(
                            f"[AuditoriaMiddleware] Ataque actualizado y bloqueado para IP {ip}"
                        )
                else:
                    # No existe, crear nuevo registro y bloquear
                    Atacante.objects.create(
                        ip=ip,
                        tipos=",".join(ataque["tipos"]),
                        descripcion="; ".join(ataque.get("descripcion", [])),
                        payload=ataque["payload"],
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                        bloqueado=True,
                        fecha=now(),
                    )
                    print(
                        f"[AuditoriaMiddleware] Ataque registrado y bloqueado desde {ip}"
                    )

            except Exception as e:
                print(f"[AuditoriaMiddleware] Error guardando ataque: {e}")

            return JsonResponse({"mensaje": "Ataque detectado"}, status=403)

        # Si no hay ataque → continuar normal
        response = self.get_response(request)
        return response
