from django.http import JsonResponse
from django.utils.timezone import now
from users.models import Atacante


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trusted_origins = ["https://mallafinita.netlify.app"]
        trusted_ips = ["127.0.0.1", "192.168.0.4"]

        ataque = getattr(request, "sql_attack_info", None)
        if ataque and "ip" in ataque:
            origen = request.META.get("HTTP_ORIGIN", "").lower()
            ip = request.META.get("REMOTE_ADDR")

            if origen in trusted_origins or ip in trusted_ips:
                return self.get_response(request)

            try:
                atacante_existente = Atacante.objects.filter(ip=ataque["ip"]).first()

                tipos = ",".join(ataque.get("tipos", []))
                descripcion = "; ".join(ataque.get("descripcion", []))
                payload = ataque.get("payload", "")
                user_agent = request.META.get("HTTP_USER_AGENT", "")

                if atacante_existente:
                    atacante_existente.tipos = tipos
                    atacante_existente.descripcion = descripcion
                    atacante_existente.payload = payload
                    atacante_existente.user_agent = user_agent
                    atacante_existente.bloqueado = True
                    atacante_existente.fecha = now()
                    atacante_existente.save()
                    print(
                        f"[AuditoriaMiddleware] Ataque actualizado y bloqueado para IP {ip}"
                    )
                else:
                    Atacante.objects.create(
                        ip=ataque["ip"],
                        tipos=tipos,
                        descripcion=descripcion,
                        payload=payload,
                        user_agent=user_agent,
                        bloqueado=True,
                        fecha=now(),
                    )
                    print(
                        f"[AuditoriaMiddleware] Ataque registrado y bloqueado desde {ip}"
                    )

            except Exception as e:
                print(f"[AuditoriaMiddleware] Error guardando ataque: {e}")

            return JsonResponse({"mensaje": "Ataque detectado"}, status=403)

        return self.get_response(request)
