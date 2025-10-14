# serializers.py
from rest_framework import serializers
from .models import (
    Atacante,
    AuditoriaEvento,
    GastoOperacion,
    Modulo,
    Proyecto,
    Rol,
    Permiso,
    Usuario,
    RolPermiso,
    UsuarioRol,
    Materiales,
    ManoDeObra,
    EquipoHerramienta,
    GastosGenerales,
)


class AtacanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atacante
        fields = "__all__"
        
class AuditoriaEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditoriaEvento
        fields = "__all__"


# =====================================================
# === =============  seccion 1   === ==================
# =====================================================
class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField(max_length=100, required=False, allow_null=True)
    password = serializers.CharField(max_length=255, required=True)


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = "__all__"


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = "__all__"


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = "__all__"


class UsuarioRolSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    rol = RolSerializer(read_only=True)

    class Meta:
        model = UsuarioRol
        fields = "__all__"


class RolPermisoSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    permiso = PermisoSerializer(read_only=True)

    class Meta:
        model = RolPermiso
        fields = "__all__"


# =====================================================
# === =============  seccion 2   === ==================
# =====================================================


class ProyectoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Proyecto
        fields = "__all__"


class ModuloSerializer(serializers.ModelSerializer):
    proyecto = ProyectoSerializer(read_only=True)

    class Meta:
        model = Modulo
        fields = "__all__"


class GastoOperacionSerializer(serializers.ModelSerializer):
    identificador = ProyectoSerializer(read_only=True)
    modulo = ModuloSerializer(read_only=True)  # Para output: objeto completo
    modulo_id = serializers.PrimaryKeyRelatedField(  # Para input: ID o null
        queryset=Modulo.objects.all(),
        source="modulo",  # Mapea "modulo_id" → campo 'modulo'
        required=False,
        allow_null=True,
        write_only=True,  # No se incluye en output
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = GastoOperacion
        fields = "__all__"  # Incluye modulo_id automáticamente


# =====================================================
# === =============  seccion 3   === ==================
# =====================================================


class MaterialesSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(
        queryset=GastoOperacion.objects.all()
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Materiales
        fields = "__all__"


class ManoDeObraSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(
        queryset=GastoOperacion.objects.all()
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = ManoDeObra
        fields = "__all__"


class EquipoHerramientaSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(
        queryset=GastoOperacion.objects.all()
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = EquipoHerramienta
        fields = "__all__"


class GastosGeneralesSerializer(serializers.ModelSerializer):
    id_gasto_operacion = serializers.PrimaryKeyRelatedField(
        queryset=GastoOperacion.objects.all()
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = GastosGenerales
        fields = "__all__"
