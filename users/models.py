# Create your models here.
from django.utils import timezone

from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password
from decimal import Decimal, InvalidOperation


# =====================================================
# === =============  seccion 1   === ==================
# =====================================================
class Rol(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    ci = models.CharField(max_length=20, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    imagen_url = models.URLField(max_length=500, null=True, blank=True)
    estado = models.BooleanField(default=True)

    intentos_fallidos = models.IntegerField(default=0)
    ultimo_intento = models.DateTimeField(null=True, blank=True)
    fecha_cambio_password = models.DateTimeField(null=True, blank=True)
    logins_exitosos = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # Solo volver a encriptar si la contraseña ha cambiado
        if "pbkdf2" not in self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class UsuarioRol(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("usuario", "rol")


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("rol", "permiso")


# =====================================================
# === =============  seccion 2   === ==================
# =====================================================


class Proyecto(models.Model):
    id_general = models.AutoField(primary_key=True)
    NombreProyecto = models.CharField(max_length=255, unique=True)
    carga_social = models.DecimalField(max_digits=5, decimal_places=2)
    iva_efectiva = models.DecimalField(max_digits=5, decimal_places=2)
    herramientas = models.DecimalField(max_digits=5, decimal_places=2)
    gastos_generales = models.DecimalField(max_digits=5, decimal_places=2)
    iva_tasa_nominal = models.DecimalField(max_digits=5, decimal_places=2)
    it = models.DecimalField(max_digits=5, decimal_places=2)
    iue = models.DecimalField(max_digits=5, decimal_places=2)
    ganancia = models.DecimalField(max_digits=5, decimal_places=2)
    a_costo_venta = models.DecimalField(max_digits=5, decimal_places=2)
    b_margen_utilidad = models.DecimalField(max_digits=5, decimal_places=2)
    porcentaje_global_100 = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="Proyecto_creado"
    )
    modificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="Proyecto_modificado",
    )

    def __str__(self):
        return f"Registro #{self.id_general}"


# cambios nuevos modulo


# ... (código existente de secciones 1 y 2) ...
class Modulo(models.Model):
    proyecto = models.ForeignKey(
        Proyecto, on_delete=models.CASCADE, related_name="modulos"
    )
    codigo = models.CharField(
        max_length=50
    )  # Código único por proyecto si es necesario
    nombre = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="modulos_creados"
    )
    modificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modulos_modificados",
    )

    class Meta:
        unique_together = ("proyecto", "codigo")  # Código único por proyecto

    def __str__(self):
        return (
            f"{self.codigo} - {self.nombre} (Proyecto: {self.proyecto.NombreProyecto})"
        )


class GastoOperacion(models.Model):
    identificador = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=False)
    modulo = models.ForeignKey(  # Nuevo campo: opcional
        Modulo, on_delete=models.SET_NULL, null=True, blank=True, related_name="gastos"
    )
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_literal = models.CharField(max_length=255, blank=True, null=True)
    costo_parcial = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="Gastos_creados"
    )
    modificado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="Gastos_modificados"
    )

    def save(self, *args, **kwargs):
        try:
            cantidad_decimal = (
                Decimal(str(self.cantidad)) if self.cantidad else Decimal("0")
            )
        except InvalidOperation:
            cantidad_decimal = Decimal("0")
        try:
            precio_decimal = (
                Decimal(str(self.precio_unitario))
                if self.precio_unitario
                else Decimal("0")
            )
        except InvalidOperation:
            precio_decimal = Decimal("0")
        self.costo_parcial = cantidad_decimal * precio_decimal
        super().save(*args, **kwargs)

    def __str__(self):
        modulo_str = f" (Módulo: {self.modulo.nombre})" if self.modulo else ""
        return f"{self.descripcion}{modulo_str} ({self.cantidad} {self.unidad} @ {self.precio_unitario})"


# =====================================================
# === =============  seccion 3   === ==================
# =====================================================
class Materiales(models.Model):
    id_gasto_operacion = models.ForeignKey(GastoOperacion, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="materiales_creados"
    )
    modificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="materiales_modificados",
    )

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class ManoDeObra(models.Model):
    id_gasto_operacion = models.ForeignKey(GastoOperacion, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="manos_creadas"
    )
    modificado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="manos_modificadas"
    )

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class EquipoHerramienta(models.Model):
    id_gasto_operacion = models.ForeignKey(GastoOperacion, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="equipos_creados"
    )
    modificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="equipos_modificados",
    )

    def __str__(self):
        return f"{self.unidad} - {self.total}"


# === GASTOS GENERALES Y ADMINISTRATIVOS ===
class GastosGenerales(models.Model):
    id_gasto_operacion = models.ForeignKey(GastoOperacion, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="gastos_creados"
    )
    modificado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="gastos_modificados"
    )

    def __str__(self):
        return f"{self.total}"


# === AUDITORIA ATACNATES ===
class Atacante(models.Model):
    ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    payload = models.TextField(blank=True, null=True)
    tipos = models.TextField()  # Lista de ataques detectados
    descripcion = models.TextField()  #
    fecha = models.DateTimeField(auto_now_add=True)
    bloqueado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ip} - {self.fecha}"
