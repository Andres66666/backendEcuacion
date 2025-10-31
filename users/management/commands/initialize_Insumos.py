from django.core.management.base import BaseCommand
from decimal import Decimal
# Asegúrate de importar los modelos desde su ubicación correcta
from users.models import GastoOperacion, Materiales, ManoDeObra, EquipoHerramienta 
from users.models import Usuario


class Command(BaseCommand):
    help = "Inicializa la base de datos con datos de prueba para Materiales, ManoDeObra y EquipoHerramienta"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Inicializando datos detallados de Operación (Materiales, ManoDeObra, EquipoHerramienta)...")

        try:
            # --- 1. OBTENER ENTIDADES REQUERIDAS ---
            creador = Usuario.objects.get(ci="13247291")
            # Asumimos que el GastoOperacion de prueba con ID=1 existe
            gasto_operacion = GastoOperacion.objects.get(id=1)
            self.stdout.write(f"✅ Encontrados Usuario Creador y GastoOperacion ID: {gasto_operacion.id}")
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Error: El usuario Administrador no existe."))
            return
        except GastoOperacion.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Error: El GastoOperacion con ID=1 no existe. Asegúrate de crearlo primero."))
            return

        # --- 2. REGISTRAR MATERIALES (basado en image_f6683c.png) ---
        self.stdout.write("\n--- Registrando Materiales ---")
        materiales_data = [
            {
                "descripcion": "CEMENTO",
                "unidad": "KG",
                "cantidad": Decimal("20.00"),
                "precio_unitario": Decimal("50.00"),
                "total": Decimal("1000.00"),
            },
            {
                "descripcion": "ARENA",
                "unidad": "M3",
                "cantidad": Decimal("4.00"),
                "precio_unitario": Decimal("190.00"),
                "total": Decimal("760.00"),
            },
        ]

        for data in materiales_data:
            material, created = Materiales.objects.get_or_create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data["descripcion"],
                defaults={
                    **data,
                    "creado_por": creador,
                    "modificado_por": creador,
                }
            )
            if created:
                self.stdout.write(f"✅ Material creado: {material.descripcion}")
            else:
                self.stdout.write(f"ℹ️ Material ya existe: {material.descripcion}. Saltando.")

        # --- 3. REGISTRAR MANO DE OBRA (basado en image_f6687f.png) ---
        self.stdout.write("\n--- Registrando Mano De Obra ---")
        manodeobra_data = [
            {
                "descripcion": "OBRERO",
                "unidad": "HR",
                "cantidad": Decimal("10.00"),
                "precio_unitario": Decimal("30.00"),
                "total": Decimal("300.00"),
            },
            {
                "descripcion": "AYUDANTE",
                "unidad": "H", # Nota: 'H' en la imagen, asumimos que es una unidad válida
                "cantidad": Decimal("5.00"),
                "precio_unitario": Decimal("25.00"),
                "total": Decimal("125.00"),
            },
        ]

        for data in manodeobra_data:
            mano_obra, created = ManoDeObra.objects.get_or_create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data["descripcion"],
                defaults={
                    **data,
                    "creado_por": creador,
                    "modificado_por": creador,
                }
            )
            if created:
                self.stdout.write(f"✅ Mano de Obra creada: {mano_obra.descripcion}")
            else:
                self.stdout.write(f"ℹ️ Mano de Obra ya existe: {mano_obra.descripcion}. Saltando.")
        
        # --- 4. REGISTRAR EQUIPO/HERRAMIENTA (basado en image_f66c3b.png) ---
        self.stdout.write("\n--- Registrando Equipo/Herramienta ---")
        equipo_data = [
            {
                "descripcion": "COMPACTADORA",
                "unidad": "HR",
                "cantidad": Decimal("19.00"),
                "precio_unitario": Decimal("5.00"),
                "total": Decimal("95.00"),
            },
            {
                "descripcion": "MEZCLADORA",
                "unidad": "HR",
                "cantidad": Decimal("50.00"),
                "precio_unitario": Decimal("5.00"),
                "total": Decimal("250.00"),
            },
        ]

        for data in equipo_data:
            equipo, created = EquipoHerramienta.objects.get_or_create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data["descripcion"],
                defaults={
                    **data,
                    "creado_por": creador,
                    "modificado_por": creador,
                }
            )
            if created:
                self.stdout.write(f"✅ Equipo/Herramienta creado: {equipo.descripcion}")
            else:
                self.stdout.write(f"ℹ️ Equipo/Herramienta ya existe: {equipo.descripcion}. Saltando.")

        self.stdout.write(
            self.style.SUCCESS(
                "🎉 ¡Detalles de Operación (Materiales, ManoDeObra, EquipoHerramienta) inicializados exitosamente!"
            )
        )
# --- INSTRUCCIONES ---
# Ejecutar en terminal:
# python manage.py initialize_Insumos
# Luego levantar servidor:
# python manage.py runserver
