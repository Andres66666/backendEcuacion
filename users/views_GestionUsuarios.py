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
import cloudinary.uploader

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
                Prefetch(
                    "usuariorol_set", queryset=UsuarioRol.objects.select_related("rol")
                ),
                Prefetch(
                    "usuariorol_set__rol__rolpermiso_set",
                    queryset=RolPermiso.objects.select_related("permiso"),
                ),
            ).get(correo=correo)

            es_admin = "Administrador" in [
                ur.rol.nombre for ur in usuario.usuariorol_set.all()
            ]

            if not usuario.estado:
                return Response(
                    {
                        "error": "Usuario desactivado. Contacte al administrador.",
                        "tipo_mensaje": "error",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # INTENTOS FALLIDOS (ADMIN NO SE BLOQUEA)
            if not check_password(password, usuario.password):
                if not es_admin:
                    if usuario.intentos_fallidos >= 3:
                        if (
                            usuario.ultimo_intento
                            and timezone.now() - usuario.ultimo_intento
                            < timedelta(minutes=10)
                        ):
                            return Response(
                                {
                                    "error": "Demasiados intentos fallidos. Intente nuevamente en 10 minutos.",
                                    "tipo_mensaje": "error",
                                },
                                status=status.HTTP_403_FORBIDDEN,
                            )

                    usuario.intentos_fallidos += 1
                    usuario.ultimo_intento = timezone.now()

                    if usuario.intentos_fallidos == 1:
                        mensaje_error = "Credenciales incorrectas. Intento 1 de 3."
                    elif usuario.intentos_fallidos == 2:
                        mensaje_error = "Credenciales incorrectas. Intento 2 de 3."
                    elif usuario.intentos_fallidos >= 3:
                        usuario.estado = False
                        mensaje_error = "Cuenta inhabilitada por intentos fallidos."

                    usuario.save()

                    return Response(
                        {"error": mensaje_error, "tipo_mensaje": "error"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return Response(
                        {
                            "error": "Credenciales incorrectas (administrador).",
                            "tipo_mensaje": "advertencia",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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
                return Response(
                    {
                        "error": "El usuario no tiene roles ni permisos asignados.",
                        "tipo_mensaje": "error",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # MENSAJES
            mensaje_principal = "¡Inicio de sesión exitoso!"
            mensaje_adicional = ""
            tipo_mensaje = "exito"
            requiere_cambio_password = False
            mensaje_urgente = False

            if not usuario.fecha_cambio_password:
                if usuario.logins_exitosos == 1:
                    mensaje_adicional = "Cambie su contraseña, primer inicio de sesión."
                    requiere_cambio_password = True
                    mensaje_urgente = True
                    tipo_mensaje = "advertencia_urgente"

                elif usuario.logins_exitosos == 2:
                    mensaje_adicional = "Debe cambiar su contraseña obligatoriamente."
                    requiere_cambio_password = True
                    mensaje_urgente = True
                    tipo_mensaje = "advertencia_urgente"

                elif usuario.logins_exitosos >= 3:
                    if not es_admin:
                        usuario.estado = False
                        usuario.save()
                        return Response(
                            {
                                "error": "Cuenta bloqueada por no cambiar contraseña.",
                                "tipo_mensaje": "error",
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )
                    else:
                        mensaje_adicional = "Administrador: debe cambiar su contraseña."
                        requiere_cambio_password = True
                        mensaje_urgente = True

            if usuario.fecha_cambio_password:
                dias_transcurridos = (
                    timezone.now().date() - usuario.fecha_cambio_password.date()
                ).days
            else:
                dias_transcurridos = (
                    timezone.now().date() - usuario.fecha_creacion.date()
                ).days

            if dias_transcurridos >= 90:
                if not es_admin:
                    usuario.estado = False
                    usuario.save()
                    return Response(
                        {"error": "Contraseña caducada.", "tipo_mensaje": "error"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                else:
                    mensaje_adicional = "Administrador: contraseña caducada."
                    requiere_cambio_password = True
                    mensaje_urgente = True
                    tipo_mensaje = "advertencia_urgente"

            elif dias_transcurridos == 89:
                mensaje_adicional = "Debe cambiar su contraseña (día 89)."
                requiere_cambio_password = True
                tipo_mensaje = "advertencia"

            elif dias_transcurridos == 88:
                mensaje_adicional = "Advertencia: contraseña por caducar (día 88)."
                tipo_mensaje = "advertencia"

            # RESPUESTA
            return Response(
                {
                    "usuario_id": usuario.id,
                    "requiere_2fa": True,
                    "opciones_2fa": ["correo", "totp"],
                    "mensaje": mensaje_principal,
                    "roles": roles,
                    "permisos": permisos,
                    "nombre_usuario": usuario.nombre,
                    "apellido": usuario.apellido,
                    "imagen_url": usuario.imagen_url,
                    "mensaje_adicional": mensaje_adicional,
                    "tipo_mensaje": tipo_mensaje,
                    "dias_transcurridos": dias_transcurridos,
                    "requiere_cambio_password": requiere_cambio_password,
                    "mensaje_urgente": mensaje_urgente,
                },
                status=status.HTTP_200_OK,
            )

        except Usuario.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )


class Verificar2FAView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        usuario_id = request.data.get("usuario_id")
        codigo = request.data.get("codigo")
        metodo = request.data.get("metodo")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        if not metodo or metodo not in ["correo", "totp"]:
            return Response({"error": "Método 2FA inválido"}, status=400)
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
            print("ERROR EN GENERAR QR:")
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

        subject = "Código de verificación"
        message = f"Hola {usuario.nombre}, tu código es: {codigo} (válido 5 minutos)."
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
        except Exception as e:
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
        temp_pass = get_random_string(10)

        token = uuid.uuid4()
        TempPasswordReset.objects.create(
            usuario=usuario,
            token=token,
            temp_password=temp_pass,
            usado=False,
            expirado=False,
        )

        subject = "Restablecimiento de contraseña temporal"
        message = f"Hola {usuario.nombre}, tu contraseña temporal es: {temp_pass}. Úsala para restablecer tu contraseña en el sistema. Válida por 15 minutos."
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
            print(
                f"[ResetPassword] Temp_pass {temp_pass} enviada a {correo} con token {token}"
            )
        except Exception as e:
            print(f"[ResetPassword] Error email: {e}")

        return Response(
            {
                "mensaje": "Se envió un correo con la contraseña temporal. Ingresa el código recibido para continuar.",
                "usuario_id": usuario.id,
                "temp_token": str(token),
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
        if token_obj.temp_password != temp_pass:
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

    # =====================================================
    # CREAR USUARIO
    # =====================================================
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Subir imagen si existe
        if "imagen_url" in request.FILES:
            try:
                uploaded_image = cloudinary.uploader.upload(
                    request.FILES["imagen_url"], folder="usuarios"
                )

                # Guardar URL y public_id
                data["imagen_url"] = uploaded_image.get("secure_url")
                data["imagen_public_id"] = uploaded_image.get("public_id")

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

    # =====================================================
    # ACTUALIZAR USUARIO
    # =====================================================
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        data = request.data.copy()

        print("Archivos recibidos:", request.FILES)

        # =================================================
        # SUBIR NUEVA IMAGEN
        # =================================================
        if "imagen_url" in request.FILES:
            try:

                # Eliminar imagen anterior de Cloudinary
                if instance.imagen_public_id:
                    cloudinary.uploader.destroy(instance.imagen_public_id)

                # Subir nueva imagen
                uploaded_image = cloudinary.uploader.upload(
                    request.FILES["imagen_url"], folder="usuarios"
                )

                # Guardar nueva URL y public_id
                data["imagen_url"] = uploaded_image.get("secure_url")

                data["imagen_public_id"] = uploaded_image.get("public_id")

            except Exception as e:
                print("Error al subir imagen:", e)

                return Response(
                    {"error": "Error al actualizar imagen"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            # Mantener imagen actual
            data["imagen_url"] = instance.imagen_url
            data["imagen_public_id"] = instance.imagen_public_id

        # =================================================
        # CAMBIO DE CONTRASEÑA
        # =================================================
        nueva_password = data.get("password")

        cambio_password = False

        if nueva_password and not check_password(nueva_password, instance.password):
            data["password"] = make_password(nueva_password)

            data["fecha_cambio_password"] = timezone.now()

            cambio_password = True

        # =================================================
        # REACTIVACIÓN DE USUARIO
        # =================================================
        nuevo_estado = data.get("estado", instance.estado)

        reactivacion = (not instance.estado) and nuevo_estado

        # =================================================
        # LIMPIAR FILES
        # =================================================
        if "imagen_url" in request.FILES:
            del request._files["imagen_url"]

        # =================================================
        # SERIALIZER
        # =================================================
        serializer = self.get_serializer(instance, data=data, partial=True)

        if not serializer.is_valid():
            print("Errores del serializer:", serializer.errors)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # RESET DE INTENTOS
        # =================================================
        if cambio_password or reactivacion:
            instance.intentos_fallidos = 0

        # =================================================
        # ACTUALIZAR ROL
        # =================================================
        rol_id = request.data.get("rol")

        if rol_id:

            usuario_rol = UsuarioRol.objects.filter(usuario=instance).first()

            if usuario_rol:
                usuario_rol.rol_id = rol_id
                usuario_rol.save()

            else:
                UsuarioRol.objects.create(usuario=instance, rol_id=rol_id)

        # =================================================
        # GUARDAR USUARIO
        # =================================================
        serializer.save()

        return Response(serializer.data)

    # =====================================================
    # ELIMINAR USUARIO
    # =====================================================
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:

            # Eliminar imagen de Cloudinary
            if instance.imagen_public_id:
                cloudinary.uploader.destroy(instance.imagen_public_id)

            # Eliminar relaciones de roles
            UsuarioRol.objects.filter(usuario=instance).delete()

            # Eliminar usuario
            instance.delete()

            return Response(
                {"mensaje": "Usuario eliminado correctamente"},
                status=status.HTTP_204_NO_CONTENT,
            )

        except Exception as e:
            print("Error al eliminar usuario:", e)

            return Response(
                {"error": "Error al eliminar usuario"},
                status=status.HTTP_400_BAD_REQUEST,
            )


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
    @action(detail=False, methods=["get"])
    def permisos_por_rol(self, request):
        rol_id = request.query_params.get("rol_id")
        if not rol_id:
            return Response({"error": "rol_id es requerido"}, status=400)

        permisos_asignados = RolPermiso.objects.filter(rol_id=rol_id).values_list(
            "permiso_id", flat=True
        )
        return Response(list(permisos_asignados))


class RegistroClienteView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data

        campos_requeridos = [
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "telefono",
            "correo",
            "password",
            "ci",
        ]

        for campo in campos_requeridos:
            if campo not in data or not str(data[campo]).strip():
                return Response(
                    {"error": f"El campo '{campo}' es obligatorio"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        correo = data["correo"].strip()
        ci = data["ci"].strip()

        registro_pendiente = (
            RegistroPendiente.objects.filter(correo=correo, verificado=True)
            .order_by("-creado_en")
            .first()
        )

        if not registro_pendiente:
            return Response(
                {"error": "Debes verificar tu correo antes de registrar"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Usuario.objects.filter(correo=correo).exists():
            return Response(
                {"error": "El correo ya está registrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Usuario.objects.filter(ci=ci).exists():
            return Response(
                {"error": "El CI ya está registrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(correo)
        except ValidationError:
            return Response(
                {"error": "El correo no tiene un formato válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = data["password"].strip()
        if len(password) < 8:
            return Response(
                {"error": "La contraseña debe tener al menos 8 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha_nac = datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "La fecha debe tener formato YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rol_cliente = Rol.objects.get(nombre__iexact="Cliente", estado=True)
        except Rol.DoesNotExist:
            return Response(
                {"error": "No existe el rol Cliente activo"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            usuario = Usuario.objects.create(
                nombre=data["nombre"].strip(),
                apellido=data["apellido"].strip(),
                fecha_nacimiento=fecha_nac,
                telefono=data["telefono"].strip(),
                correo=correo,
                password=password,
                ci=ci,
                estado=True,
            )

            UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol_cliente)

            return Response(
                {
                    "mensaje": "Cliente registrado correctamente",
                    "usuario_id": usuario.id,
                    "rol_asignado": rol_cliente.nombre,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"No se pudo registrar el cliente: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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

        return Response(
            {
                "mensaje": "Verificación correcta",
                "datos": registro.datos,
                "verificado": True,
            },
            status=200,
        )
