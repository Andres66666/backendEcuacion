import logging
import json
import socket
import uuid
import hashlib
import re
import requests
from django.utils.deprecation import MiddlewareMixin
from users.models import AuditoriaEvento # Asume que el modelo existe

logger = logging.getLogger("auditoria_servidor")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


# ================= Utilidades de IP ======================
def is_private_ip(ip):
    """Verifica si una IP es privada (RFC 1918) o de loopback."""
    if not ip:
        return False
    # 10.0.0.0/8 | 172.16.0.0/12 | 192.168.0.0/16 | 127.0.0.0/8
    priv_re = re.compile(r"^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|127\.)")
    return bool(priv_re.match(ip))

def obtener_ip_publica():
    """Obtiene la IP pública externa mediante un servicio externo."""
    try:
        return requests.get("https://api.ipify.org", timeout=1).text
    except Exception:
        return None

def obtener_ip_servidor_lan():
    """Obtiene la IP privada (LAN) del servidor de Django."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_privada = s.getsockname()[0]
        s.close()
        return ip_privada
    except Exception:
        return None

# ================= Navegador y SO =======================
def detectar_navegador_y_so(user_agent):
    """Detecta navegador y sistema operativo a partir del User-Agent."""
    navegador = "Desconocido"
    sistema = "Desconocido"

    # ================= Navegador =================
    if re.search(r"OPR\/|Opera", user_agent):
        navegador = "Opera"
    elif re.search(r"Edg\/|Edge", user_agent):
        navegador = "Edge"
    elif re.search(r"Brave\/", user_agent):
        navegador = "Brave"
    elif re.search(r"Chrome\/", user_agent):
        navegador = "Chrome"
    elif re.search(r"Firefox\/", user_agent):
        navegador = "Firefox"
    elif re.search(r"Safari\/", user_agent) and not re.search(r"Chrome\/", user_agent):
        navegador = "Safari"

    # ================= Sistema operativo =================
    if re.search(r"Windows NT", user_agent):
        sistema = "Windows"
    elif re.search(r"Mac OS X", user_agent):
        sistema = "Mac OS X"
    elif re.search(r"Linux", user_agent):
        sistema = "Linux"
    elif re.search(r"Android", user_agent):
        sistema = "Android"
    elif re.search(r"iPhone|iPad", user_agent):
        sistema = "iOS"

    return navegador, sistema


# ================= IP del cliente ========================
def obtener_ip_cliente(request):
    """
    Intenta obtener la IP pública real del cliente a través de varios encabezados.
    Si la IP encontrada es privada, busca la IP pública externa como fallback.
    """
    ip_candidata = None

    # 1. X-Forwarded-For (típico en proxies/balanceadores)
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # La primera IP en XFF suele ser la del cliente (o la más cercana)
        ips = [ip.strip() for ip in xff.split(",") if ip.strip()]
        if ips:
            # Priorizamos la primera IP que no sea privada
            for ip_cand in ips:
                if not is_private_ip(ip_cand):
                    ip_candidata = ip_cand
                    break
            # Si todas son privadas, usamos la última como la IP más remota
            if not ip_candidata:
                ip_candidata = ips[-1] 

    # 2. Otros encabezados comunes
    if not ip_candidata:
        for h in ("HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP", "HTTP_CLIENT_IP"):
            ip_cand = request.META.get(h)
            if ip_cand and not is_private_ip(ip_cand):
                ip_candidata = ip_cand
                break

    # 3. REMOTE_ADDR
    if not ip_candidata:
        ip_candidata = request.META.get("REMOTE_ADDR") 

    # ================= Lógica de corrección de IP pública =================

    # Si la IP candidata es privada (192.168.x.x, 127.0.0.1, etc.), 
    # obtenemos la IP pública externa como la verdadera IP pública.
    if ip_candidata and is_private_ip(ip_candidata):
        logger.debug(f"IP Candidata ({ip_candidata}) es privada. Buscando IP pública externa.")
        ip_publica_externa = obtener_ip_publica()
        return ip_publica_externa or ip_candidata

    # Si la IP candidata no es privada (es pública o None), la devolvemos.
    # Si es None, el último fallback es la IP pública del servidor.
    return ip_candidata or obtener_ip_publica() or "IP pública desconocida"


# ================= Geolocalización ======================
def obtener_ubicacion_por_ip(ip):
    """Retorna ciudad, región, país y coordenadas de la IP."""
    if not ip or is_private_ip(ip) or ip in ["0.0.0.0", "localhost", "IP pública desconocida"]:
        return "IP local / privada, no geolocalizable"
    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon",
            timeout=2
        )
        data = resp.json()
        if data.get("status") == "success":
            city = data.get('city','')
            region = data.get('regionName','')
            country = data.get('country','')
            lat = data.get('lat')
            lon = data.get('lon')
            return f"{city}, {region}, {country} (Lat: {lat}, Lon: {lon})"
    except Exception:
        pass
    return "Ubicación desconocida"
    
# ================= Datos de la máquina ==================
def obtener_datos_maquina(request):
    """Retorna un diccionario con información del cliente y servidor."""
    datos = {}

    try:
        # IP Pública (Corregida para ser siempre externa si es posible)
        datos["ip_cliente"] = obtener_ip_cliente(request)

        # IP Privada (Reportada por el cliente o fallback del servidor)
        ip_local = None
        if request.method == "POST":
            try:
                body = json.loads(request.body.decode("utf-8"))
                ip_local = body.get("ip_local")
            except Exception:
                ip_local = request.POST.get("ip_local")
        elif request.method == "GET":
            ip_local = request.GET.get("ip_local")
            
        if ip_local == "":
            ip_local = None

        # Fallback de IP privada: si no se reporta, usamos la del servidor.
        if not ip_local:
            ip_local = obtener_ip_servidor_lan()
        
        datos["ip_local"] = ip_local 

        # Navegador y sistema
        ua = request.META.get("HTTP_USER_AGENT", "")
        navegador, sistema = detectar_navegador_y_so(ua)
        datos["navegador"] = navegador
        datos["sistema_operativo"] = sistema
        datos["user_agent_completo"] = ua

        # Ruta y URL
        datos["ruta"] = request.path
        datos["url"] = request.build_absolute_uri()
        datos["metodo_http"] = request.method
        datos["parametros"] = request.POST.dict() if request.method == "POST" else request.GET.dict()

        # Información del servidor (se mantiene para otros usos)
        datos["servidor_nombre"] = socket.gethostname()
        datos["servidor_ip"] = obtener_ip_servidor_lan() or socket.gethostbyname(socket.gethostname())
        datos["servidor_uuid"] = str(uuid.uuid4())

    except Exception as e:
        logger.error(f"Error obteniendo datos de máquina: {e}")

    return datos


# ================= Registro de BD =======================
def registrar_evento_bd(request, tipo, descripcion, severidad="BAJO", bloqueado=False, extra=None):
    """
    Registra un evento completo en la base de datos AuditoriaEvento.
    """
    try:
        datos = obtener_datos_maquina(request)
        ip_publica = datos.get("ip_cliente") # IP pública (corregida)
        ip_privada = datos.get("ip_local") # IP privada (LAN)
        ubicacion = obtener_ubicacion_por_ip(ip_publica)
        
        # Extracción de campos necesarios
        usuario_id = extra.get("usuario_id") if extra else None
        roles = extra.get("roles") if extra else None

        # Intenta obtener el nombre de la vista (acción)
        accion = getattr(request.resolver_match, "view_name", None) if getattr(request, "resolver_match", None) else None
        
        # Determinar el resultado de la acción (se asume True por defecto si no está en 'extra')
        resultado = extra.get("resultado", True) if extra else True

        # CREACIÓN DEL OBJETO: SOLO SE USAN LOS CAMPOS DEFINIDOS EN EL MODELO AuditoriaEvento
        evento = AuditoriaEvento.objects.create(
            tipo=tipo,
            accion=accion,
            descripcion=descripcion,
            resultado=resultado,
            usuario_id=usuario_id,
            # Se convierte la lista de roles en un string separado por comas
            rol_usuario=", ".join(roles) if roles else None, 
            severidad=severidad,
            # Mapeo corregido de IPs:
            ip_cliente_publica=ip_publica,
            ip_cliente_privada=ip_privada,
            navegador=datos.get("navegador"),
            sistema_operativo=datos.get("sistema_operativo"),
            ubicacion=ubicacion,
            ruta=datos.get("ruta"),
            metodo_http=datos.get("metodo_http"),
            bloqueado=bloqueado,
        )
        logger.info(f"[AUDITORIA BD] Evento registrado: {evento}")
        return evento
    except Exception as e:
        logger.error(f"Error al registrar evento en BD: {type(e).__name__} - {e}")
        return None


# ================= Middleware ==========================
class AuditoriaServidorMiddleware(MiddlewareMixin):
    """
    Middleware de auditoría del servidor.
    Registra automáticamente todos los accesos HTTP.
    """

    def process_request(self, request):
        # Ignorar peticiones a archivos estáticos o favicon
        if request.path.startswith(("/static/", "/media/", "/favicon.ico")):
            return None

        try:
            datos_cliente = obtener_datos_maquina(request)
            severidad = "BAJO"
            descripcion = (
                f"Acceso a {datos_cliente.get('ruta')} | IP Pública: {datos_cliente.get('ip_cliente')} "
                f"| IP Privada: {datos_cliente.get('ip_local')} | Navegador: {datos_cliente.get('navegador')}"
            )

            # Asumiendo que el usuario está autenticado al pasar por aquí
            usuario_id = getattr(request.user, "id", None)
            
            # Obtener roles, si el modelo de usuario tiene un campo 'rol' o método
            roles = [getattr(request.user, "rol")] if hasattr(request.user, "rol") and request.user.rol else []

            extra = {
                "datos_cliente": datos_cliente,
                "descripcion": descripcion,
                "severidad": severidad,
                "usuario_id": usuario_id,
                "roles": roles,
                "resultado": True # Asume que la solicitud de acceso fue exitosa
            }

            registrar_evento_bd(
                request=request,
                tipo="ACCESO",
                descripcion=descripcion,
                severidad=severidad,
                bloqueado=False,
                extra=extra
            )

            request.guardian_auditoria = extra # Guarda los datos en el request para uso posterior

        except Exception as e:
            logger.error(f"Error en AuditoriaServidorMiddleware: {e}")
            
        return None
