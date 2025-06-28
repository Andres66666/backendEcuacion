# serializers.py

from rest_framework import serializers
from .models import (
    Rol, Permiso, Usuario, RolPermiso, UsuarioRol,
    Categorias, Materiales, ManoDeObra, EquipoHerramienta,
    Ecuacion, GastosGeneralesAdministrativos
)

# Serializers existentes (los de Rol, Permiso, Usuario, UsuarioRol, RolPermiso)
# Los mantenemos como ya los tienes.
class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField(max_length=100, required=False, allow_null=True)
    password = serializers.CharField(max_length=255, required=True)  
    
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class UsuarioRolSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    rol = RolSerializer(read_only=True)

    class Meta:
        model = UsuarioRol
        fields = '__all__'

class RolPermisoSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    permiso = PermisoSerializer(read_only=True)

    class Meta:
        model = RolPermiso
        fields = '__all__'


# === NUEVOS SERIALIZERS ===

class CategoriasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = '__all__'


class MaterialesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materiales
        fields = '__all__'


class ManoDeObraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManoDeObra
        fields = '__all__'


class EquipoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipoHerramienta
        fields = '__all__'


class EcuacionSerializer(serializers.ModelSerializer):
    materiales = MaterialesSerializer(read_only=True)
    mano_de_obra = ManoDeObraSerializer(read_only=True)
    quipo_herramienta = EquipoHerramientaSerializer(read_only=True)

    class Meta:
        model = Ecuacion
        fields = '__all__'


class GastosGeneralesAdministrativosSerializer(serializers.ModelSerializer):
    ecuacion = EcuacionSerializer(read_only=True)

    class Meta:
        model = GastosGeneralesAdministrativos
        fields = '__all__'


