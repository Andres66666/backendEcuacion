from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import Rol, Permiso, Usuario, UsuarioRol, RolPermiso
from datetime import date

class Command(BaseCommand):
    help = 'Inicializa la base de datos con usuarios, roles y permisos para RBAC'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Inicializando base de datos con RBAC...")

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
            permiso, _ = Permiso.objects.get_or_create(nombre=nombre_permiso, defaults={'estado': True})
            permisos_objetos[nombre_permiso] = permiso

        # --- ASIGNAR PERMISOS A ROLES ---
        # Todos los permisos al rol Administrador
        for permiso in permisos_objetos.values():
            RolPermiso.objects.get_or_create(rol=admin_role, permiso=permiso)

        # Solo algunos permisos al rol Empleado
        permisos_empleado = ["ListarUsuarios", "ListarPermisos"]
        for nombre_permiso in permisos_empleado:
            RolPermiso.objects.get_or_create(rol=empleado_role, permiso=permisos_objetos[nombre_permiso])

        # --- CREAR USUARIO ADMINISTRADOR ---
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
        UsuarioRol.objects.get_or_create(usuario=admin_user, rol=admin_role)
        if created_admin:
            self.stdout.write(f"✅ Usuario administrador creado: {admin_user}")

        # --- CREAR USUARIO EMPLEADO ---
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
        UsuarioRol.objects.get_or_create(usuario=empleado_user, rol=empleado_role)
        if created_empleado:
            self.stdout.write(f"✅ Usuario empleado creado: {empleado_user}")

        self.stdout.write(self.style.SUCCESS("🎉 ¡Base de datos RBAC inicializada exitosamente!"))


        # --- INSTRUCCIONES ---
        # Ejecutar en terminal:
        # python manage.py initialize_db
        # Luego levantar servidor:
        # python manage.py runserver
