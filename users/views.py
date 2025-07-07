import cloudinary
from django.shortcuts import render
from .models import Categorias, Ecuacion, EquipoHerramienta, GastoOperacion, GastosGeneralesAdministrativos, IdentificadorGeneral, ManoDeObra, Materiales, Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from .serializers import  CategoriasSerializer, EcuacionSerializer, EquipoHerramientaSerializer, GastoOperacionSerializer, GastosGeneralesAdministrativosSerializer, IdentificadorGeneralSerializer, LoginSerializer, ManoDeObraSerializer, MaterialesSerializer, PermisoSerializer, RolPermisoSerializer, RolSerializer, UsuarioRolSerializer, UsuarioSerializer
from rest_framework import viewsets
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Prefetch
from django.contrib.auth.hashers import  check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from cloudinary import uploader



class LoginView(APIView):
    authentication_classes = []  # Eliminamos la autenticación para esta vista
    permission_classes = []      # Sin permisos especiales

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        correo = serializer.validated_data.get('correo')
        password = serializer.validated_data.get('password')

        try:
            usuario = Usuario.objects.prefetch_related(
                Prefetch('usuariorol_set', queryset=UsuarioRol.objects.select_related('rol')),
                Prefetch('usuariorol_set__rol__rolpermiso_set', queryset=RolPermiso.objects.select_related('permiso'))
            ).get(correo=correo)

            if not usuario.estado:
                return Response({
                    'error': 'No puedes iniciar sesión. Comuníquese con el administrador. Gracias.'
                }, status=status.HTTP_403_FORBIDDEN)

            if not check_password(password, usuario.password):
                return Response({'error': 'Credenciales incorrectas'}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(usuario)
            access_token = str(refresh.access_token)

            roles = [usuario_rol.rol.nombre for usuario_rol in usuario.usuariorol_set.all()]
            permisos = []
            for usuario_rol in usuario.usuariorol_set.all():
                permisos += [rp.permiso.nombre for rp in usuario_rol.rol.rolpermiso_set.all()]

            if not roles or not permisos:
                return Response({'error': 'El usuario no tiene roles ni permisos asignados.'}, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'access_token': access_token,
                'roles': roles,
                'permisos': permisos,
                'nombre_usuario': usuario.nombre,
                'apellido': usuario.apellido,
                'imagen_url': usuario.imagen_url,
                'usuario_id': usuario.id
            }, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UsuarioViewSet(viewsets.ModelViewSet):
        queryset = Usuario.objects.all()
        serializer_class = UsuarioSerializer

        def create(self, request, *args, **kwargs):
            data = request.data.copy()

            # Subir la imagen a Cloudinary si se incluye
            if 'imagen_url' in request.FILES:
                try:
                    uploaded_image = cloudinary.uploader.upload(request.FILES['imagen_url'])
                    data['imagen_url'] = uploaded_image.get('url')
                    print("Imagen subida correctamente:", data['imagen_url'])
                except Exception as e:
                    print("Error al subir imagen a Cloudinary:", e)
                    return Response({'error': 'Error al subir imagen a Cloudinary'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                print(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        def update(self, request, *args, **kwargs):
            instance = self.get_object()
            data = request.data.copy()

            print("Archivos recibidos:", request.FILES)

            # Subir nueva imagen si se incluye
            if 'imagen_url' in request.FILES:
                try:
                    uploaded_image = cloudinary.uploader.upload(request.FILES['imagen_url'])
                    data['imagen_url'] = uploaded_image.get('url')
                except Exception as e:
                    print("Error al subir imagen:", e)
                    return Response({'error': 'Error al subir imagen a Cloudinary'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Si no se sube una nueva imagen, mantener la actual
                data['imagen_url'] = instance.imagen_url

            # Eliminar el archivo si quedó por accidente
            if 'imagen_url' in request.FILES:
                del request._files['imagen_url']

            serializer = self.get_serializer(instance, data=data, partial=True)

            if not serializer.is_valid():
                print("Errores del serializer:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response(serializer.data)
        


class UsuarioRolViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRol.objects.all()
    serializer_class = UsuarioRolSerializer

    def create(self, request, *args, **kwargs):
        usuario = request.data.get('usuario')
        rol = request.data.get('rol')

        usuario_id = usuario.get('id') if isinstance(usuario, dict) else usuario
        rol_id = rol.get('id') if isinstance(rol, dict) else rol

        if UsuarioRol.objects.filter(usuario_id=usuario_id, rol_id=rol_id).exists():
            return Response({'error': ['El usuario ya tiene este rol asignado']}, status=status.HTTP_400_BAD_REQUEST)

        usuario_rol = UsuarioRol.objects.create(usuario_id=usuario_id, rol_id=rol_id)
        return Response(UsuarioRolSerializer(usuario_rol).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        instance = self.get_object()

        usuario_raw = request.data.get('usuario')
        rol_raw = request.data.get('rol')

        usuario_id = usuario_raw.get('id') if isinstance(usuario_raw, dict) else usuario_raw
        rol_id = rol_raw.get('id') if isinstance(rol_raw, dict) else rol_raw

        if UsuarioRol.objects.filter(usuario_id=usuario_id, rol_id=rol_id).exclude(pk=instance.pk).exists():
            return Response({'error': ['El usuario ya tiene este rol asignado']}, status=status.HTTP_400_BAD_REQUEST)

        instance.usuario_id = usuario_id
        instance.rol_id = rol_id
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer

    def create(self, request, *args, **kwargs):
        rol_id = request.data.get('rol')
        permiso_id = request.data.get('permiso')

        # Verificar si ya existe la relación entre rol y permiso
        if RolPermiso.objects.filter(rol_id=rol_id, permiso_id=permiso_id).exists():
            return Response({'error': ['Este rol ya tiene este permiso asignado']}, status=status.HTTP_400_BAD_REQUEST)

        # Crear la relación
        roles_permisos = RolPermiso.objects.create(rol_id=rol_id, permiso_id=permiso_id)
        return Response(RolPermisoSerializer(roles_permisos).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        instance = self.get_object()

        rol = request.data.get('rol')
        permiso = request.data.get('permiso')

        # Si vienen como objetos (dict), extraer el ID; si ya son IDs, usarlos directamente
        rol_id = rol.get('id') if isinstance(rol, dict) else rol or instance.rol_id
        permiso_id = permiso.get('id') if isinstance(permiso, dict) else permiso or instance.permiso_id

        # Verificar duplicidad
        if RolPermiso.objects.filter(rol_id=rol_id, permiso_id=permiso_id).exclude(pk=instance.pk).exists():
            return Response({'error': ['Este rol ya tiene este permiso asignado']}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar
        instance.rol_id = rol_id
        instance.permiso_id = permiso_id
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


""" usuario auto creado  """
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Subir imagen si se incluye (tu lógica original)
        if 'imagen_url' in request.FILES:
            try:
                uploaded_image = cloudinary.uploader.upload(request.FILES['imagen_url'])
                data['imagen_url'] = uploaded_image.get('url')
            except Exception as e:
                return Response({'error': 'Error al subir imagen a Cloudinary'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario = serializer.save()

        # Asignar rol 'Cliente' por defecto
        try:
            rol_cliente = Rol.objects.get(nombre='Cliente')
        except Rol.DoesNotExist:
            return Response({'error': 'Rol "Cliente" no encontrado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Asignar permiso básico 'servicios' (ajusta el nombre según tu modelo)
        try:
            permiso_servicios = Permiso.objects.get(nombre='servicios')
        except Permiso.DoesNotExist:
            return Response({'error': 'Permiso "servicios" no encontrado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Crear relación UsuarioRol si no existe
        usuario_rol, created = UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol_cliente)

        # Crear relación RolPermiso si no existe (para que el rol tenga el permiso)
        rol_permiso, created = RolPermiso.objects.get_or_create(rol=rol_cliente, permiso=permiso_servicios)
        return Response(serializer.data, status=status.HTTP_201_CREATED)






class CategoriasViewSet(viewsets.ModelViewSet):
    queryset = Categorias.objects.all()
    serializer_class = CategoriasSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)  
class MaterialesViewSet(viewsets.ModelViewSet):
    queryset = Materiales.objects.all()
    serializer_class = MaterialesSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ManoDeObraViewSet(viewsets.ModelViewSet):
    queryset = ManoDeObra.objects.all()
    serializer_class = ManoDeObraSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)    

class EquipoHerramientaViewSet(viewsets.ModelViewSet):
    queryset = EquipoHerramienta.objects.all()
    serializer_class = EquipoHerramientaSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class EcuacionViewSet(viewsets.ModelViewSet):
    queryset = Ecuacion.objects.all()
    serializer_class = EcuacionSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)    

class GastosGeneralesViewSet(viewsets.ModelViewSet):
    queryset = GastosGeneralesAdministrativos.objects.all()
    serializer_class = GastosGeneralesAdministrativosSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class IdentificadorInmuebleViewSet(viewsets.ModelViewSet):
    queryset = IdentificadorGeneral.objects.all()
    serializer_class = IdentificadorGeneralSerializer

    def create(self, request, *args, **kwargs):
        nombre_proyecto = request.data.get('NombreProyecto', '').strip()

        if not nombre_proyecto:
            return Response({'error': 'El campo NombreProyecto es obligatorio.'}, status=400)

        # Verificar si ya existe un proyecto con ese nombre
        existente = IdentificadorGeneral.objects.filter(NombreProyecto__iexact=nombre_proyecto).first()
        if existente:
            return Response({
                'mensaje': 'Ya existe un proyecto con este nombre.',
                'id_general': existente.id_general,
                'NombreProyecto': existente.NombreProyecto
            }, status=200)

        # Crear si no existe
        return super().create(request, *args, **kwargs)

class GastoOperacionViewSet(viewsets.ModelViewSet):
    queryset = GastoOperacion.objects.all()
    serializer_class = GastoOperacionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        print("Data recibida:", data)
        
        if not isinstance(data, list):
            return Response({"error": "Se espera una lista de ítems."}, status=400)

        # Intentar usar el identificador existente si se proporciona
        identificador_id = None
        if data and isinstance(data[0], dict) and 'identificador' in data[0]:
            identificador_data = data[0]['identificador']
            if isinstance(identificador_data, dict) and 'id_general' in identificador_data:
                identificador_id = identificador_data['id_general']
        
        if identificador_id:
            try:
                identificador = IdentificadorGeneral.objects.get(id_general=identificador_id)
            except IdentificadorGeneral.DoesNotExist:
                return Response({"error": "Identificador proporcionado no existe."}, status=400)
        else:
            identificador = IdentificadorGeneral.objects.create()
        
        print("Identificador usado:", identificador.id_general)

        gastos_guardados = []
        for item in data:
            item_copy = item.copy()
            if 'identificador' in item_copy:
                del item_copy['identificador']

            serializer = self.get_serializer(data=item_copy)
            serializer.is_valid(raise_exception=True)
            gasto = serializer.save(identificador=identificador)
            gastos_guardados.append(self.get_serializer(gasto).data)

        return Response({
            "mensaje": "Gastos creados correctamente.",
            "identificador_general": identificador.id_general,
            "gastos": gastos_guardados
        }, status=status.HTTP_201_CREATED)

    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()
        identificador_id = self.request.query_params.get('identificador', None)
        if identificador_id is not None:
            queryset = queryset.filter(identificador__id_general=identificador_id)  # Filtrar por el ID del identificador
        return queryset


