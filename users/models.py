from django.utils import timezone
from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password
from decimal import Decimal, InvalidOperation
import base64
import qrcode
from io import BytesIO
import pyotp
from datetime import timedelta
import uuid


# === =============  seccion 1   === ==================

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

    # Campos para 2FA (agrega si no existen)
    tipo_2fa = models.CharField(
        max_length=20,
        choices=[("correo", "Correo"), ("totp", "Google Authenticator")],
        default="correo",
    )
    secret_2fa = models.CharField(max_length=32, blank=True, null=True)

    # Métodos para TOTP
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
    ) 
    creado_en = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    expirado = models.BooleanField(default=False)

    def es_valido(self):
        if self.expirado or self.usado:
            return False
        return (timezone.now() - self.creado_en) < timedelta(minutes=15)

    def __str__(self):
        return f"Token {self.token} para {self.usuario.correo}"

class RegistroPendiente(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    datos = models.JSONField() 
    correo = models.EmailField()
    creado_en = models.DateTimeField(auto_now_add=True)
    verificado = models.BooleanField(default=False)

    def __str__(self):
        return f"Registro pendiente: {self.correo}"

# === AUDITORIA ATACNATES ===
class Atacante(models.Model):
    ip = models.GenericIPAddressField()
    fingerprint = models.CharField(max_length=64, db_index=True) 
    user_agent = models.TextField(blank=True, null=True)
    payload = models.TextField(blank=True, null=True)
    tipos = models.TextField()
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    bloqueado = models.BooleanField(default=False)
    url = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ip} - {self.fecha}"

# ================  seccion 2   =======================

class Proyecto(models.Model):
    id_proyecto = models.AutoField(primary_key=True)
    NombreProyecto = models.CharField(max_length=255)
    carga_social = models.DecimalField(max_digits=5, decimal_places=2)
    iva_efectiva = models.DecimalField(max_digits=5, decimal_places=2)
    herramientas = models.DecimalField(max_digits=5, decimal_places=2)
    gastos_generales = models.DecimalField(max_digits=5, decimal_places=2)
    iva_tasa_nominal = models.DecimalField(max_digits=5, decimal_places=2)
    it = models.DecimalField(max_digits=5, decimal_places=2)
    iue = models.DecimalField(max_digits=5, decimal_places=2)
    ganancia = models.DecimalField(max_digits=5, decimal_places=2)
    margen_utilidad = models.DecimalField(max_digits=5, decimal_places=2)

    creado_por = models.ForeignKey("Usuario",on_delete=models.CASCADE,related_name="proyectos_creados")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["creado_por", "NombreProyecto"],name="uq_proyecto_por_usuario")]

    def __str__(self):
        return f"{self.NombreProyecto} (#{self.id_proyecto})"

class Modulo(models.Model):
    proyecto = models.ForeignKey(Proyecto,on_delete=models.CASCADE,related_name="modulos")
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["proyecto", "codigo"],name="uq_modulo_codigo_por_proyecto")]

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.proyecto.NombreProyecto})"


class GastoOperacion(models.Model):
    modulo = models.ForeignKey(Modulo,on_delete=models.CASCADE,   related_name="gastos")
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_parcial = models.DecimalField(max_digits=12, decimal_places=2, default=0)


    def __str__(self):
        return f"{self.descripcion} ({self.cantidad} {self.unidad} @ {self.precio_unitario})"

# === =============  seccion 3   === ==================

class Materiales(models.Model):
    gasto_operacion = models.ForeignKey(GastoOperacion,on_delete=models.CASCADE,related_name="materiales")
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=5)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class ManoDeObra(models.Model):
    gasto_operacion = models.ForeignKey(GastoOperacion,on_delete=models.CASCADE,related_name="mano_obra")
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=5)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class EquipoHerramienta(models.Model):
    gasto_operacion = models.ForeignKey(GastoOperacion,on_delete=models.CASCADE,related_name="equipos")
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=5)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class GastosGenerales(models.Model):
    gasto_operacion = models.ForeignKey(GastoOperacion,on_delete=models.CASCADE,related_name="gastos_generales")
    totalgastosgenerales = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.total}"

