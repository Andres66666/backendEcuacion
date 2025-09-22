from django.utils import timezone

import cloudinary
from django.shortcuts import render
from .models import (
    Atacante,
    EquipoHerramienta,
    GastoOperacion,
    GastosGenerales,
    Modulo,
    Proyecto,
    ManoDeObra,
    Materiales,
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)
from .serializers import (
    AtacanteSerializer,
    EquipoHerramientaSerializer,
    GastoOperacionSerializer,
    GastosGeneralesSerializer,
    ModuloSerializer,
    ProyectoSerializer,
    LoginSerializer,
    ManoDeObraSerializer,
    MaterialesSerializer,
    PermisoSerializer,
    RolPermisoSerializer,
    RolSerializer,
    UsuarioRolSerializer,
    UsuarioSerializer,
)
from rest_framework import viewsets
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Prefetch
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from cloudinary import uploader
from django.db import models
from decimal import Decimal, ROUND_HALF_UP
from rest_framework.decorators import action

from decimal import Decimal, InvalidOperation
from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import AllowAny

import json


# =====================================================
# === =============  seccion 1   === ==================
# =====================================================


class AtacanteViewSet(viewsets.ModelViewSet):
    queryset = Atacante.objects.all().order_by("-fecha")
    serializer_class = AtacanteSerializer


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

            # ==============================
            # INTENTOS FALLIDOS (EXENTO PARA ADMIN)
            # ==============================
            if not check_password(password, usuario.password):
                if not es_admin:  # ← NUEVO: Solo aplica a no-admins
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

                    # Mensajes según intento (solo para no-admins)
                    if usuario.intentos_fallidos == 1:
                        mensaje_error = "Credenciales incorrectas. Intento 1 de 3."
                    elif usuario.intentos_fallidos == 2:
                        mensaje_error = "Credenciales incorrectas. Intento 2 de 3. Contacte con el administrador si olvidó su contraseña."
                    elif usuario.intentos_fallidos >= 3:
                        usuario.estado = False  # Inactiva solo si no es admin
                        mensaje_error = "Credenciales incorrectas. Intentos superados. Cuenta inhabilitada, comuníquese con el administrador."

                    usuario.save()
                    return Response(
                        {"error": mensaje_error, "tipo_mensaje": "error"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    # Para admin: Solo mensaje suave, sin incrementar contadores
                    return Response(
                        {
                            "error": "Credenciales incorrectas. Como administrador, revise sus datos sin penalizaciones.",
                            "tipo_mensaje": "advertencia",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # ==============================
            # LOGIN EXITOSO: Reset contadores (siempre)
            # ==============================
            usuario.intentos_fallidos = 0
            usuario.logins_exitosos += 1
            usuario.ultimo_intento = timezone.now()
            usuario.save()

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

            refresh = RefreshToken.for_user(usuario)
            access_token = str(refresh.access_token)

            # ... (resto del código igual hasta la sección de MENSAJES DE INICIO DE SESIÓN)

            # ==============================
            # MENSAJES DE INICIO DE SESIÓN
            # ==============================
            mensaje_principal = "¡Inicio de sesión exitoso!"
            mensaje_adicional = ""
            tipo_mensaje = "exito"
            dias_transcurridos = 0
            requiere_cambio_password = False
            mensaje_urgente = (
                False  # ← NUEVO: Flag para mensajes que requieren lectura manual
            )
            if not es_admin:  # ← Solo aplica reglas a no-admins
                # Control de primer login / cambio obligatorio
                if not usuario.fecha_cambio_password:  # Nunca cambió contraseña
                    if usuario.logins_exitosos == 1:
                        mensaje_adicional = (
                            "Cambie su contraseña, este es su primer inicio de sesión."
                        )
                        requiere_cambio_password = True
                        mensaje_urgente = True  # ← NUEVO: Requiere cierre manual
                        tipo_mensaje = "advertencia_urgente"  # ← NUEVO: Tipo especial
                    elif usuario.logins_exitosos == 2:
                        mensaje_adicional = "Debe cambiar su contraseña obligatoriamente, este es su segundo inicio de sesión. despues de este inicio de sesion sera bloqueada la cuenta si no cambia la contraseña"
                        requiere_cambio_password = True
                        mensaje_urgente = True  # ← NUEVO: Requiere cierre manual
                        tipo_mensaje = "advertencia_urgente"  # ← NUEVO: Tipo especial
                    elif usuario.logins_exitosos >= 3:
                        usuario.estado = False
                        usuario.save()
                        return Response(
                            {
                                "error": "Cuenta bloqueada por no cambiar contraseña. Comuniquese con el administrador",
                                "tipo_mensaje": "error",
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )

                # Control de caducidad (solo para no-admins)
                if usuario.fecha_cambio_password:
                    dias_transcurridos = (
                        timezone.now().date() - usuario.fecha_cambio_password.date()
                    ).days
                else:
                    dias_transcurridos = (
                        timezone.now().date() - usuario.fecha_creacion.date()
                    ).days

                if dias_transcurridos >= 90:
                    usuario.estado = False
                    usuario.save()
                    return Response(
                        {
                            "error": "Su contraseña ha caducado y su cuenta fue desactivada por incumplimiento de normas.",
                            "tipo_mensaje": "error",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
                elif dias_transcurridos == 89:
                    mensaje_adicional = (
                        "Debe cambiar su contraseña de forma obligatoria. Día 89."
                    )
                    requiere_cambio_password = True
                    tipo_mensaje = "advertencia"
                elif dias_transcurridos == 88:
                    mensaje_adicional = (
                        "Advertencia: su contraseña caducará pronto. Día 88."
                    )
                    tipo_mensaje = "advertencia"
            else:
                # Para admin: Mensaje simple
                mensaje_adicional = "Bienvenido, administrador. Acceso completo."

            return Response(
                {
                    "access_token": access_token,
                    "roles": roles,
                    "permisos": permisos,
                    "nombre_usuario": usuario.nombre,
                    "apellido": usuario.apellido,
                    "imagen_url": usuario.imagen_url,
                    "usuario_id": usuario.id,
                    "mensaje": mensaje_principal,
                    "mensaje_adicional": mensaje_adicional,
                    "tipo_mensaje": tipo_mensaje,
                    "dias_transcurridos": dias_transcurridos,
                    "requiere_cambio_password": requiere_cambio_password,
                    "mensaje_urgente": mensaje_urgente,  # ← NUEVO: Para manejo en frontend
                },
                status=status.HTTP_200_OK,
            )

        except Usuario.DoesNotExist:
            # Registrar intento de ataque o usuario no existente
            try:
                frontend_ips = ["127.0.0.1", "192.168.0.4"]  # tu backend de confianza
                if request.META.get("REMOTE_ADDR") not in frontend_ips:
                    Atacante.objects.create(
                        ip=request.META.get("REMOTE_ADDR"),
                        tipos="Usuario no encontrado",
                        payload=json.dumps(request.data),
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                        bloqueado=True,
                        fecha=now(),
                    )

                print("[LoginView] Ataque registrado: usuario no encontrado")
            except Exception as e:
                import traceback

                print(traceback.format_exc())
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
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

        # ⚡ Detectar cambio de contraseña y reset de intentos fallidos
        nueva_password = data.get("password")
        cambio_password = False
        if nueva_password and not check_password(nueva_password, instance.password):
            # Solo si es distinta de la actual
            data["password"] = make_password(nueva_password)
            data["fecha_cambio_password"] = timezone.now()
            cambio_password = True  # ← NUEVO: Flag para reset

        # ⚡ Detectar reactivación de usuario (estado False → True) y reset de intentos fallidos
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

        if UsuarioRol.objects.filter(usuario_id=usuario_id, rol_id=rol_id).exists():
            return Response(
                {"error": ["El usuario ya tiene este rol asignado"]},
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


# =====================================================
# === =============  seccion 2   === ==================
# =====================================================
class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            nombre_proyecto = data.get("NombreProyecto", "").strip()
            if not nombre_proyecto:
                return Response(
                    {"error": "El campo NombreProyecto es obligatorio."}, status=400
                )

            existente = Proyecto.objects.filter(
                NombreProyecto__iexact=nombre_proyecto
            ).first()
            if existente:
                return Response(
                    {
                        "mensaje": "Ya existe un proyecto con este nombre.",
                        "id_general": existente.id_general,
                        "NombreProyecto": existente.NombreProyecto,
                        "carga_social": existente.carga_social,
                        "iva_efectiva": existente.iva_efectiva,
                        "herramientas": existente.herramientas,
                        "gastos_generales": existente.gastos_generales,
                        "iva_tasa_nominal": existente.iva_tasa_nominal,
                        "it": existente.it,
                        "iue": existente.iue,
                        "ganancia": existente.ganancia,
                        "a_costo_venta": existente.a_costo_venta,
                        "b_margen_utilidad": existente.b_margen_utilidad,
                        "porcentaje_global_100": existente.porcentaje_global_100,
                    },
                    status=200,
                )

            id_usuario = data.get("creado_por")
            usuario = Usuario.objects.get(id=id_usuario) if id_usuario else None

            proyecto = Proyecto.objects.create(
                NombreProyecto=nombre_proyecto,
                carga_social=data.get("carga_social", 0),
                iva_efectiva=data.get("iva_efectiva", 0),
                herramientas=data.get("herramientas", 0),
                gastos_generales=data.get("gastos_generales", 0),
                iva_tasa_nominal=data.get("iva_tasa_nominal", 0),
                it=data.get("it", 0),
                iue=data.get("iue", 0),
                ganancia=data.get("ganancia", 0),
                a_costo_venta=data.get("a_costo_venta", 0),
                b_margen_utilidad=data.get("b_margen_utilidad", 0),
                porcentaje_global_100=data.get("porcentaje_global_100", 0),
                creado_por=usuario,
                modificado_por=usuario,
            )

            serializer = self.get_serializer(proyecto)
            return Response(serializer.data, status=201)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            for field in [
                "NombreProyecto",
                "carga_social",
                "iva_efectiva",
                "herramientas",
                "gastos_generales",
                "iva_tasa_nominal",
                "it",
                "iue",
                "ganancia",
                "a_costo_venta",
                "b_margen_utilidad",
                "porcentaje_global_100",
            ]:
                if field in data:
                    setattr(
                        instance,
                        field,
                        (
                            data[field]
                            if field != "NombreProyecto"
                            else data[field].strip()
                        ),
                    )

            if "modificado_por" in data:
                usuario = Usuario.objects.get(id=data["modificado_por"])
                instance.modificado_por = usuario

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        identificador_id = self.request.query_params.get("identificador", None)
        if identificador_id is not None:
            queryset = queryset.filter(identificador__id_general=identificador_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Importar modelos relacionados
        from .models import (
            GastoOperacion,
            Materiales,
            ManoDeObra,
            EquipoHerramienta,
            GastosGenerales,
        )

        # Buscar todos los gastos asociados al proyecto
        gastos = GastoOperacion.objects.filter(identificador=instance)

        for gasto in gastos:
            # Borrar hijos primero
            Materiales.objects.filter(id_gasto_operacion=gasto).delete()
            ManoDeObra.objects.filter(id_gasto_operacion=gasto).delete()
            EquipoHerramienta.objects.filter(id_gasto_operacion=gasto).delete()
            GastosGenerales.objects.filter(id_gasto_operacion=gasto).delete()
            # Luego borrar el gasto
            gasto.delete()

        # Finalmente borrar el proyecto
        instance.delete()

        return Response(
            {
                "mensaje": "Proyecto y todos sus registros asociados fueron eliminados correctamente."
            },
            status=status.HTTP_204_NO_CONTENT,
        )


# Sección 2
class ModuloViewSet(viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        proyecto_id = self.request.query_params.get("proyecto", None)
        if proyecto_id:
            queryset = queryset.filter(proyecto_id=proyecto_id)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            proyecto_id = data.get("proyecto")  # ID del proyecto
            if not proyecto_id:
                return Response(
                    {"error": "Debe proporcionar un proyecto válido"}, status=400
                )

            proyecto = Proyecto.objects.get(id_general=proyecto_id)
            id_usuario = data.get("creado_por")
            usuario = Usuario.objects.get(id=id_usuario) if id_usuario else None

            modulo = Modulo.objects.create(
                proyecto=proyecto,
                codigo=data.get("codigo", "").strip(),
                nombre=data.get("nombre", "").strip(),
                creado_por=usuario,
                modificado_por=usuario,
            )

            serializer = self.get_serializer(modulo)
            return Response(serializer.data, status=201)

        except Proyecto.DoesNotExist:
            return Response({"error": "Proyecto no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            for field in ["codigo", "nombre"]:
                if field in data:
                    setattr(instance, field, data[field].strip())

            if "modificado_por" in data:
                usuario = Usuario.objects.get(id=data["modificado_por"])
                instance.modificado_por = usuario

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)


class GastoOperacionViewSet(viewsets.ModelViewSet):
    queryset = GastoOperacion.objects.all()
    serializer_class = GastoOperacionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Se espera una lista de ítems."}, status=400)

        identificador_id = None
        if data and isinstance(data[0], dict) and "identificador" in data[0]:
            identificador_data = data[0]["identificador"]
            if (
                isinstance(identificador_data, dict)
                and "id_general" in identificador_data
            ):
                identificador_id = identificador_data["id_general"]

        if identificador_id:
            try:
                identificador = Proyecto.objects.get(id_general=identificador_id)
            except Proyecto.DoesNotExist:
                return Response(
                    {"error": "Identificador proporcionado no existe."}, status=400
                )
        else:
            return Response(
                {"error": "Debe proporcionar un proyecto válido"}, status=400
            )

        gastos_guardados = []
        for item_data in data:  # Cambiado: usa item_data para serializer
            # Usa el serializer para validar y mapear (incluyendo modulo_id → modulo)
            serializer = self.get_serializer(data=item_data)
            if serializer.is_valid():
                # Maneja usuario manualmente (no viene en serializer)
                id_usuario = item_data.get("creado_por")
                if id_usuario:
                    try:
                        usuario = Usuario.objects.get(id=id_usuario)
                        serializer.validated_data["creado_por"] = usuario
                        serializer.validated_data["modificado_por"] = usuario
                    except Usuario.DoesNotExist:
                        return Response({"error": "Usuario no encontrado"}, status=400)

                # Serializer guarda automáticamente (modulo_id se mapea a modulo)
                gasto = serializer.save(identificador=identificador)
                gastos_guardados.append(serializer.data)
            else:
                return Response({"error": serializer.errors}, status=400)

        return Response(
            {
                "mensaje": "Gastos creados correctamente.",
                "identificador_general": identificador.id_general,
                "gastos": gastos_guardados,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Usa serializer con partial=True para updates parciales (e.g., solo modulo_id)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Maneja usuario modificado (no viene en serializer)
        id_usuario = request.data.get("modificado_por")
        if id_usuario:
            try:
                usuario = Usuario.objects.get(id=id_usuario)
                serializer.validated_data["modificado_por"] = usuario
            except Usuario.DoesNotExist:
                return Response({"error": "Usuario no encontrado"}, status=400)

        # Serializer maneja todo: mapea modulo_id → modulo y guarda
        serializer.save()
        return Response(serializer.data)

    def save(self, *args, **kwargs):
        try:
            cantidad = Decimal(str(self.cantidad or "0"))
            precio = Decimal(str(self.precio_unitario or "0"))
            self.costo_parcial = cantidad * precio
        except (InvalidOperation, TypeError, ValueError):
            self.costo_parcial = Decimal("0")
        super().save(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()
        identificador_id = self.request.query_params.get("identificador", None)
        if identificador_id is not None:
            queryset = queryset.filter(
                identificador__id_general=identificador_id
            )  # Filtrar por el ID del identificador
        return queryset


# =====================================================
# === =============  seccion 3   === ==================
# =====================================================


class MaterialesViewSet(viewsets.ModelViewSet):
    queryset = Materiales.objects.all()
    serializer_class = MaterialesSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            id_gasto = data.get("id_gasto_operacion")
            id_usuario = data.get("creado_por")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"}, status=400
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)
            usuario = Usuario.objects.get(id=id_usuario) if id_usuario else None

            material = Materiales.objects.create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data.get("descripcion"),
                unidad=data.get("unidad"),
                cantidad=data.get("cantidad", 0),
                precio_unitario=data.get("precio_unitario", 0),
                total=data.get("total", 0),
                creado_por=usuario,
            )

            serializer = self.get_serializer(material)
            return Response(serializer.data, status=201)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                gasto_operacion = GastoOperacion.objects.get(
                    id=data["id_gasto_operacion"]
                )
                instance.id_gasto_operacion = gasto_operacion

            if "descripcion" in data:
                instance.descripcion = data["descripcion"]

            if "unidad" in data:
                instance.unidad = data["unidad"]

            if "cantidad" in data:
                instance.cantidad = data["cantidad"]

            if "precio_unitario" in data:
                instance.precio_unitario = data["precio_unitario"]

            if "total" in data:
                instance.total = data["total"]

            # 👇 Solo se actualiza el modificado_por
            if "modificado_por" in data:
                usuario = Usuario.objects.get(id=data["modificado_por"])
                instance.modificado_por = usuario

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset


class ManoDeObraViewSet(viewsets.ModelViewSet):
    queryset = ManoDeObra.objects.all()
    serializer_class = ManoDeObraSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            id_gasto = data.get("id_gasto_operacion")
            id_usuario = data.get("creado_por")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"}, status=400
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)
            usuario = Usuario.objects.get(id=id_usuario) if id_usuario else None

            mano = ManoDeObra.objects.create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data.get("descripcion"),
                unidad=data.get("unidad"),
                cantidad=data.get("cantidad", 0),
                precio_unitario=data.get("precio_unitario", 0),
                total=data.get("total", 0),
                creado_por=usuario,
            )

            serializer = self.get_serializer(mano)
            return Response(serializer.data, status=201)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                gasto_operacion = GastoOperacion.objects.get(
                    id=data["id_gasto_operacion"]
                )
                instance.id_gasto_operacion = gasto_operacion

            if "descripcion" in data:
                instance.descripcion = data["descripcion"]

            if "unidad" in data:
                instance.unidad = data["unidad"]

            if "cantidad" in data:
                instance.cantidad = data["cantidad"]

            if "precio_unitario" in data:
                instance.precio_unitario = data["precio_unitario"]

            if "total" in data:
                instance.total = data["total"]

            if "modificado_por" in data:
                usuario = Usuario.objects.get(id=data["modificado_por"])
                instance.modificado_por = usuario

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset


class EquipoHerramientaViewSet(viewsets.ModelViewSet):
    queryset = EquipoHerramienta.objects.all()
    serializer_class = EquipoHerramientaSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            id_gasto = data.get("id_gasto_operacion")
            id_usuario = data.get("creado_por")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"}, status=400
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)
            usuario = Usuario.objects.get(id=id_usuario) if id_usuario else None

            equipo = EquipoHerramienta.objects.create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data.get("descripcion"),
                unidad=data.get("unidad"),
                cantidad=data.get("cantidad", 0),
                precio_unitario=data.get("precio_unitario", 0),
                total=data.get("total", 0),
                creado_por=usuario,
            )

            serializer = self.get_serializer(equipo)
            return Response(serializer.data, status=201)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                gasto_operacion = GastoOperacion.objects.get(
                    id=data["id_gasto_operacion"]
                )
                instance.id_gasto_operacion = gasto_operacion

            if "descripcion" in data:
                instance.descripcion = data["descripcion"]

            if "unidad" in data:
                instance.unidad = data["unidad"]

            if "cantidad" in data:
                instance.cantidad = data["cantidad"]

            if "precio_unitario" in data:
                instance.precio_unitario = data["precio_unitario"]

            if "total" in data:
                instance.total = data["total"]

            if "modificado_por" in data:
                usuario = Usuario.objects.get(id=data["modificado_por"])
                instance.modificado_por = usuario

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset


class GastosGeneralesViewSet(viewsets.ModelViewSet):
    queryset = GastosGenerales.objects.all()
    serializer_class = GastosGeneralesSerializer

    def create(self, request, *args, **kwargs):
        print("Datos recibidos:", request.data)
        data = request.data.copy()

        try:
            id_gasto = data.get("id_gasto_operacion")
            id_usuario = data.get("creado_por")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)
            usuario = None
            if id_usuario:
                usuario = Usuario.objects.get(id=id_usuario)

            gasto_general = GastosGenerales.objects.create(
                id_gasto_operacion=gasto_operacion,
                total=data.get("total", 0),
                creado_por=usuario,
            )

            serializer = self.get_serializer(gasto_general)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except GastoOperacion.DoesNotExist:
            return Response(
                {"error": "GastoOperacion no encontrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Usuario.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                try:
                    gasto_operacion = GastoOperacion.objects.get(
                        id=data["id_gasto_operacion"]
                    )
                    instance.id_gasto_operacion = gasto_operacion
                except GastoOperacion.DoesNotExist:
                    return Response(
                        {"error": "GastoOperacion no encontrado"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if "total" in data:
                instance.total = data["total"]

            # 👇 Aquí ya NO modificamos creado_por
            if "modificado_por" in data:
                try:
                    usuario = Usuario.objects.get(id=data["modificado_por"])
                    instance.modificado_por = usuario
                except Usuario.DoesNotExist:
                    return Response(
                        {"error": "Usuario no encontrado"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastosGenerales.DoesNotExist:
            return Response(
                {"error": "Registro no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset
