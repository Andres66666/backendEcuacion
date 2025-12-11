import json
import uuid
import traceback
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db.models import Prefetch
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken

import cloudinary
# =================== MODELOS ===================
from .models import (
    Atacante,
    Codigo2FA,
    Permiso,
    RegistroPendiente,
    Rol,
    RolPermiso,
    TempPasswordReset,
    Usuario,
    UsuarioRol,
)

# =================== SERIALIZERS ===================
from .serializers import (
    LoginSerializer,
    PermisoSerializer,
    RolPermisoSerializer,
    RolSerializer,
    UsuarioRolSerializer,
    UsuarioSerializer,
)

# =================== FUNCIONES DE AUDITORÍA ===================
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
# =====================================================
# === =============  seccion 1   === ==================
# =====================================================


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        correo = serializer.validated_data.get("correo")
        password = serializer.validated_data.get("password")

        try:
            usuario = Usuario.objects.prefetch_related(
                Prefetch("usuariorol_set", queryset=UsuarioRol.objects.select_related("rol")),
                Prefetch("usuariorol_set__rol__rolpermiso_set", queryset=RolPermiso.objects.select_related("permiso")),
            ).get(correo=correo)

            es_admin = "Administrador" in [ur.rol.nombre for ur in usuario.usuariorol_set.all()]

            if not usuario.estado:
                return Response(
                    {"error": "Usuario desactivado. Contacte al administrador.", "tipo_mensaje": "error"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # INTENTOS FALLIDOS (EXENTO PARA ADMIN)
            if not check_password(password, usuario.password):
                if not es_admin:
                    if usuario.intentos_fallidos >= 3:
                        if usuario.ultimo_intento and timezone.now() - usuario.ultimo_intento < timedelta(minutes=10):
                            return Response(
                                {"error": "Demasiados intentos fallidos. Intente nuevamente en 10 minutos.", "tipo_mensaje": "error"},
                                status=status.HTTP_403_FORBIDDEN,
                            )

                    usuario.intentos_fallidos += 1
                    usuario.ultimo_intento = timezone.now()

                    if usuario.intentos_fallidos == 1:
                        mensaje_error = "Credenciales incorrectas. Intento 1 de 3."
                    elif usuario.intentos_fallidos == 2:
                        mensaje_error = "Credenciales incorrectas. Intento 2 de 3. Contacte con el administrador si olvidó su contraseña."
                    elif usuario.intentos_fallidos >= 3:
                        usuario.estado = False
                        mensaje_error = "Credenciales incorrectas. Intentos superados. Cuenta inhabilitada, comuníquese con el administrador."

                    usuario.save()

                   

                    return Response({"error": mensaje_error, "tipo_mensaje": "error"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(
                        {"error": "Credenciales incorrectas. Como administrador, revise sus datos sin penalizaciones.", "tipo_mensaje": "advertencia"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # LOGIN EXITOSO: Reset contadores
            usuario.intentos_fallidos = 0
            usuario.logins_exitosos += 1
            usuario.ultimo_intento = timezone.now()
            usuario.save()

            # ROLES Y PERMISOS
            roles = [ur.rol.nombre for ur in usuario.usuariorol_set.all()]
            permisos = []
            for ur in usuario.usuariorol_set.all():
                permisos += [rp.permiso.nombre for rp in ur.rol.rolpermiso_set.all()]

            if not roles or not permisos:
                return Response({"error": "El usuario no tiene roles ni permisos asignados.", "tipo_mensaje": "error"}, status=status.HTTP_403_FORBIDDEN)

           
            # MENSAJES DE INICIO DE SESIÓN
            mensaje_principal = "¡Inicio de sesión exitoso!"
            mensaje_adicional = ""
            tipo_mensaje = "exito"
            dias_transcurridos = 0
            requiere_cambio_password = False
            mensaje_urgente = False
            if not es_admin:
                # Control de primer login / cambio obligatorio
                if not usuario.fecha_cambio_password:
                    if usuario.logins_exitosos == 1:
                        mensaje_adicional = "Cambie su contraseña, este es su primer inicio de sesión."
                        requiere_cambio_password = True
                        mensaje_urgente = True
                        tipo_mensaje = "advertencia_urgente"
                    elif usuario.logins_exitosos == 2:
                        mensaje_adicional = "Debe cambiar su contraseña obligatoriamente, este es su segundo inicio de sesión. Después de este inicio de sesión será bloqueada la cuenta si no cambia la contraseña"
                        requiere_cambio_password = True
                        mensaje_urgente = True
                        tipo_mensaje = "advertencia_urgente"
                    elif usuario.logins_exitosos >= 3:
                        usuario.estado = False
                        usuario.save()
                        return Response({"error": "Cuenta bloqueada por no cambiar contraseña. Comuníquese con el administrador", "tipo_mensaje": "error"}, status=status.HTTP_403_FORBIDDEN)

                # Control de caducidad
                dias_transcurridos = None
                if usuario.fecha_cambio_password:
                    dias_transcurridos = (timezone.now().date() - usuario.fecha_cambio_password.date()).days
                else:
                    dias_transcurridos = (timezone.now().date() - usuario.fecha_creacion.date()).days

                if dias_transcurridos >= 90:
                    usuario.estado = False
                    usuario.save()
                    return Response({"error": "Su contraseña ha caducado y su cuenta fue desactivada por incumplimiento de normas.", "tipo_mensaje": "error"}, status=status.HTTP_403_FORBIDDEN)
                elif dias_transcurridos == 89:
                    mensaje_adicional = "Debe cambiar su contraseña de forma obligatoria. Día 89."
                    requiere_cambio_password = True
                    tipo_mensaje = "advertencia"
                elif dias_transcurridos == 88:
                    mensaje_adicional = "Advertencia: su contraseña caducará pronto. Día 88."
                    tipo_mensaje = "advertencia"
            else:
                mensaje_adicional = "Bienvenido, administrador. Acceso completo."

            # RESPUESTA PARA SELECCIÓN DE 2FA
            return Response({
                "usuario_id": usuario.id,
                "requiere_2fa": True,
                "opciones_2fa": ["correo", "totp"],
                "mensaje": "Seleccione un método de verificación de dos factores.",
                "roles": roles,
                "permisos": permisos,
                "nombre_usuario": usuario.nombre,
                "apellido": usuario.apellido,
                "imagen_url": usuario.imagen_url,
                "mensaje_adicional": mensaje_adicional,
                "tipo_mensaje": tipo_mensaje,
                "dias_transcurridos": dias_transcurridos,
                "dias_transcurridos": dias_transcurridos,
                "requiere_cambio_password": requiere_cambio_password,
                "mensaje_urgente": mensaje_urgente,
            }, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            # Registrar intento de ataque o usuario no existente
            try:
                Atacante.objects.create(
                    ip=request.META.get("REMOTE_ADDR"),
                    tipos="Usuario no encontrado",
                    payload=json.dumps(request.data),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    bloqueado=True,
                    fecha=timezone.now(),
                )
            except Exception as e:
                print("Error guardando ataque:", e)

            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class Verificar2FAView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        usuario_id = request.data.get("usuario_id")
        codigo = request.data.get("codigo")
        metodo = request.data.get(
            "metodo"
        )  # ← MODIFICADO: Recibe 'metodo' del frontend ("correo" o "totp")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        if not metodo or metodo not in ["correo", "totp"]:
            return Response(
                {"error": "Método 2FA inválido"}, status=400
            )  # ← MODIFICADO: Valida metodo

        # ← MODIFICADO: Verificar según 'metodo' elegido (no tipo_2fa fijo)
        if metodo == "correo":
            codigo_obj = (
                Codigo2FA.objects.filter(usuario=usuario, codigo=codigo, expirado=False)
                .order_by("-creado_en")
                .first()
            )
            if not codigo_obj or not codigo_obj.es_valido():
                return Response({"error": "Código inválido o caducado"}, status=400)
            codigo_obj.expirado = True
            codigo_obj.save()

        elif metodo == "totp":
            if not usuario.verificar_codigo_totp(codigo):
                return Response({"error": "Código TOTP incorrecto"}, status=400)

        # Generar token JWT definitivo
        refresh = RefreshToken.for_user(usuario)
        access_token = str(refresh.access_token)

        return Response(
            {
                "access_token": access_token,
                "usuario_id": usuario.id,
                "roles": [ur.rol.nombre for ur in usuario.usuariorol_set.all()],
                "mensaje": "Autenticación 2FA exitosa",
            },
            status=200,
        )

class GenerarQRView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        usuario_id = request.data.get("usuario_id")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        try:
            usuario.generar_secret_2fa()
            qr_base64 = usuario.generar_qr_authenticator()
            return Response(
                {
                    "qr_base64": qr_base64,
                    "mensaje": "Escanee este código QR con Google Authenticator.",
                },
                status=200,
            )
        except Exception as e:
            print("🧨 ERROR EN GENERAR QR:")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=500)

class EnviarCodigoCorreoView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        usuario_id = request.data.get("usuario_id")
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        # Buscar el código más reciente no expirado o crear uno nuevo
        codigo_obj = (
            Codigo2FA.objects.filter(usuario=usuario, expirado=False)
            .order_by("-creado_en")
            .first()
        )
        if codigo_obj and codigo_obj.es_valido():
            codigo = codigo_obj.codigo
        else:
            codigo = get_random_string(6, allowed_chars="0123456789")
            Codigo2FA.objects.create(usuario=usuario, codigo=codigo)

        # Envío de correo (requerirá configuración SMTP o proveedor)
        subject = "Código de verificación"
        message = f"Hola {usuario.nombre}, tu código es: {codigo} (válido 5 minutos)."
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
        except Exception as e:
            # En dev puede fallar si no configuras SMTP; lo imprimimos y retornamos OK para pruebas
            print("[EnviarCodigoCorreo] No se pudo enviar email:", e)

        return Response({"mensaje": "Código enviado"}, status=200)

class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        correo = request.data.get("correo")
        try:
            usuario = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)
        temp_pass = get_random_string(10)  # Genera temporal
        # ← MODIFICADO: No actualizar password aún; guardar en token temporal
        token = uuid.uuid4()
        TempPasswordReset.objects.create(
            usuario=usuario,
            token=token,
            temp_password=temp_pass,  # Plana para verificación (o encripta si prefieres)
            usado=False,
            expirado=False,
        )
        # Envío de correo con temp_pass
        subject = "Restablecimiento de contraseña temporal"
        message = f"Hola {usuario.nombre}, tu contraseña temporal es: {temp_pass}. Úsala para restablecer tu contraseña en el sistema. Válida por 15 minutos."
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
            print(
                f"[ResetPassword] Temp_pass {temp_pass} enviada a {correo} con token {token}"
            )
        except Exception as e:
            print(f"[ResetPassword] Error email: {e}")
            # No falla la respuesta; asume enviado (o maneja rollback si quieres)
        return Response(
            {
                "mensaje": "Se envió un correo con la contraseña temporal. Ingresa el código recibido para continuar.",
                "usuario_id": usuario.id,
                "temp_token": str(token),  # ← NUEVO: Retorna token para frontend
            },
            status=200,
        )

class VerificarTempPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        usuario_id = request.data.get("usuario_id")
        temp_token = request.data.get("temp_token")
        temp_pass = request.data.get("temp_pass")
        try:
            token_obj = TempPasswordReset.objects.get(
                usuario_id=usuario_id, token=temp_token, usado=False
            )
        except TempPasswordReset.DoesNotExist:
            return Response({"error": "Token inválido o expirado"}, status=400)
        if not token_obj.es_valido():
            token_obj.expirado = True
            token_obj.save()
            return Response({"error": "Token expirado o ya usado"}, status=400)
        if (
            token_obj.temp_password != temp_pass
        ):  # ← Verifica contra la temp_pass guardada
            # Opcional: Contar intentos y bloquear después de 3
            return Response({"error": "Contraseña temporal incorrecta"}, status=400)
        return Response(
            {
                "valid": True,
                "mensaje": "Contraseña temporal verificada. Ingrese nueva contraseña.",
            },
            status=200,
        )

class CambiarPasswordTempView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        usuario_id = request.data.get("usuario_id")
        temp_token = request.data.get("temp_token")
        nueva_password = request.data.get("nueva_password")
        confirmar_password = request.data.get("confirmar_password")
        if nueva_password != confirmar_password:
            return Response({"error": "Las contraseñas no coinciden"}, status=400)
        if len(nueva_password) < 8:
            return Response(
                {"error": "La nueva contraseña debe tener al menos 8 caracteres"},
                status=400,
            )
        try:
            token_obj = TempPasswordReset.objects.get(
                usuario_id=usuario_id, token=temp_token, usado=False
            )
        except TempPasswordReset.DoesNotExist:
            return Response({"error": "Token inválido o expirado"}, status=400)
        if not token_obj.es_valido():
            token_obj.expirado = True
            token_obj.save()
            return Response({"error": "Token expirado o ya usado"}, status=400)
        # Actualizar usuario
        usuario = token_obj.usuario
        usuario.password = make_password(nueva_password)
        usuario.fecha_cambio_password = timezone.now()
        usuario.intentos_fallidos = 0  # Reset
        usuario.estado = True  # Reactivar si estaba bloqueado
        usuario.save()
        # Marcar token como usado
        token_obj.usado = True
        token_obj.save()
        return Response(
            {
                "mensaje": "Contraseña actualizada exitosamente. Vuelve al login para ingresar con tu nueva contraseña.",
                "usuario_id": usuario.id,
            },
            status=200,
        )

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

    def create(self, request, *args, **kwargs):
        nombre = request.data.get("nombre", "").strip()

        # Validar duplicado
        if Rol.objects.filter(nombre__iexact=nombre).exists():
            return Response(
                {"error": f"El rol '{nombre}' ya existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        nombre = request.data.get("nombre", "").strip()

        # Verificar que no exista otro rol con el mismo nombre
        if Rol.objects.filter(nombre__iexact=nombre).exclude(id=instance.id).exists():
            return Response(
                {"error": f"Ya existe otro rol con el nombre '{nombre}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"mensaje": f"Rol '{nombre}' actualizado correctamente."},
            status=status.HTTP_200_OK,
        )

class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer

    def create(self, request, *args, **kwargs):
        nombre = request.data.get("nombre", "").strip()

        # Validar duplicado
        if Permiso.objects.filter(nombre__iexact=nombre).exists():
            return Response(
                {"error": f"El permiso '{nombre}' ya existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        nombre = request.data.get("nombre", "").strip()

        # Validar duplicado en otro registro
        if (
            Permiso.objects.filter(nombre__iexact=nombre)
            .exclude(id=instance.id)
            .exists()
        ):
            return Response(
                {"error": f"Ya existe otro permiso con el nombre '{nombre}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"mensaje": f"Permiso '{nombre}' actualizado correctamente."},
            status=status.HTTP_200_OK,
        )

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Subir imagen si existe
        if "imagen_url" in request.FILES:
            try:
                uploaded_image = cloudinary.uploader.upload(request.FILES["imagen_url"])
                data["imagen_url"] = uploaded_image.get("url")
            except Exception as e:
                return Response(
                    {"error": f"Error al subir imagen: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Crear usuario
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()

        # Asignar rol si viene en el request
        rol_id = request.data.get("rol")
        if rol_id:
            UsuarioRol.objects.create(usuario=usuario, rol_id=rol_id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        print("Archivos recibidos:", request.FILES)

        # Subir nueva imagen si se incluye
        if "imagen_url" in request.FILES:
            try:
                uploaded_image = cloudinary.uploader.upload(request.FILES["imagen_url"])
                data["imagen_url"] = uploaded_image.get("url")
            except Exception as e:
                print("Error al subir imagen:", e)
                return Response(
                    {"error": "Error al subir imagen a Cloudinary"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Mantener imagen actual si no se sube nueva
            data["imagen_url"] = instance.imagen_url

        # Detectar cambio de contraseña y reset de intentos fallidos
        nueva_password = data.get("password")
        cambio_password = False
        if nueva_password and not check_password(nueva_password, instance.password):
            # Solo si es distinta de la actual
            data["password"] = make_password(nueva_password)
            data["fecha_cambio_password"] = timezone.now()
            cambio_password = True  # ← NUEVO: Flag para reset

        #  Detectar reactivación de usuario (estado False → True) y reset de intentos fallidos
        nuevo_estado = data.get("estado", instance.estado)  # Usa actual si no se envía
        reactivacion = (
            not instance.estado
        ) and nuevo_estado  # ← NUEVO: Solo si era False y ahora True

        # Eliminar archivo accidental
        if "imagen_url" in request.FILES:
            del request._files["imagen_url"]

        serializer = self.get_serializer(instance, data=data, partial=True)

        if not serializer.is_valid():
            print("Errores del serializer:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ← NUEVO: Aplicar resets antes de guardar
        if cambio_password or reactivacion:
            instance.intentos_fallidos = 0  # Reset en ambos casos
            if cambio_password:
                print(
                    f"Contraseña cambiada para usuario {instance.id}: intentos fallidos reseteados a 0"
                )
            if reactivacion:
                print(
                    f"Usuario {instance.id} reactivado: intentos fallidos reseteados a 0"
                )

        serializer.save()
        return Response(serializer.data)

class UsuarioRolViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRol.objects.all()
    serializer_class = UsuarioRolSerializer

    
    def create(self, request, *args, **kwargs):
        usuario = request.data.get("usuario")
        rol = request.data.get("rol")

        usuario_id = usuario.get("id") if isinstance(usuario, dict) else usuario
        rol_id = rol.get("id") if isinstance(rol, dict) else rol

        # Verificar si ya tiene ESTE rol
        if UsuarioRol.objects.filter(usuario_id=usuario_id, rol_id=rol_id).exists():
            return Response(
                {"error": ["Este usuario ya tiene este rol asignado."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario_rol = UsuarioRol.objects.create(usuario_id=usuario_id, rol_id=rol_id)
        return Response(
            UsuarioRolSerializer(usuario_rol).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        instance = self.get_object()

        usuario_raw = request.data.get("usuario")
        rol_raw = request.data.get("rol")

        usuario_id = (
            usuario_raw.get("id") if isinstance(usuario_raw, dict) else usuario_raw
        )
        rol_id = rol_raw.get("id") if isinstance(rol_raw, dict) else rol_raw

        if (
            UsuarioRol.objects.filter(usuario_id=usuario_id, rol_id=rol_id)
            .exclude(pk=instance.pk)
            .exists()
        ):
            return Response(
                {"error": ["El usuario ya tiene este rol asignado"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.usuario_id = usuario_id
        instance.rol_id = rol_id
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer

    def create(self, request, *args, **kwargs):
        rol_id = request.data.get("rol")
        permiso_id = request.data.get("permiso")

        # Verificar si ya existe la relación entre rol y permiso
        if RolPermiso.objects.filter(rol_id=rol_id, permiso_id=permiso_id).exists():
            return Response(
                {"error": ["Este rol ya tiene este permiso asignado"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear la relación
        roles_permisos = RolPermiso.objects.create(rol_id=rol_id, permiso_id=permiso_id)
        return Response(
            RolPermisoSerializer(roles_permisos).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        instance = self.get_object()

        rol = request.data.get("rol")
        permiso = request.data.get("permiso")

        # Si vienen como objetos (dict), extraer el ID; si ya son IDs, usarlos directamente
        rol_id = rol.get("id") if isinstance(rol, dict) else rol or instance.rol_id
        permiso_id = (
            permiso.get("id")
            if isinstance(permiso, dict)
            else permiso or instance.permiso_id
        )

        # Verificar duplicidad
        if (
            RolPermiso.objects.filter(rol_id=rol_id, permiso_id=permiso_id)
            .exclude(pk=instance.pk)
            .exists()
        ):
            return Response(
                {"error": ["Este rol ya tiene este permiso asignado"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Actualizar
        instance.rol_id = rol_id
        instance.permiso_id = permiso_id
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    # Agregar este método
    @action(detail=False, methods=['get'])
    def permisos_por_rol(self, request):
        rol_id = request.query_params.get('rol_id')
        if not rol_id:
            return Response({"error": "rol_id es requerido"}, status=400)
        
        permisos_asignados = RolPermiso.objects.filter(rol_id=rol_id).values_list('permiso_id', flat=True)
        return Response(list(permisos_asignados))


class RegistroClienteView(APIView): 
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data

        # 1️⃣ Campos obligatorios
        campos_requeridos = [
            "nombre", "apellido", "fecha_nacimiento", "telefono",
            "correo", "password", "ci"
        ]

        for campo in campos_requeridos:
            if campo not in data or not str(data[campo]).strip():
                return Response(
                    {"error": f"El campo '{campo}' es obligatorio"},
                    status=400
                )

        # 2️⃣ Verificar que exista un registro pendiente verificado
        registro_pendiente = RegistroPendiente.objects.filter(
            correo=data["correo"], verificado=True
        ).order_by('-creado_en').first()

        if not registro_pendiente:
            return Response({"error": "Debes verificar tu correo antes de registrar"}, status=400)

        # 3️⃣ Validar duplicados reales
        if Usuario.objects.filter(correo=data["correo"]).exists():
            return Response({"error": "El correo ya está registrado"}, status=400)
        if Usuario.objects.filter(ci=data["ci"]).exists():
            return Response({"error": "El CI ya está registrado"}, status=400)

        # 4️⃣ Validar formato de correo
        try:
            validate_email(data["correo"])
        except ValidationError:
            return Response({"error": "El correo no tiene un formato válido"}, status=400)

        # 5️⃣ Validar contraseña
        if len(data["password"]) < 8:
            return Response({"error": "La contraseña debe tener al menos 8 caracteres"}, status=400)

        # 6️⃣ Validar fecha de nacimiento
        try:
            fecha_nac = datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "La fecha debe tener formato YYYY-MM-DD"}, status=400)

        # 7️⃣ Crear usuario
        usuario = Usuario.objects.create(
            nombre=data["nombre"].strip(),
            apellido=data["apellido"].strip(),
            fecha_nacimiento=fecha_nac,
            telefono=data["telefono"].strip(),
            correo=data["correo"].strip(),
            password=make_password(data["password"]),
            ci=data["ci"].strip(),
            estado=True
        )

        # 8️⃣ Asignar rol Cliente
        try:
            rol_cliente = Rol.objects.get(nombre__iexact="Cliente")
        except Rol.DoesNotExist:
            usuario.delete()
            return Response({"error": "No existe el rol Cliente"}, status=500)

        UsuarioRol.objects.create(usuario=usuario, rol=rol_cliente)

        # 9️⃣ Asegurar que el rol Cliente tenga permisos asignados
        # Por ejemplo, todos los permisos que correspondan a "Cliente"
        permisos_cliente = Permiso.objects.filter(nombre__in=["Cliente"])  # Reemplaza con los permisos reales
        for permiso in permisos_cliente:
            RolPermiso.objects.get_or_create(rol=rol_cliente, permiso=permiso)

        return Response({
            "mensaje": "Cliente registrado correctamente",
            "usuario_id": usuario.id
        }, status=201)

class ValidarCorreoView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        correo = request.data.get("correo", "").strip()
        if not correo:
            return Response({"error": "El correo es obligatorio"}, status=400)

        try:
            validate_email(correo)
        except ValidationError:
            return Response({"error": "Correo con formato inválido"}, status=400)

        if Usuario.objects.filter(correo=correo).exists():
            return Response({"error": "El correo ya está registrado"}, status=400)

        return Response({"mensaje": "Correo válido"}, status=200)

class EnviarVerificacionView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        datos = request.data
        correo = datos.get("correo")
        if not correo:
            return Response({"error": "Correo obligatorio"}, status=400)

        # evitar duplicados reales
        if Usuario.objects.filter(correo=correo).exists():
            return Response({"error": "El correo ya está registrado"}, status=400)

        # registrar pendiente
        registro = RegistroPendiente.objects.create(datos=datos, correo=correo)

        link = f"{settings.FRONTEND_URL}/confirmar/{registro.token}"

        mensaje = "Hola,\n\nConfirma tus datos:\n\n"
        for key, value in datos.items():
            mensaje += f"{key}: {value}\n"

        mensaje += f"\nHaz clic aquí:\n{link}\n\nGracias!"

        try:
            send_mail(
                "Verificación de datos",
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [correo],
            )
        except Exception:
            return Response({"error": "No se pudo enviar correo"}, status=500)

        return Response({"mensaje": "Correo enviado"}, status=200)

class ConfirmarRegistroView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        registro = get_object_or_404(RegistroPendiente, token=token)

        # si ya estaba verificado devolver igual
        if not registro.verificado:
            registro.verificado = True
            registro.save()

        return Response({
            "mensaje": "Verificación correcta",
            "datos": registro.datos,
            "verificado": True
        }, status=200)
