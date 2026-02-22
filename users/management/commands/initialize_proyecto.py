from django.core.management.base import BaseCommand
from decimal import Decimal, InvalidOperation
from datetime import date
from users.models import Proyecto, Modulo, GastoOperacion  # Asegúrate de que 'core' es la app donde están tus modelos
from users.models import Usuario  # Asume que el modelo Usuario está en 'users.models'


class Command(BaseCommand):
    help = "Inicializa la base de datos con datos de prueba para Proyecto, Modulo y GastoOperacion"

    def handle(self, *args, **kwargs):
        self.stdout.write("Inicializando datos de Proyecto, Módulo y Gasto de Operación...")

        try:
            # --- OBTENER USUARIO CREADOR ---
            # Asume que el usuario Administrador ya fue creado por el comando anterior
            creador = Usuario.objects.get(ci="13247291")
            self.stdout.write(f"Usuario creador encontrado: {creador.nombre} {creador.apellido}")
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR("Error: El usuario Administrador con CI '13247291' no existe. ¡Asegúrate de ejecutar initialize_db primero!"))
            return

        # --- 1. CREAR PROYECTO ---
        self.stdout.write("--- Creando Proyecto ---")
        proyecto_data = {
            "NombreProyecto": "CARPENTERAS",
            "carga_social": Decimal("55.00"),
            "iva_efectiva": Decimal("14.94"),
            "herramientas": Decimal("5.00"),
            "gastos_generales": Decimal("12.00"),
            "iva_tasa_nominal": Decimal("10.00"),
            "it": Decimal("3.00"),
            "iue": Decimal("25.00"),
            "ganancia": Decimal("50.00"),
            "a_costo_venta": Decimal("77.00"),
            "b_margen_utilidad": Decimal("10.00"),
            "porcentaje_global_100": Decimal("100.00"),
            "creado_por": creador,
            "modificado_por": creador,
        }

        proyecto, created_proyecto = Proyecto.objects.get_or_create(
            NombreProyecto=proyecto_data["NombreProyecto"],
            defaults=proyecto_data
        )

        if created_proyecto:
            self.stdout.write(f"Proyecto creado: {proyecto.NombreProyecto} (ID: {proyecto.id_proyecto})")
        else:
            self.stdout.write(f"Proyecto ya existe: {proyecto.NombreProyecto} (ID: {proyecto.id_proyecto}). Usando registro existente.")

        # --- 2. CREAR MÓDULO (basado en image_f66084.png) ---
        self.stdout.write("--- Creando Módulo ---")
        modulo_data = {
            "proyecto": proyecto,
            "codigo": "0018",
            "nombre": "TRAMO1",
            "creado_por": creador,
            "modificado_por": creador,
        }

        # La clave es usar el proyecto y código para get_or_create si unique_together está configurado
        modulo, created_modulo = Modulo.objects.get_or_create(
            proyecto=proyecto,
            codigo=modulo_data["codigo"],
            defaults={
                "nombre": modulo_data["nombre"],
                "creado_por": modulo_data["creado_por"],
                "modificado_por": modulo_data["modificado_por"],
            }
        )

        if created_modulo:
            self.stdout.write(f"Módulo creado: {modulo.codigo} - {modulo.nombre} (ID: {modulo.id})")
        else:
            self.stdout.write(f"Módulo ya existe: {modulo.codigo} - {modulo.nombre} (ID: {modulo.id}). Usando registro existente.")

        # --- 3. CREAR GASTO DE OPERACIÓN (basado en image_f660da.png) ---
        self.stdout.write("--- Creando GastoOperacion ---")
        gasto_data = {
            "identificador": proyecto,  # FK al Proyecto
            "modulo": modulo,  # FK al Módulo
            "descripcion": "TRAMO 12",
            "unidad": "M2",
            "cantidad": Decimal("165.00"),
            "precio_unitario": Decimal("3249.79"),
            "precio_literal": "Tres mil seiscientos setenta", # Nota: El literal no coincide con el costo_parcial de la imagen
            "creado_por": creador,
            "modificado_por": creador,
            # 'costo_parcial' se calculará en el método save
        }
        
        # Un valor único para el gasto (puedes usar la descripción y el proyecto, aunque no es estricto)
        # Vamos a usar get_or_create en base al identificador, modulo y descripcion
        gasto, created_gasto = GastoOperacion.objects.get_or_create(
            identificador=gasto_data["identificador"],
            modulo=gasto_data["modulo"],
            descripcion=gasto_data["descripcion"],
            defaults=gasto_data
        )

        if created_gasto:
            self.stdout.write(f"GastoOperacion creado: {gasto.descripcion} (Costo: {gasto.costo_parcial})")
        else:
            # Forzamos la actualización de los campos si ya existe (útil para pruebas)
            for key, value in gasto_data.items():
                setattr(gasto, key, value)
            gasto.save() # Guarda y recalcula costo_parcial
            self.stdout.write(f"GastoOperacion ya existe. Actualizado: {gasto.descripcion} (Costo: {gasto.costo_parcial})")


        self.stdout.write(
            self.style.SUCCESS(
                "¡Datos de Proyecto, Módulo y Gasto inicializados exitosamente!"
            )
        )

# --- INSTRUCCIONES ---
# Ejecutar en terminal:
# python manage.py initialize_proyecto
# Luego levantar servidor:
# python manage.py runserver
