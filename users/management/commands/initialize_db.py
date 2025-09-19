from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import Rol, Permiso, Usuario, UsuarioRol, RolPermiso
from datetime import date


class Command(BaseCommand):
    help = "Inicializa la base de datos con usuarios, roles y permisos para RBAC"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Inicializando base de datos con RBAC...")

        # --- CREAR ROLES ---
        admin_role, _ = Rol.objects.get_or_create(
            nombre="Administrador", defaults={"estado": True}
        )
        colaborador_role, _ = Rol.objects.get_or_create(
            nombre="Colaborador", defaults={"estado": True}
        )
        asistente_role, _ = Rol.objects.get_or_create(
            nombre="Asistente", defaults={"estado": True}
        )

        # --- CREAR PERMISOS ---
        permisos_data = [
            # Gestión de Usuarios
            "GestionDeUsuarios",
            "ListarRoles",
            "ListarPermisos",
            "ListarUsuarios",
            "ListarUsuarioRol",
            "ListarRolPermiso",
            # Operaciones
            "Operaciones",
            "GastosOperaciones",
            # Reportes
            "Reportes",
            "ReporteSQL",
            "ReporteXSS",
            "ReporteCSRF",
            "ReporteDoS",
            "ReporteKeylogger",
            "ReporteAuditoria",
            "ReporteIAGeneral",
        ]

        permisos_objetos = {}
        for nombre_permiso in permisos_data:
            permiso, _ = Permiso.objects.get_or_create(
                nombre=nombre_permiso, defaults={"estado": True}
            )
            permisos_objetos[nombre_permiso] = permiso

        # --- ASIGNAR PERMISOS A ROLES ---
        # Administrador → todos los permisos
        for permiso in permisos_objetos.values():
            RolPermiso.objects.get_or_create(rol=admin_role, permiso=permiso)

        # Colaborador → solo acceso a Operaciones
        permisos_colaborador = ["Operaciones", "GastosOperaciones"]
        for nombre_permiso in permisos_colaborador:
            RolPermiso.objects.get_or_create(
                rol=colaborador_role, permiso=permisos_objetos[nombre_permiso]
            )

        # Asistente → solo acceso a Reportes
        permisos_asistente = [
            "Reportes",
            "ReporteSQL",
            "ReporteXSS",
            "ReporteCSRF",
            "ReporteDoS",
            "ReporteKeylogger",
            "ReporteAuditoria",
            "ReporteIAGeneral",
        ]
        for nombre_permiso in permisos_asistente:
            RolPermiso.objects.get_or_create(
                rol=asistente_role, permiso=permisos_objetos[nombre_permiso]
            )

        # --- CREAR USUARIOS ---
        usuarios_data = [
            {
                "ci": "13247291",
                "nombre": "Andres Benito",
                "apellido": "Yucra",
                "fecha_nacimiento": date(1998, 11, 6),
                "telefono": "72937437",
                "correo": "benitoandrescalle035@gmail.com",
                "password": "Andres1234*",
                "rol": admin_role,
                "imagen_url": "https://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/fnsesmm80hgwelhyzaie.jpg",
            },
            {
                "ci": "87654321",
                "nombre": "Juan Carlos",
                "apellido": "Pérez",
                "fecha_nacimiento": date(1990, 5, 15),
                "telefono": "78945612",
                "correo": "juanperez@example.com",
                "password": "Colaborador123*",
                "rol": colaborador_role,
                "imagen_url": "https://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/sample-image.jpg",
            },
            {
                "ci": "87654322",
                "nombre": "Luis",
                "apellido": "Ramirez",
                "fecha_nacimiento": date(1995, 7, 10),
                "telefono": "70123456",
                "correo": "luis.ramirez@example.com",
                "password": "Asistente123*",
                "rol": asistente_role,
                "imagen_url": "https://res.cloudinary.com/dlrpns8z7/image/upload/v1743595809/sample-image.jpg",
            },
        ]

        for u in usuarios_data:
            user, created = Usuario.objects.get_or_create(
                ci=u["ci"],
                defaults={
                    "nombre": u["nombre"],
                    "apellido": u["apellido"],
                    "fecha_nacimiento": u["fecha_nacimiento"],
                    "telefono": u["telefono"],
                    "correo": u["correo"],
                    "password": make_password(u["password"]),
                    "estado": True,
                    "imagen_url": u["imagen_url"],
                },
            )
            UsuarioRol.objects.get_or_create(usuario=user, rol=u["rol"])
            if created:
                self.stdout.write(
                    f"✅ Usuario creado: {user} con rol {u['rol'].nombre}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                "🎉 ¡Base de datos RBAC inicializada exitosamente con roles, permisos y usuarios!"
            )
        )

        # --- INSTRUCCIONES ---
        # Ejecutar en terminal:
        # python manage.py initialize_db
        # Luego levantar servidor:
        # python manage.py runserver
