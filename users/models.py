# Create your models here.
import os
from django.utils import timezone

from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password
from decimal import Decimal, InvalidOperation
from django_otp.util import random_hex
from django_otp.oath import TOTP
import base64
import qrcode
from io import BytesIO
import pyotp
from datetime import timedelta
from django.utils.crypto import get_random_string
import uuid


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

    # ... hasta aqui funciona el codigo correo  ...
    # ← NUEVO: Campos para 2FA (agrega si no existen)
    tipo_2fa = models.CharField(
        max_length=20,
        choices=[("correo", "Correo"), ("totp", "Google Authenticator")],
        default="correo",
    )
    secret_2fa = models.CharField(max_length=32, blank=True, null=True)

    # ← NUEVO: Métodos para TOTP
    def generar_secret_2fa(self):
        """Genera un nuevo secreto TOTP para Google Authenticator"""
        if not self.secret_2fa:
            self.secret_2fa = pyotp.random_base32()
            self.save()

    def generar_qr_authenticator(self):
        """Devuelve la imagen QR en base64 para escanear con Google Authenticator"""
        if not self.secret_2fa:
            self.generar_secret_2fa()
        totp_uri = pyotp.TOTP(self.secret_2fa).provisioning_uri(
            name=self.correo, issuer_name="EcuacionPotosi"
        )
        img = qrcode.make(totp_uri)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return qr_base64

    def verificar_codigo_totp(self, codigo):
        """Verifica un código del Authenticator"""
        if not self.secret_2fa:
            return False
        totp = pyotp.TOTP(self.secret_2fa)
        return totp.verify(codigo)


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


class Codigo2FA(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expirado = models.BooleanField(default=False)

    def es_valido(self):
        return (
            not self.expirado and (timezone.now() - self.creado_en).seconds < 300
        )  # 5 min


class TempPasswordReset(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    temp_password = models.CharField(
        max_length=128
    )  # Encriptada o plana (para verificación simple)
    creado_en = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    expirado = models.BooleanField(default=False)

    def es_valido(self):
        if self.expirado or self.usado:
            return False
        return (timezone.now() - self.creado_en) < timedelta(minutes=15)

    def __str__(self):
        return f"Token {self.token} para {self.usuario.correo}"


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
    
    # NUEVO: campo para registrar la URL/endpoint atacado
    url = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ip} - {self.fecha}"
