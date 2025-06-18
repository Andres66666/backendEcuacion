from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import Rol, Permiso, Usuario, UsuarioRolSucursal, RolPermiso, Sucursal, Categoria
from datetime import date

class Command(BaseCommand):
    help = 'Inicializa la base de datos con datos básicos'

    def handle(self, *args, **kwargs):
        self.stdout.write("Inicializando base de datos...")

        # --- CREAR SUCURSAL POR DEFECTO ---
        sucursal_default, _ = Sucursal.objects.get_or_create(
            nombre="Sucursal Principal",
            defaults={
                'direccion': 'Dirección principal',
                'estado': True
            }
        )

        # --- CREAR ROLES ---
        admin_role, _ = Rol.objects.get_or_create(
            nombre="Administrador",
            defaults={'estado': True}
        )
        empleado_role, _ = Rol.objects.get_or_create(
            nombre="Empleado",
            defaults={'estado': True}
        )

        # --- CREAR PERMISOS ---
        permisos_data = [
            {"nombre": "vender"},
            {"nombre": "GestiónDeUsuarios"},
            {"nombre": "GestionDeProductos"},
            {"nombre": "GestionDeReportes"},
            {"nombre": "listarSucursal"},
            {"nombre": "listarRol"},
            {"nombre": "listarPermiso"},
            {"nombre": "listarUsuario"},
            {"nombre": "listarUsuarioRolSucursal"},
            {"nombre": "listarRolPermiso"},
            {"nombre": "listarCategoria"},
            {"nombre": "listarProductoMadera"},
            {"nombre": "listarVenta"},
            {"nombre": "listarDetalleVenta"},
            {"nombre": "listarFacturaRecibo"},
            {"nombre": "reportesgrafica"},
            {"nombre": "reportes"},
        ]

        permisos_objetos = {}
        for permiso in permisos_data:
            p, _ = Permiso.objects.get_or_create(
                nombre=permiso["nombre"],
                defaults={
                    'estado': True
                }
            )
            permisos_objetos[permiso["nombre"]] = p

        # --- ASIGNAR PERMISOS A ROLES ---
        permisos_admin = [permiso["nombre"] for permiso in permisos_data]

        permisos_empleado = [
            "vender", "GestionDeProductos",
            "listarVenta", "listarDetalleVenta", "listarFacturaRecibo"
        ]

        for permiso_nombre in permisos_admin:
            RolPermiso.objects.get_or_create(
                rol=admin_role,
                permiso=permisos_objetos[permiso_nombre]
            )

        for permiso_nombre in permisos_empleado:
            RolPermiso.objects.get_or_create(
                rol=empleado_role,
                permiso=permisos_objetos[permiso_nombre]
            )

        # --- CREAR CATEGORÍAS ---
        # --- CREAR CATEGORÍAS ---
        categorias_data = [
            {"nombre": "Tabla", "descripcion": "Categoría para tablas"},
            {"nombre": "Liston", "descripcion": "Categoría para listones (sin tilde)"},
            {"nombre": "Ripa", "descripcion": "Categoría para ripas"},
            {"nombre": "Mueble", "descripcion": "Categoría para muebles"},
            {"nombre": "Tijera", "descripcion": "Categoría para tijeras"},
        ]

        for categoria in categorias_data:
            Categoria.objects.get_or_create(
                nombre=categoria["nombre"],
                defaults={
                    'descripcion': categoria["descripcion"],
                    'estado': True
                }
            )


        # --- CREAR USUARIOS ---

        # Usuario Administrador
        admin_user, created_admin = Usuario.objects.get_or_create(
            ci="13247291",
            defaults={
                'nombre': "Andres Benito",
                'apellido': "Yucra",
                'fecha_nacimiento': date(1998, 11, 6),
                'telefono': "72937437",
                'correo': "benitoandrescalle035@gmail.com",
                'password': make_password("Andres1234*"),
                'estado': True,
                'imagen_url': "http://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/fnsesmm80hgwelhyzaie.jpg"
            }
        )

        if created_admin:
            self.stdout.write(f"Usuario administrador creado: {admin_user}")

        UsuarioRolSucursal.objects.get_or_create(
            usuario=admin_user,
            rol=admin_role,
            sucursal=sucursal_default
        )

        # Usuario Empleado
        empleado_user, created_empleado = Usuario.objects.get_or_create(
            ci="87654321",
            defaults={
                'nombre': "Juan Carlos",
                'apellido': "Pérez",
                'fecha_nacimiento': date(1990, 5, 15),
                'telefono': "78945612",
                'correo': "juanperez@example.com",
                'password': make_password("Empleado123*"),
                'estado': True,
                'imagen_url': "http://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/sample-image.jpg"
            }
        )

        if created_empleado:
            self.stdout.write(f"Usuario empleado creado: {empleado_user}")

        UsuarioRolSucursal.objects.get_or_create(
            usuario=empleado_user,
            rol=empleado_role,
            sucursal=sucursal_default
        )

        self.stdout.write(self.style.SUCCESS("Base de datos inicializada exitosamente!"))

        # --- INSTRUCCIONES ---
        # Ejecutar en terminal:
        # python manage.py initialize_db
        # Luego levantar servidor:
        # python manage.py runserver
