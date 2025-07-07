

# Create your models here.
from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password

# === MODELOS DE USUARIO, ROL Y PERMISO ===

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

    def save(self, *args, **kwargs):
        # Solo volver a encriptar si la contraseña ha cambiado
        if 'pbkdf2' not in self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class UsuarioRol(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('usuario', 'rol')


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('rol', 'permiso')


# === MODELOS DE CATEGORIZACIÓN Y COSTOS ===
class Categorias(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


# === MODELOS DE COSTOS DIRECTOS ===

class Materiales(models.Model):
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class ManoDeObra(models.Model):
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    carga_social = models.DecimalField(max_digits=5, decimal_places=2)
    impuestos_iva = models.DecimalField(max_digits=5, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.unidad} - {self.total}"


class EquipoHerramienta(models.Model):
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    herramientas = models.DecimalField(max_digits=5, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.unidad} - {self.total}"


# === MODELO DE ECUACIÓN / CÁLCULO ===

class Ecuacion(models.Model):
    materiales = models.ForeignKey(Materiales, on_delete=models.CASCADE)
    mano_de_obra = models.ForeignKey(ManoDeObra, on_delete=models.CASCADE)
    quipo_herramienta = models.ForeignKey(EquipoHerramienta, on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Ecuación #{self.id}"


# === GASTOS GENERALES Y ADMINISTRATIVOS ===
class GastosGeneralesAdministrativos(models.Model):
    ecuacion = models.ForeignKey(Ecuacion, on_delete=models.CASCADE) # recuperar el total de 1
    gastos_generales = models.DecimalField(max_digits=5, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Gastos Generales #{self.id}"


class IdentificadorGeneral(models.Model):
    id_general = models.AutoField(primary_key=True)
    NombreProyecto = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return f"Registro #{self.id_general}"

class GastoOperacion(models.Model):
    identificador = models.ForeignKey(IdentificadorGeneral,on_delete=models.CASCADE, null=False)
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_literal = models.CharField(max_length=255, blank=True, null=True)
    costo_parcial = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.costo_parcial = (self.cantidad or Decimal("0")) * (self.precio_unitario or Decimal("0"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descripcion} ({self.cantidad} {self.unidad} @ {self.precio_unitario})"
