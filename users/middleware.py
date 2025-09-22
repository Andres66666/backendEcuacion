from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Excepciones de frontend
        trusted_origins = ["https://mallafinita.netlify.app"]
        trusted_ips = ["127.0.0.1", "192.168.0.4"]

        # Si viene marcado un ataque desde SQLIDefenseMiddleware
        if hasattr(request, "sql_attack_info"):
            # Ignorar si es frontend confiable o IP de confianza
            origen = request.META.get("HTTP_ORIGIN", "").lower()
            ip = request.META.get("REMOTE_ADDR")

            if origen in trusted_origins or ip in trusted_ips:
                return self.get_response(request)

            ataque = request.sql_attack_info
            ip = ataque["ip"]

            try:
                # Buscar si ya existe la IP en la base de datos
                atacante_existente = Atacante.objects.filter(ip=ip).first()

                if atacante_existente:
                    if atacante_existente.bloqueado:
                        return JsonResponse({"mensaje": "Acceso bloqueado"}, status=403)
                    else:
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
        return self.get_response(request)
