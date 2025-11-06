from django.core.management.base import BaseCommand
from users.models import Atacante
from datetime import datetime

class Command(BaseCommand):
    help = "Inicializa la base de datos con registros de atacantes de prueba"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Inicializando registros de atacantes...")


        atacantes_data = [
            # --- SQLi ---
            {
                "ip": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "payload": "SELECT * FROM users WHERE id=1 UNION SELECT password FROM admin",
                "tipos": "SQLi",
                "descripcion": "UNION SELECT (exfiltración)",
                "fecha": datetime(2020,1,15,10,30),
                "bloqueado": False,
                "url": "http://example.com/login"
            },
            {
                "ip": "192.168.1.6",
                "user_agent": "Mozilla/5.0 (Android 11; Mobile)...",
                "payload": "1; DROP TABLE users--",
                "tipos": "SQLi",
                "descripcion": "Stacked queries (uso de ; para apilar)",
                "fecha": datetime(2020,6,18,13,30),
                "bloqueado": True,
                "url": "http://example.com/auth"
            },
            {
                "ip": "192.168.1.11",
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X)...",
                "payload": "SELECT * FROM information_schema.tables",
                "tipos": "SQLi",
                "descripcion": "INFORMATION_SCHEMA (recon meta-datos)",
                "fecha": datetime(2020,11,8,10,20),
                "bloqueado": False,
                "url": "http://example.com/delay"
            },
            {
                "ip": "192.168.1.16",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "payload": "BENCHMARK(1000000,MD5(1))",
                "tipos": "SQLi",
                "descripcion": "BENCHMARK() MySQL (time/DoS)",
                "fecha": datetime(2021,4,10,13,25),
                "bloqueado": True,
                "url": "http://example.com/concat"
            },
            {
                "ip": "192.168.1.26",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1)...",
                "payload": "OR 1=1",
                "tipos": "SQLi",
                "descripcion": "Tautología OR/AND x=x o 1=1",
                "fecha": datetime(2022,2,8,13,15),
                "bloqueado": True,
                "url": "http://example.com/bulk"
            },

            # --- CSRF ---
            {
                "ip": "192.168.1.2",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
                "payload": "Falta token CSRF en cookie/header/form",
                "tipos": "CSRF",
                "descripcion": "Falta token CSRF en cookie/header/form",
                "fecha": datetime(2020,2,20,14,45),
                "bloqueado": True,
                "url": "http://example.com/admin"
            },
            {
                "ip": "192.168.1.7",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "payload": "Origin/Referer no coinciden con Host",
                "tipos": "CSRF",
                "descripcion": "Origin/Referer no coinciden con Host (posible cross-site)",
                "fecha": datetime(2020,7,25,8,45),
                "bloqueado": False,
                "url": "http://example.com/data"
            },
            {
                "ip": "192.168.1.12",
                "user_agent": "Mozilla/5.0 (Android 10; Mobile)...",
                "payload": "Referer ausente y sin X-CSRFToken",
                "tipos": "CSRF",
                "descripcion": "Referer ausente y sin X-CSRFToken",
                "fecha": datetime(2020,12,1,14,5),
                "bloqueado": True,
                "url": "http://example.com/dump"
            },
            {
                "ip": "192.168.1.17",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2)...",
                "payload": "Content-Type sospechoso: text/plain",
                "tipos": "CSRF",
                "descripcion": "Content-Type sospechoso: text/plain",
                "fecha": datetime(2021,5,5,8,40),
                "bloqueado": False,
                "url": "http://example.com/execimm"
            },
            {
                "ip": "192.168.1.27",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64)...",
                "payload": "JSON POST desde origen externo",
                "tipos": "CSRF",
                "descripcion": "JSON POST desde origen externo (posible CSRF)",
                "fecha": datetime(2022,3,21,8,50),
                "bloqueado": False,
                "url": "http://example.com/fileget"
            },

            # --- XSS ---
            {
                "ip": "192.168.1.3",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64)...",
                "payload": "<script>alert(1)</script>",
                "tipos": "XSS",
                "descripcion": "Etiqueta <script> (directa)",
                "fecha": datetime(2020,3,10,9,15),
                "bloqueado": False,
                "url": "http://example.com/db"
            },
            {
                "ip": "192.168.1.8",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)...",
                "payload": "<img src=x onerror=alert(1)>",
                "tipos": "XSS",
                "descripcion": "<img ... onerror>",
                "fecha": datetime(2020,8,30,17,10),
                "bloqueado": True,
                "url": "http://example.com/query"
            },
            {
                "ip": "192.168.1.13",
                "user_agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)...",
                "payload": "javascript:alert(1)",
                "tipos": "XSS",
                "descripcion": "URI javascript:",
                "fecha": datetime(2021,1,19,9,30),
                "bloqueado": False,
                "url": "http://example.com/char"
            },
            {
                "ip": "192.168.1.18",
                "user_agent": "Mozilla/5.0 (Android 11; Mobile)...",
                "payload": "<svg onload=alert(1)>",
                "tipos": "XSS",
                "descripcion": "SVG con onload/on* (SVG vector)",
                "fecha": datetime(2021,6,22,15,10),
                "bloqueado": True,
                "url": "http://example.com/sys"
            },
            {
                "ip": "192.168.1.28",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "payload": "eval(alert(1))",
                "tipos": "XSS",
                "descripcion": "Ejecución dinámica (eval/Function/setTimeout)",
                "fecha": datetime(2022,4,14,15,25),
                "bloqueado": True,
                "url": "http://example.com/pgsleep"
            },

            # --- DoS ---
            {
                "ip": "192.168.1.4",
                "user_agent": "Mozilla/5.0 (Windows NT 6.1; WOW64)...",
                "payload": "Tasa de peticiones: 150 req/min",
                "tipos": "DoS",
                "descripcion": "Alta tasa de peticiones desde IP",
                "fecha": datetime(2020,4,5,16,20),
                "bloqueado": True,
                "url": "http://example.com/search"
            },
            {
                "ip": "192.168.1.9",
                "user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)...",
                "payload": "Tasa de peticiones: 120 req/min",
                "tipos": "DoS",
                "descripcion": "Posible saturación desde IP",
                "fecha": datetime(2020,9,14,12,55),
                "bloqueado": False,
                "url": "http://example.com/exec"
            },
            {
                "ip": "192.168.1.14",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)...",
                "payload": "Tasa de peticiones: 180 req/min",
                "tipos": "DoS",
                "descripcion": "Alta tasa de peticiones desde IP",
                "fecha": datetime(2021,2,14,16,15),
                "bloqueado": True,
                "url": "http://example.com/pg"
            },
            {
                "ip": "192.168.1.19",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "payload": "Tasa de peticiones: 140 req/min",
                "tipos": "DoS",
                "descripcion": "Posible saturación desde IP",
                "fecha": datetime(2021,7,15,11,40),
                "bloqueado": True,
                "url": "http://example.com/mssql"
            },
            {
                "ip": "192.168.1.29",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X)...",
                "payload": "Flooding POST/GET",
                "tipos": "DoS",
                "descripcion": "Flooding POST/GET masivo",
                "fecha": datetime(2022,5,5,18,20),
                "bloqueado": True,
                "url": "http://example.com/api"
            },

            # --- Scraping/Escaneo ---
            {
                "ip": "192.168.1.40",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X)...",
                "payload": "Acceso a 80 endpoints distintos",
                "tipos": "Scraping/Escaneo",
                "descripcion": "Número anormal de endpoints distintos accedidos",
                "fecha": datetime(2023,4,5,17,40),
                "bloqueado": True,
                "url": "http://example.com/openrowset"
            },
            {
                "ip": "192.168.1.41",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "payload": "Listar directorios y ficheros",
                "tipos": "Scraping/Escaneo",
                "descripcion": "Acceso masivo a directorios",
                "fecha": datetime(2023,4,10,10,10),
                "bloqueado": True,
                "url": "http://example.com/files"
            },
            {
                "ip": "192.168.1.42",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1)...",
                "payload": "Descarga masiva de datos",
                "tipos": "Scraping/Escaneo",
                "descripcion": "Scraping de endpoints críticos",
                "fecha": datetime(2023,4,12,11,30),
                "bloqueado": False,
                "url": "http://example.com/data"
            },
            {
                "ip": "192.168.1.43",
                "user_agent": "Mozilla/5.0 (Linux x86_64; Ubuntu 20.04)...",
                "payload": "Acceso repetido a API sin límite",
                "tipos": "Scraping/Escaneo",
                "descripcion": "Intentos repetidos a API",
                "fecha": datetime(2023,4,15,14,20),
                "bloqueado": False,
                "url": "http://example.com/api"
            },
            {
                "ip": "192.168.1.44",
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X)...",
                "payload": "Escaneo de puertos",
                "tipos": "Scraping/Escaneo",
                "descripcion": "Escaneo de puertos TCP/UDP",
                "fecha": datetime(2023,4,20,9,50),
                "bloqueado": True,
                "url": "http://example.com/ports"
            },
        ]


        for data in atacantes_data:
            atacante, created = Atacante.objects.get_or_create(
                ip=data["ip"],
                payload=data["payload"],
                fecha=data["fecha"],
                defaults={
                    "user_agent": data["user_agent"],
                    "tipos": data["tipos"],
                    "descripcion": data["descripcion"],
                    "bloqueado": data["bloqueado"],
                    "url": data["url"]
                }
            )
            if created:
                self.stdout.write(f"✅ Atacante creado: {atacante.ip} - {atacante.fecha}")
            else:
                self.stdout.write(f"ℹ️ Atacante ya existe: {atacante.ip} - {atacante.fecha}")

        self.stdout.write(
            self.style.SUCCESS("🎉 ¡Registros de atacantes inicializados exitosamente!")
        )

# --- INSTRUCCIONES ---
# Guardar como: users/management/commands/initialize_atacantes.py
# Ejecutar:
# python manage.py initialize_atacantes
# Luego levantar servidor:
# python manage.py runserver
