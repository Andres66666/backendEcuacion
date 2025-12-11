
from decimal import Decimal, InvalidOperation
from django.db.models import Max
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
# =================== MODELOS ===================
from .models import (EquipoHerramienta, GastoOperacion, GastosGenerales, Modulo, Proyecto, ManoDeObra, Materiales, Usuario,)
# =================== SERIALIZERS ===================
from .serializers import ( EquipoHerramientaSerializer, GastoOperacionSerializer, GastosGeneralesSerializer, ModuloSerializer, ProyectoSerializer, ManoDeObraSerializer, MaterialesSerializer,)

# =====================================================
# === =============  seccion 2   === ==================
# =====================================================
class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            nombre_proyecto = data.get("NombreProyecto", "").strip()
            if not nombre_proyecto:
                return Response(
                    {"error": "El campo NombreProyecto es obligatorio."}, status=400
                )

            existente = Proyecto.objects.filter(
                NombreProyecto__iexact=nombre_proyecto
            ).first()
            if existente:
                return Response(
                    {
                        "mensaje": "Ya existe un proyecto con este nombre.",
                        "id_proyecto": existente.id_proyecto,
                        "NombreProyecto": existente.NombreProyecto,
                        "carga_social": existente.carga_social,
                        "iva_efectiva": existente.iva_efectiva,
                        "herramientas": existente.herramientas,
                        "gastos_generales": existente.gastos_generales,
                        "iva_tasa_nominal": existente.iva_tasa_nominal,
                        "it": existente.it,
                        "iue": existente.iue,
                        "ganancia": existente.ganancia,
                        "a_costo_venta": existente.a_costo_venta,
                        "b_margen_utilidad": existente.b_margen_utilidad,
                        "porcentaje_global_100": existente.porcentaje_global_100,
                    },
                    status=200,
                )

            id_usuario = data.get("creado_por")

            proyecto = Proyecto.objects.create(
                NombreProyecto=nombre_proyecto,
                carga_social=data.get("carga_social", 0),
                iva_efectiva=data.get("iva_efectiva", 0),
                herramientas=data.get("herramientas", 0),
                gastos_generales=data.get("gastos_generales", 0),
                iva_tasa_nominal=data.get("iva_tasa_nominal", 0),
                it=data.get("it", 0),
                iue=data.get("iue", 0),
                ganancia=data.get("ganancia", 0),
                a_costo_venta=data.get("a_costo_venta", 0),
                b_margen_utilidad=data.get("b_margen_utilidad", 0),
                porcentaje_global_100=data.get("porcentaje_global_100", 0),
            )

            serializer = self.get_serializer(proyecto)
            return Response(serializer.data, status=201)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            for field in [
                "NombreProyecto",
                "carga_social",
                "iva_efectiva",
                "herramientas",
                "gastos_generales",
                "iva_tasa_nominal",
                "it",
                "iue",
                "ganancia",
                "a_costo_venta",
                "b_margen_utilidad",
                "porcentaje_global_100",
            ]:
                if field in data:
                    setattr(
                        instance,
                        field,
                        (
                            data[field]
                            if field != "NombreProyecto"
                            else data[field].strip()
                        ),
                    )
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        identificador_id = self.request.query_params.get("identificador", None)
        if identificador_id is not None:
            queryset = queryset.filter(identificador__id_proyecto=identificador_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Importar modelos relacionados
        from .models import (
            GastoOperacion,
            Materiales,
            ManoDeObra,
            EquipoHerramienta,
            GastosGenerales,
        )

        # Buscar todos los gastos asociados al proyecto
        gastos = GastoOperacion.objects.filter(identificador=instance)

        for gasto in gastos:
            # Borrar hijos primero
            Materiales.objects.filter(id_gasto_operacion=gasto).delete()
            ManoDeObra.objects.filter(id_gasto_operacion=gasto).delete()
            EquipoHerramienta.objects.filter(id_gasto_operacion=gasto).delete()
            GastosGenerales.objects.filter(id_gasto_operacion=gasto).delete()
            # Luego borrar el gasto
            gasto.delete()

        # Finalmente borrar el proyecto
        instance.delete()

        return Response(
            {
                "mensaje": "Proyecto y todos sus registros asociados fueron eliminados correctamente."
            },
            status=status.HTTP_204_NO_CONTENT,
        )

class ModuloViewSet(viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        proyecto_id = self.request.query_params.get("proyecto", None)
        if proyecto_id:
            queryset = queryset.filter(proyecto_id=proyecto_id)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            proyecto_id = data.get("proyecto")  # ID del proyecto
            if not proyecto_id:
                return Response(
                    {"error": "Debe proporcionar un proyecto válido"}, status=400
                )

            proyecto = Proyecto.objects.get(id_proyecto=proyecto_id)
            
            modulo = Modulo.objects.create(
                proyecto=proyecto,
                codigo=data.get("codigo", "").strip(),
                nombre=data.get("nombre", "").strip(),
            )

            serializer = self.get_serializer(modulo)
            return Response(serializer.data, status=201)

        except Proyecto.DoesNotExist:
            return Response({"error": "Proyecto no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            for field in ["codigo", "nombre"]:
                if field in data:
                    setattr(instance, field, data[field].strip())

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

class GastoOperacionViewSet(viewsets.ModelViewSet):
    queryset = GastoOperacion.objects.all()
    serializer_class = GastoOperacionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Se espera una lista de ítems."}, status=400)

        identificador_id = None
        if data and isinstance(data[0], dict) and "identificador" in data[0]:
            identificador_data = data[0]["identificador"]
            if (
                isinstance(identificador_data, dict)
                and "id_proyecto" in identificador_data
            ):
                identificador_id = identificador_data["id_proyecto"]

        if identificador_id:
            try:
                identificador = Proyecto.objects.get(id_proyecto=identificador_id)
            except Proyecto.DoesNotExist:
                return Response(
                    {"error": "Identificador proporcionado no existe."}, status=400
                )
        else:
            return Response(
                {"error": "Debe proporcionar un proyecto válido"}, status=400
            )

        gastos_guardados = []
        for item_data in data:  # Cambiado: usa item_data para serializer
            # Usa el serializer para validar y mapear (incluyendo modulo_id → modulo)
            serializer = self.get_serializer(data=item_data)
            if serializer.is_valid():
                
                # Serializer guarda automáticamente (modulo_id se mapea a modulo)
                gasto = serializer.save(identificador=identificador)
                gastos_guardados.append(serializer.data)
            else:
                return Response({"error": serializer.errors}, status=400)

        return Response(
            {
                "mensaje": "Gastos creados correctamente.",
                "identificador_general": identificador.id_proyecto,
                "gastos": gastos_guardados,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)

    def save(self, *args, **kwargs):
        try:
            cantidad = Decimal(str(self.cantidad or "0"))
            precio = Decimal(str(self.precio_unitario or "0"))
            self.costo_parcial = cantidad * precio
        except (InvalidOperation, TypeError, ValueError):
            self.costo_parcial = Decimal("0")
        super().save(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()
        proyecto_id = self.request.query_params.get('identificador')
        
        if proyecto_id:
            return (queryset
                .filter(identificador__id_proyecto=proyecto_id)
                .select_related('modulo', 'identificador')  # Carga eager de relaciones
                .prefetch_related('gastosgenerales_set')  # Carga anticipada de gastos generales
                .annotate(
                    total_gastos_generales=Max('gastosgenerales__total')
                ))
        return queryset

    @action(detail=False, methods=["get"])
    def unidades(self, request):
        """Retorna lista única y ordenada de unidades (sin vacíos ni null)."""
        unidades_qs = (
            GastoOperacion.objects
            .exclude(unidad__isnull=True)
            .exclude(unidad__exact='')
            .values_list('unidad', flat=True)
            .distinct()
        )
        unidades = sorted(u for u in unidades_qs if u)
        return Response(unidades)

    # Nuevo endpoint
    @action(detail=False, methods=["get"])
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id:
            return Response({"error": "Debe proporcionar un proyecto"}, status=400)

        # Traer todos los materiales vinculados a gastos de operaciones de este proyecto
        Gasto_Operacion = (
            GastoOperacion.objects.filter(
                id_gasto_operacion__identificador__id_proyecto=proyecto_id
            )
            .values("descripcion")
            .annotate(ultimo_precio=Max("precio_unitario"))
            .order_by("descripcion")
        )
        return Response(list(Gasto_Operacion))

    @action(detail=False, methods=["post"])
    def actualizar_precio_descripcion(self, request):
        descripcion = request.data.get("descripcion")
        id_gasto_operacion = request.data.get("id_gasto_operacion")
        nuevo_precio = request.data.get("precio_unitario")

        if not descripcion or not id_gasto_operacion or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        # Obtener el proyecto asociado al gasto de operación
        try:
            gasto = GastoOperacion.objects.get(id=id_gasto_operacion)
        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=404)

        # Actualizar todos los materiales del mismo proyecto y misma descripción
        Gasto_Operacion = GastoOperacion.objects.filter(
            id_gasto_operacion__identificador=gasto.identificador,
            descripcion__iexact=descripcion,
        )

        if not Gasto_Operacion.exists():
            return Response(
                {"error": "No se encontraron materiales para actualizar"}, status=404
            )

        Gasto_Operacion.update(precio_unitario=nuevo_precio)

        return Response(
            {
                "success": True,
                "descripcion": descripcion,
                "nuevo_precio": nuevo_precio,
                "actualizados": Gasto_Operacion.count(),
            }
        )
    
# =====================================================
# === =============  seccion 3   === ==================
# =====================================================

class MaterialesViewSet(viewsets.ModelViewSet):
    queryset = Materiales.objects.all()
    serializer_class = MaterialesSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            id_gasto = data.get("id_gasto_operacion")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"}, status=400
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)

            material = Materiales.objects.create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data.get("descripcion"),
                unidad=data.get("unidad"),
                cantidad=data.get("cantidad", 0),
                precio_unitario=data.get("precio_unitario", 0),
                total=data.get("total", 0),
            )

            serializer = self.get_serializer(material)
            return Response(serializer.data, status=201)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
      
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                gasto_operacion = GastoOperacion.objects.get(
                    id=data["id_gasto_operacion"]
                )
                instance.id_gasto_operacion = gasto_operacion

            if "descripcion" in data:
                instance.descripcion = data["descripcion"]

            if "unidad" in data:
                instance.unidad = data["unidad"]

            if "cantidad" in data:
                instance.cantidad = data["cantidad"]

            if "precio_unitario" in data:
                instance.precio_unitario = data["precio_unitario"]

            if "total" in data:
                instance.total = data["total"]

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset

    @action(detail=False, methods=["get"])
    def unidades(self, request):
        # Trae unidades únicas (distinct)
        unidades = (
            Materiales.objects.values_list("unidad", flat=True)
            .distinct()
            .order_by("unidad")
        )
        return Response(unidades)

    # Nuevo endpoint
    @action(detail=False, methods=["get"])
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id:
            return Response({"error": "Debe proporcionar un proyecto"}, status=400)

        # Traer todos los materiales vinculados a gastos de operaciones de este proyecto
        materiales = (
            Materiales.objects.filter(
                id_gasto_operacion__identificador__id_proyecto=proyecto_id
            )
            .values("descripcion")
            .annotate(ultimo_precio=Max("precio_unitario"))
            .order_by("descripcion")
        )
        return Response(list(materiales))

    @action(detail=False, methods=["post"])
    def actualizar_precio_descripcion(self, request):
        descripcion = request.data.get("descripcion")
        id_gasto_operacion = request.data.get("id_gasto_operacion")
        nuevo_precio = request.data.get("precio_unitario")

        if not descripcion or not id_gasto_operacion or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        # Obtener el proyecto asociado al gasto de operación
        try:
            gasto = GastoOperacion.objects.get(id=id_gasto_operacion)
        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=404)

        # Actualizar todos los materiales del mismo proyecto y misma descripción
        materiales = Materiales.objects.filter(
            id_gasto_operacion__identificador=gasto.identificador,
            descripcion__iexact=descripcion,
        )

        if not materiales.exists():
            return Response(
                {"error": "No se encontraron materiales para actualizar"}, status=404
            )

        materiales.update(precio_unitario=nuevo_precio)

        return Response(
            {
                "success": True,
                "descripcion": descripcion,
                "nuevo_precio": nuevo_precio,
                "actualizados": materiales.count(),
            }
        )

class ManoDeObraViewSet(viewsets.ModelViewSet):
    queryset = ManoDeObra.objects.all()
    serializer_class = ManoDeObraSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            id_gasto = data.get("id_gasto_operacion")
            id_usuario = data.get("creado_por")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"}, status=400
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)

            mano = ManoDeObra.objects.create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data.get("descripcion"),
                unidad=data.get("unidad"),
                cantidad=data.get("cantidad", 0),
                precio_unitario=data.get("precio_unitario", 0),
                total=data.get("total", 0),
            )

            serializer = self.get_serializer(mano)
            return Response(serializer.data, status=201)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                gasto_operacion = GastoOperacion.objects.get(
                    id=data["id_gasto_operacion"]
                )
                instance.id_gasto_operacion = gasto_operacion

            if "descripcion" in data:
                instance.descripcion = data["descripcion"]

            if "unidad" in data:
                instance.unidad = data["unidad"]

            if "cantidad" in data:
                instance.cantidad = data["cantidad"]

            if "precio_unitario" in data:
                instance.precio_unitario = data["precio_unitario"]

            if "total" in data:
                instance.total = data["total"]

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset

    @action(detail=False, methods=["get"])
    def unidades(self, request):
        # Trae unidades únicas (distinct)
        unidades = (
            ManoDeObra.objects.values_list("unidad", flat=True)
            .distinct()
            .order_by("unidad")
        )
        return Response(unidades)

    # Nuevo endpoint
    @action(detail=False, methods=["get"])
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id:
            return Response({"error": "Debe proporcionar un proyecto"}, status=400)

        # Traer todos los materiales vinculados a gastos de operaciones de este proyecto
        mano_de_obra = (
            ManoDeObra.objects.filter(
                id_gasto_operacion__identificador__id_proyecto=proyecto_id
            )
            .values("descripcion")
            .annotate(ultimo_precio=Max("precio_unitario"))
            .order_by("descripcion")
        )
        return Response(list(mano_de_obra))

    @action(detail=False, methods=["post"])
    def actualizar_precio_descripcion(self, request):
        descripcion = request.data.get("descripcion")
        id_gasto_operacion = request.data.get("id_gasto_operacion")
        nuevo_precio = request.data.get("precio_unitario")

        if not descripcion or not id_gasto_operacion or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)
        try:
            gasto = GastoOperacion.objects.get(id=id_gasto_operacion)
        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=404)
        # Actualizar todos los registros de mano de obra del mismo proyecto y misma descripción
        mano_obra_items = ManoDeObra.objects.filter(
            id_gasto_operacion__identificador=gasto.identificador,
            descripcion__iexact=descripcion,
        )
        if not mano_obra_items.exists():
            return Response(
                {"error": "No se encontraron registros para actualizar"}, status=404
            )
        mano_obra_items.update(precio_unitario=nuevo_precio)
        return Response(
            {
                "success": True,
                "descripcion": descripcion,
                "nuevo_precio": nuevo_precio,
                "actualizados": mano_obra_items.count(),
            }
        )

class EquipoHerramientaViewSet(viewsets.ModelViewSet):
    queryset = EquipoHerramienta.objects.all()
    serializer_class = EquipoHerramientaSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            id_gasto = data.get("id_gasto_operacion")
            id_usuario = data.get("creado_por")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"}, status=400
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)

            equipo = EquipoHerramienta.objects.create(
                id_gasto_operacion=gasto_operacion,
                descripcion=data.get("descripcion"),
                unidad=data.get("unidad"),
                cantidad=data.get("cantidad", 0),
                precio_unitario=data.get("precio_unitario", 0),
                total=data.get("total", 0),
            )

            serializer = self.get_serializer(equipo)
            return Response(serializer.data, status=201)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                gasto_operacion = GastoOperacion.objects.get(
                    id=data["id_gasto_operacion"]
                )
                instance.id_gasto_operacion = gasto_operacion

            if "descripcion" in data:
                instance.descripcion = data["descripcion"]

            if "unidad" in data:
                instance.unidad = data["unidad"]

            if "cantidad" in data:
                instance.cantidad = data["cantidad"]

            if "precio_unitario" in data:
                instance.precio_unitario = data["precio_unitario"]

            if "total" in data:
                instance.total = data["total"]

           

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=400)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset

    @action(detail=False, methods=["get"])
    def unidades(self, request):
        unidades = (
            EquipoHerramienta.objects.values_list("unidad", flat=True)
            .distinct()
            .order_by("unidad")
        )
        return Response(unidades)

        # Nuevo endpoint

    @action(detail=False, methods=["get"])
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id:
            return Response({"error": "Debe proporcionar un proyecto"}, status=400)

        equipo_herramienta = (
            EquipoHerramienta.objects.filter(
                id_gasto_operacion__identificador__id_proyecto=proyecto_id
            )
            .values("descripcion")
            .annotate(ultimo_precio=Max("precio_unitario"))
            .order_by("descripcion")
        )
        return Response(list(equipo_herramienta))

    @action(detail=False, methods=["post"])
    def actualizar_precio_descripcion(self, request):
        descripcion = request.data.get("descripcion")
        id_gasto_operacion = request.data.get("id_gasto_operacion")
        nuevo_precio = request.data.get("precio_unitario")

        if not descripcion or not id_gasto_operacion or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        # Obtener el proyecto asociado al gasto de operación
        try:
            gasto = GastoOperacion.objects.get(id=id_gasto_operacion)
        except GastoOperacion.DoesNotExist:
            return Response({"error": "GastoOperacion no encontrado"}, status=404)

        # Actualizar todos los equipos del mismo proyecto y misma descripción
        equipo_herramienta = EquipoHerramienta.objects.filter(
            id_gasto_operacion__identificador=gasto.identificador,
            descripcion__iexact=descripcion,
        )

        if not equipo_herramienta.exists():
            return Response(
                {"error": "No se encontraron equipos para actualizar"},
                status=404,
            )

        equipo_herramienta.update(precio_unitario=nuevo_precio)

        return Response(
            {
                "success": True,
                "descripcion": descripcion,
                "nuevo_precio": nuevo_precio,
                "actualizados": equipo_herramienta.count(),
            }
        )

class GastosGeneralesViewSet(viewsets.ModelViewSet):
    queryset = GastosGenerales.objects.all()
    serializer_class = GastosGeneralesSerializer

    def create(self, request, *args, **kwargs):
        print("Datos recibidos:", request.data)
        data = request.data.copy()

        try:
            id_gasto = data.get("id_gasto_operacion")

            if not id_gasto:
                return Response(
                    {"error": "id_gasto_operacion es requerido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            gasto_operacion = GastoOperacion.objects.get(id=id_gasto)
            usuario = None
            
            gasto_general = GastosGenerales.objects.create(
                id_gasto_operacion=gasto_operacion,
                total=data.get("total", 0),
                creado_por=usuario,
            )

            serializer = self.get_serializer(gasto_general)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except GastoOperacion.DoesNotExist:
            return Response(
                {"error": "GastoOperacion no encontrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()

            if "id_gasto_operacion" in data:
                try:
                    gasto_operacion = GastoOperacion.objects.get(
                        id=data["id_gasto_operacion"]
                    )
                    instance.id_gasto_operacion = gasto_operacion
                except GastoOperacion.DoesNotExist:
                    return Response(
                        {"error": "GastoOperacion no encontrado"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if "total" in data:
                instance.total = data["total"]

            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except GastosGenerales.DoesNotExist:
            return Response(
                {"error": "Registro no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = super().get_queryset()
        id_gasto = self.request.query_params.get("id_gasto_operacion")
        if id_gasto:
            queryset = queryset.filter(id_gasto_operacion=id_gasto)
        return queryset

    @action(detail=False, methods=['get'])
    def totals_por_proyecto(self, request):
        proyecto_id = request.query_params.get('proyecto') or request.query_params.get('identificador')
        if not proyecto_id:
            return Response({"error": "Debe proporcionar un proyecto"}, status=400)

        totals_qs = (
            GastosGenerales.objects
            .filter(id_gasto_operacion__identificador__id_proyecto=proyecto_id)
            .values('id_gasto_operacion')
            .annotate(total=Max('total'))
        )

        # Devolver mapa id_gasto_operacion -> total
        result = {str(t['id_gasto_operacion']): t['total'] for t in totals_qs}
        return Response(result)
