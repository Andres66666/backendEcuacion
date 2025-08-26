# serializers.py
from rest_framework import serializers
from .models import (
    GastoOperacion, IdentificadorGeneral, Rol, Permiso, Usuario, RolPermiso, UsuarioRol,
    Materiales, ManoDeObra, EquipoHerramienta,
    GastosGeneralesAdministrativos
)
# =====================================================
# === =============  seccion 1   === ==================
# =====================================================
class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField(max_length=100, required=True)  # 👈 obligatorio
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


# =====================================================
# === =============  seccion 2   === ==================
# =====================================================

class IdentificadorGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model =  IdentificadorGeneral
        fields = '__all__'

class GastoOperacionSerializer(serializers.ModelSerializer):
    identificador = IdentificadorGeneralSerializer(read_only=True)  # Asegúrate de que esto esté aquí

    class Meta:
        model = GastoOperacion
        fields = '__all__'  

# =====================================================
# === =============  seccion 3   === ==================
# =====================================================

class MaterialesSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(queryset=GastoOperacion.objects.all())
    class Meta:
        model = Materiales
        fields = '__all__'
class ManoDeObraSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(queryset=GastoOperacion.objects.all())
    class Meta:
        model = ManoDeObra
        fields = '__all__'
class EquipoHerramientaSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(queryset=GastoOperacion.objects.all())
    class Meta:
        model = EquipoHerramienta
        fields = '__all__'
class GastosGeneralesAdministrativosSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(queryset=GastoOperacion.objects.all())
    class Meta:
        model = GastosGeneralesAdministrativos
        fields = '__all__'


