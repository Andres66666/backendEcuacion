from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import Rol, Permiso, Usuario, UsuarioRol, RolPermiso, Categorias
from datetime import date

class Command(BaseCommand):
    help = 'Inicializa la base de datos con datos básicos'

    def handle(self, *args, **kwargs):
        self.stdout.write("Inicializando base de datos...")

        # --- CREAR ROLES ---
        admin_role, _ = Rol.objects.get_or_create(nombre="Administrador", defaults={'estado': True})
        empleado_role, _ = Rol.objects.get_or_create(nombre="Empleado", defaults={'estado': True})

        # --- CREAR PERMISOS ---
        permisos_data = [
            "GestionDeUsuarios",
            "GestionDeProductos",
            "GestionDeReportes",
            "ListarRoles",
            "ListarPermisos",
            "ListarUsuarios",
            "ListarUsuarioRol",
            "ListarRolPermiso",
        ]

        permisos_objetos = {}
        for nombre_permiso in permisos_data:
            p, _ = Permiso.objects.get_or_create(nombre=nombre_permiso, defaults={'estado': True})
            permisos_objetos[nombre_permiso] = p

        # --- ASIGNAR PERMISOS A ROLES ---
        for permiso in permisos_objetos.values():
            RolPermiso.objects.get_or_create(rol=admin_role, permiso=permiso)

        # --- CREAR CATEGORÍAS ---
        categorias_data = [
            {"nombre": "Tabla", "descripcion": "Categoría para tablas"},
            {"nombre": "Listón", "descripcion": "Categoría para listones"},
            {"nombre": "Ripa", "descripcion": "Categoría para ripas"},
            {"nombre": "Mueble", "descripcion": "Categoría para muebles"},
            {"nombre": "Tijera", "descripcion": "Categoría para tijeras"},
        ]

        for cat in categorias_data:
            Categorias.objects.get_or_create(
                nombre=cat["nombre"],
                defaults={'descripcion': cat["descripcion"], 'estado': True}
            )

        # --- CREAR USUARIOS ---
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
                'imagen_url': "https://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/fnsesmm80hgwelhyzaie.jpg"
            }
        )
        if created_admin:
            self.stdout.write(f"Usuario administrador creado: {admin_user}")
        UsuarioRol.objects.get_or_create(usuario=admin_user, rol=admin_role)

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
                'imagen_url': "https://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/sample-image.jpg"
            }
        )
        if created_empleado:
            self.stdout.write(f"Usuario empleado creado: {empleado_user}")
        UsuarioRol.objects.get_or_create(usuario=empleado_user, rol=empleado_role)

        self.stdout.write(self.style.SUCCESS("Base de datos inicializada exitosamente!"))


        # --- INSTRUCCIONES ---
        # Ejecutar en terminal:
        # python manage.py initialize_db
        # Luego levantar servidor:
        # python manage.py runserver
