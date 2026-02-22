
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db.models import Max
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
# =================== MODELOS ===================
from .models import (EquipoHerramienta, GastoOperacion, GastosGenerales, Modulo, Proyecto, ManoDeObra, Materiales, Usuario,)
# =================== SERIALIZERS ===================
from .serializers import ( EquipoHerramientaSerializer, GastoOperacionSerializer, GastosGeneralesSerializer, ModuloSerializer, ProyectoSerializer, ManoDeObraSerializer, MaterialesSerializer,)
from django.db.models import Sum 
from decimal import Decimal, ROUND_HALF_UP
from django.db.models.functions import Trim, Upper
from django.db.models import F



def redondear2(valor) -> Decimal:
    try:
        return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")

def to_decimal(valor) -> Decimal:
    try:
        return Decimal(str(valor))
    except Exception:
        return Decimal("0")

def recalcular_item_gastos_generales(item: GastoOperacion) -> GastosGenerales:
    """
    Recalcula y guarda el registro de GastosGenerales (1 por item).
    IMPORTANTE: retorna el objeto GastosGenerales para usarlo en endpoints.
    """

    proyecto = item.modulo.proyecto

    gastos_generales_pct = to_decimal(proyecto.gastos_generales or 0)
    margen_utilidad_pct = to_decimal(proyecto.margen_utilidad or 0)
    iva_tasa_nominal_pct = to_decimal(proyecto.iva_tasa_nominal or 0)
    carga_social_pct = to_decimal(proyecto.carga_social or 0)
    iva_efectiva_pct = to_decimal(proyecto.iva_efectiva or 0)
    herramientas_pct = to_decimal(proyecto.herramientas or 0)

    subtotal_materiales = (
        Materiales.objects.filter(gasto_operacion=item)
        .aggregate(s=Sum("total"))["s"] or 0
    )
    subtotal_mano_obra = (
        ManoDeObra.objects.filter(gasto_operacion=item)
        .aggregate(s=Sum("total"))["s"] or 0
    )
    subtotal_equipos = (
        EquipoHerramienta.objects.filter(gasto_operacion=item)
        .aggregate(s=Sum("total"))["s"] or 0
    )

    subtotal_materiales = to_decimal(subtotal_materiales)
    subtotal_mano_obra = to_decimal(subtotal_mano_obra)
    subtotal_equipos = to_decimal(subtotal_equipos)

    # 1) Mano de obra ajustada
    cargas_mano_obra = redondear2(subtotal_mano_obra * carga_social_pct / Decimal("100"))
    iva_mano_obra = redondear2((subtotal_mano_obra + cargas_mano_obra) * iva_efectiva_pct / Decimal("100"))
    total_mano_obra = redondear2(subtotal_mano_obra + cargas_mano_obra + iva_mano_obra)

    # 2) Equipos ajustados con herramientas (% mano de obra total)
    herramientas_monto = redondear2(total_mano_obra * herramientas_pct / Decimal("100"))
    total_equipos_ajustado = redondear2(subtotal_equipos + herramientas_monto)

    # 3) Subtotal previo
    subtotal_previo = redondear2(subtotal_materiales + total_mano_obra + total_equipos_ajustado)

    # 4) Gastos generales (%)
    gastos_generales_monto = redondear2(subtotal_previo * gastos_generales_pct / Decimal("100"))
    suma_hasta_gg = redondear2(subtotal_previo + gastos_generales_monto)

    # 5) Valor agregado (margen utilidad) usando iva tasa nominal
    base = Decimal("100") - iva_tasa_nominal_pct
    if (base - margen_utilidad_pct) > 0:
        valor_agregado = redondear2(suma_hasta_gg * margen_utilidad_pct / (base - margen_utilidad_pct))
    else:
        valor_agregado = Decimal("0.00")

    total_final = redondear2(suma_hasta_gg + valor_agregado)

    # Guardar/actualizar: 1 solo registro por item
    gg, _ = GastosGenerales.objects.update_or_create(
        gasto_operacion=item,
        defaults={
            "totalgastosgenerales": suma_hasta_gg,
            "total": total_final,
        },
    )
    return gg


def recalcular_proyecto(proyecto: Proyecto) -> None:
    """
    Recalcula todos los items de un proyecto (sin devolver conteo).
    """
    items = (
        GastoOperacion.objects
        .filter(modulo__proyecto=proyecto)
        .select_related("modulo", "modulo__proyecto")
    )
    for item in items:
        recalcular_item_gastos_generales(item)


def recalcular_proyecto_completo(proyecto: Proyecto) -> int:
    """
    Recalcula todos los items y retorna cuántos items fueron recalculados.
    """
    items = (
        GastoOperacion.objects
        .filter(modulo__proyecto=proyecto)
        .select_related("modulo", "modulo__proyecto")
    )
    count = 0
    for item in items:
        recalcular_item_gastos_generales(item)
        count += 1
    return count
# =====================================================
# === =============  seccion 2   === ==================
# =====================================================

class ProyectoViewSet(viewsets.ModelViewSet):
   
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            return qs.filter(creado_por=self.request.user)
        usuario_id = self.request.query_params.get("usuario_id")
        if not usuario_id:
            return qs.none()
        try:
            return qs.filter(creado_por_id=int(usuario_id))
        except ValueError:
            return qs.none()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # determinar usuario
        if getattr(request, "user", None) and request.user.is_authenticated:
            usuario = request.user
        else:
            usuario_id = data.get("creado_por")
            if not usuario_id:
                return Response({"error": "Usuario no identificado"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                usuario = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                return Response({"error": "Usuario no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

        nombre = (data.get("NombreProyecto") or "").strip()
        if not nombre:
            return Response({"error": "El campo NombreProyecto es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        existe = Proyecto.objects.filter(creado_por=usuario, NombreProyecto__iexact=nombre).exists()
        if existe:
            return Response({"error": "Ya existe un proyecto con este nombre para este usuario."},
                            status=status.HTTP_400_BAD_REQUEST)

        data["NombreProyecto"] = nombre
        data["creado_por"] = usuario.id  

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        proyecto = serializer.save(creado_por=usuario)

        return Response(self.get_serializer(proyecto).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        campos_calculo = {
            "carga_social",
            "iva_efectiva",
            "herramientas",
            "gastos_generales",
            "iva_tasa_nominal",
            "margen_utilidad",
        }
        recalcular = any(c in data for c in campos_calculo)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        proyecto = serializer.save()

        if recalcular:
            recalcular_proyecto(proyecto.id_proyecto)

        return Response(self.get_serializer(proyecto).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete() 
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=["post"])
    def duplicar(self, request, pk=None):
        proyecto = self.get_object()

        with transaction.atomic():
            # 1) nuevo proyecto
            nuevo = Proyecto.objects.create(
                NombreProyecto=f"{proyecto.NombreProyecto} (COPIA)",
                carga_social=proyecto.carga_social,
                iva_efectiva=proyecto.iva_efectiva,
                herramientas=proyecto.herramientas,
                gastos_generales=proyecto.gastos_generales,
                iva_tasa_nominal=proyecto.iva_tasa_nominal,
                it=proyecto.it,
                iue=proyecto.iue,
                ganancia=proyecto.ganancia,
                margen_utilidad=proyecto.margen_utilidad,
                creado_por=proyecto.creado_por,
            )

            # 2) copiar módulos
            map_modulos = {}
            for mod in proyecto.modulos.all().order_by("id"):
                mod_nuevo = Modulo.objects.create(
                    proyecto=nuevo,
                    codigo=mod.codigo,
                    nombre=mod.nombre
                )
                map_modulos[mod.id] = mod_nuevo

            # 3) copiar gastos + hijos
            gastos = GastoOperacion.objects.filter(modulo__proyecto=proyecto).order_by("id")
            for go in gastos:
                go_nuevo = GastoOperacion.objects.create(
                    modulo=map_modulos[go.modulo_id],
                    descripcion=go.descripcion,
                    unidad=go.unidad,
                    cantidad=go.cantidad,
                    precio_unitario=go.precio_unitario,
                    costo_parcial=go.costo_parcial,
                )

                # materiales
                for m in go.materiales.all():
                    Materiales.objects.create(
                        gasto_operacion=go_nuevo,
                        descripcion=m.descripcion,
                        unidad=m.unidad,
                        cantidad=m.cantidad,
                        precio_unitario=m.precio_unitario,
                        total=m.total,
                    )

                # mano de obra
                for mo in go.mano_obra.all():
                    ManoDeObra.objects.create(
                        gasto_operacion=go_nuevo,
                        descripcion=mo.descripcion,
                        unidad=mo.unidad,
                        cantidad=mo.cantidad,
                        precio_unitario=mo.precio_unitario,
                        total=mo.total,
                    )

                # equipos
                for e in go.equipos.all():
                    EquipoHerramienta.objects.create(
                        gasto_operacion=go_nuevo,
                        descripcion=e.descripcion,
                        unidad=e.unidad,
                        cantidad=e.cantidad,
                        precio_unitario=e.precio_unitario,
                        total=e.total,
                    )

                # gastos generales
                for gg in go.gastos_generales.all():
                    GastosGenerales.objects.create(
                        gasto_operacion=go_nuevo,
                        totalgastosgenerales=gg.totalgastosgenerales,
                        total=gg.total
                    )

        return Response({"nuevo_id": nuevo.id_proyecto}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        campos_calculo = {
            "carga_social",
            "iva_efectiva",
            "herramientas",
            "gastos_generales",
            "iva_tasa_nominal",
            "margen_utilidad",
        }
        recalcular = any(c in data for c in campos_calculo)

        serializer = self.get_serializer(instance, data=data, partial=False)
        serializer.is_valid(raise_exception=True)
        proyecto = serializer.save()

        if recalcular:
            recalcular_proyecto(proyecto)  # ✅ objeto, no id

        return Response(self.get_serializer(proyecto).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        campos_calculo = {
            "carga_social",
            "iva_efectiva",
            "herramientas",
            "gastos_generales",
            "iva_tasa_nominal",
            "margen_utilidad",
        }
        recalcular = any(c in data for c in campos_calculo)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        proyecto = serializer.save()

        if recalcular:
            recalcular_proyecto(proyecto)  # ✅ objeto, no id

        return Response(self.get_serializer(proyecto).data, status=status.HTTP_200_OK)
class ModuloViewSet(viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            if getattr(self.request, "user", None) and self.request.user.is_authenticated:
                return qs.filter(proyecto__creado_por=self.request.user)

            usuario_id = self.request.query_params.get("usuario_id")
            if not usuario_id:
                return qs.none()

            try:
                return qs.filter(proyecto__creado_por_id=int(usuario_id))
            except ValueError:
                return qs.none()

        # ========= LIST (GET /modulos/?proyecto=) =========
        proyecto_id = self.request.query_params.get("proyecto")
        if not proyecto_id or proyecto_id == "undefined":
            return qs.none()

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return qs.none()

        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            return qs.filter(proyecto_id=proyecto_id, proyecto__creado_por=self.request.user)

        usuario_id = self.request.query_params.get("usuario_id")
        if not usuario_id:
            return qs.none()

        try:
            usuario_id = int(usuario_id)
        except ValueError:
            return qs.none()

        return qs.filter(proyecto_id=proyecto_id, proyecto__creado_por_id=usuario_id)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        proyecto_id = data.get("proyecto")
        if not proyecto_id:
            return Response({"error": "Debe proporcionar el proyecto"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "Proyecto inválido"}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(request, "user", None) and request.user.is_authenticated:
            proyecto = Proyecto.objects.filter(id_proyecto=proyecto_id, creado_por=request.user).first()
        else:
            usuario_id = request.query_params.get("usuario_id") or data.get("usuario_id")
            if not usuario_id:
                return Response({"error": "Usuario no identificado"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return Response({"error": "Usuario inválido"}, status=status.HTTP_400_BAD_REQUEST)

            proyecto = Proyecto.objects.filter(id_proyecto=proyecto_id, creado_por_id=usuario_id).first()

        if not proyecto:
            return Response({"error": "Proyecto no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)

        codigo = (data.get("codigo") or "").strip()
        nombre = (data.get("nombre") or "").strip()

        if not codigo:
            return Response({"error": "El campo codigo es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
        if not nombre:
            return Response({"error": "El campo nombre es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)

        if Modulo.objects.filter(proyecto=proyecto, codigo__iexact=codigo).exists():
            return Response({"error": "Ya existe un módulo con ese código en este proyecto"},
                            status=status.HTTP_400_BAD_REQUEST)

        modulo = Modulo.objects.create(proyecto=proyecto, codigo=codigo, nombre=nombre)
        return Response(self.get_serializer(modulo).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        data = request.data.copy()

        if getattr(request, "user", None) and request.user.is_authenticated:
            if instance.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        if "codigo" in data:
            data["codigo"] = (data["codigo"] or "").strip()
        if "nombre" in data:
            data["nombre"] = (data["nombre"] or "").strip()

        serializer = self.get_serializer(instance, data=data, partial=False)
        serializer.is_valid(raise_exception=True)
        modulo = serializer.save()

        return Response(self.get_serializer(modulo).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        if getattr(request, "user", None) and request.user.is_authenticated:
            if instance.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        if "codigo" in data:
            data["codigo"] = (data["codigo"] or "").strip()
        if "nombre" in data:
            data["nombre"] = (data["nombre"] or "").strip()

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        modulo = serializer.save()

        return Response(self.get_serializer(modulo).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if getattr(request, "user", None) and request.user.is_authenticated:
            if instance.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        proyecto = instance.proyecto  # ✅ objeto proyecto
        instance.delete()

        try:
            recalcular_proyecto(proyecto)  # ✅ objeto
        except Exception:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)


class GastoOperacionViewSet(viewsets.ModelViewSet):
    queryset = GastoOperacion.objects.all()
    serializer_class = GastoOperacionSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("modulo", "modulo__proyecto")

        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            qs = qs.filter(modulo__proyecto__creado_por=self.request.user)
        else:
            usuario_id = self.request.query_params.get("usuario_id")
            if not usuario_id:
                return qs.none()
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return qs.none()
            qs = qs.filter(modulo__proyecto__creado_por_id=usuario_id)

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return qs


        proyecto_id = self.request.query_params.get("proyecto")
        modulo_id = self.request.query_params.get("modulo")

        if modulo_id and modulo_id != "undefined":
            try:
                return qs.filter(modulo_id=int(modulo_id)).order_by("id")
            except ValueError:
                return qs.none()

        if proyecto_id and proyecto_id != "undefined":
            try:
                return qs.filter(modulo__proyecto__id_proyecto=int(proyecto_id)).order_by("modulo_id", "id")
            except ValueError:
                return qs.none()

        return qs.none()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Permite:
        - crear 1 item (dict)
        - crear varios items (list)  => bulk
        Requiere: modulo_id en cada item (según tu serializer).
        """
        data = request.data

        def _crear_uno(payload: dict):
            serializer = self.get_serializer(data=payload)
            serializer.is_valid(raise_exception=True)

            item: GastoOperacion = serializer.save()

            # costo_parcial (si quieres mantenerlo)
            item.costo_parcial = redondear2(to_decimal(item.cantidad) * to_decimal(item.precio_unitario))
            item.save(update_fields=["costo_parcial"])

            # crear/actualizar gastos generales del item (al inicio será con subtotales 0 en hijos)
            recalcular_item_gastos_generales(item)

            return self.get_serializer(item).data

        # bulk
        if isinstance(data, list):
            resultados = []
            for payload in data:
                resultados.append(_crear_uno(payload))
            return Response(resultados, status=status.HTTP_201_CREATED)

        # single
        if isinstance(data, dict):
            creado = _crear_uno(data)
            return Response(creado, status=status.HTTP_201_CREATED)

        return Response({"error": "Formato inválido"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Si cambian cantidad / precio_unitario => actualizar costo_parcial y recalcular gastos generales del item.
        """
        instance: GastoOperacion = self.get_object()

        # seguridad (dueño)
        if getattr(request, "user", None) and request.user.is_authenticated:
            if instance.modulo.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        item: GastoOperacion = serializer.save()

        item.costo_parcial = redondear2(to_decimal(item.cantidad) * to_decimal(item.precio_unitario))
        item.save(update_fields=["costo_parcial"])

        recalcular_item_gastos_generales(item)

        return Response(self.get_serializer(item).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance: GastoOperacion = self.get_object()

        if getattr(request, "user", None) and request.user.is_authenticated:
            if instance.modulo.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item: GastoOperacion = serializer.save()

        # si tocaron cantidad o precio_unitario => recalcular costo_parcial
        if ("cantidad" in request.data) or ("precio_unitario" in request.data):
            item.costo_parcial = redondear2(to_decimal(item.cantidad) * to_decimal(item.precio_unitario))
            item.save(update_fields=["costo_parcial"])

        recalcular_item_gastos_generales(item)
        return Response(self.get_serializer(item).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Borra un item y por CASCADE borra sus hijos.
        Luego recalcula el proyecto completo (porque cambió el conjunto).
        """
        instance: GastoOperacion = self.get_object()

        if getattr(request, "user", None) and request.user.is_authenticated:
            if instance.modulo.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        proyecto = instance.modulo.proyecto
        instance.delete()

        # recalcular todo el proyecto (regla que pediste)
        recalcular_proyecto(proyecto)

        return Response(status=status.HTTP_204_NO_CONTENT)

    # ==========================
    # Acciones extra
    # ==========================

    @action(detail=False, methods=["get"])
    def ultimos_precios(self, request):
        """
        Devuelve último precio_unitario por descripcion dentro del proyecto.
        ?proyecto=<id_proyecto>
        """
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id or proyecto_id == "undefined":
            return Response({"error": "proyecto requerido"}, status=400)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "proyecto inválido"}, status=400)

        qs = GastoOperacion.objects.filter(modulo__proyecto__id_proyecto=proyecto_id)

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(modulo__proyecto__creado_por=request.user)

        data = (
            qs.values("descripcion")
            .annotate(ultimo_precio=Max("precio_unitario"))
        )
        return Response(list(data), status=200)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def actualizar_precio_descripcion(self, request):
        """
        Actualiza precio_unitario en TODOS los items del proyecto con esa descripcion
        y recalcula SOLO esos items afectados.
        body:
          - proyecto: id_proyecto
          - descripcion: str
          - precio_unitario: number
        """
        proyecto_id = request.data.get("proyecto")
        descripcion = (request.data.get("descripcion") or "").strip()
        nuevo_precio = request.data.get("precio_unitario")

        if not proyecto_id or not descripcion or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "Proyecto inválido"}, status=400)

        try:
            nuevo_precio = Decimal(str(nuevo_precio).replace(",", "."))
        except Exception:
            return Response({"error": f"Precio inválido: {nuevo_precio}"}, status=400)

        proyecto = Proyecto.objects.filter(id_proyecto=proyecto_id).first()
        if not proyecto:
            return Response({"error": "Proyecto no encontrado"}, status=404)

        if getattr(request, "user", None) and request.user.is_authenticated:
            if proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        afectados = list(
            GastoOperacion.objects
            .filter(modulo__proyecto=proyecto, descripcion__iexact=descripcion)
            .values_list("id", flat=True)
        )

        if not afectados:
            return Response({"success": True, "actualizados": 0}, status=200)

        GastoOperacion.objects.filter(id__in=afectados).update(precio_unitario=nuevo_precio)

        # recalcular SOLO afectados
        items = GastoOperacion.objects.filter(id__in=afectados).select_related("modulo", "modulo__proyecto")
        for item in items:
            item.costo_parcial = redondear2(to_decimal(item.cantidad) * to_decimal(item.precio_unitario))
            item.save(update_fields=["costo_parcial"])
            recalcular_item_gastos_generales(item)

        return Response(
            {"success": True, "descripcion": descripcion, "nuevo_precio": float(nuevo_precio), "actualizados": len(afectados)},
            status=200
        )

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def mover_item(self, request):
        """
        Mueve un item a otro módulo (dentro del mismo proyecto)
        body:
          - item_id
          - modulo_destino_id
        """
        item_id = request.data.get("item_id")
        modulo_destino_id = request.data.get("modulo_destino_id")

        if not item_id or not modulo_destino_id:
            return Response({"error": "Datos incompletos"}, status=400)

        try:
            item = GastoOperacion.objects.select_related("modulo__proyecto").get(id=int(item_id))
            modulo_destino = Modulo.objects.select_related("proyecto").get(id=int(modulo_destino_id))
        except Exception:
            return Response({"error": "Ítem o módulo no encontrado"}, status=404)

        # seguridad y coherencia: mismo proyecto
        if item.modulo.proyecto_id != modulo_destino.proyecto_id:
            return Response({"error": "El módulo destino debe pertenecer al mismo proyecto"}, status=400)

        if getattr(request, "user", None) and request.user.is_authenticated:
            if item.modulo.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        item.modulo = modulo_destino
        item.save(update_fields=["modulo"])

        # recalcular solo ese item (por si cambian parámetros de proyecto, aquí no cambian)
        recalcular_item_gastos_generales(item)

        return Response({"success": True}, status=200)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def duplicar_item(self, request):
        """
        Duplica un item a otro módulo (mismo proyecto),
        duplicando Materiales/ManoDeObra/EquipoHerramienta y GastosGenerales.
        body:
          - item_id
          - modulo_destino_id
        """
        item_id = request.data.get("item_id")
        modulo_destino_id = request.data.get("modulo_destino_id")

        if not item_id or not modulo_destino_id:
            return Response({"error": "Datos incompletos"}, status=400)

        try:
            original = GastoOperacion.objects.select_related("modulo__proyecto").get(id=int(item_id))
            modulo_destino = Modulo.objects.select_related("proyecto").get(id=int(modulo_destino_id))
        except Exception:
            return Response({"error": "Ítem o módulo no encontrado"}, status=404)

        if original.modulo.proyecto_id != modulo_destino.proyecto_id:
            return Response({"error": "El módulo destino debe pertenecer al mismo proyecto"}, status=400)

        if getattr(request, "user", None) and request.user.is_authenticated:
            if original.modulo.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        nuevo = GastoOperacion.objects.create(
            modulo=modulo_destino,
            descripcion=original.descripcion,
            unidad=original.unidad,
            cantidad=original.cantidad,
            precio_unitario=original.precio_unitario,
            costo_parcial=redondear2(to_decimal(original.cantidad) * to_decimal(original.precio_unitario)),
        )

        # hijos: materiales
        for m in Materiales.objects.filter(gasto_operacion=original):
            Materiales.objects.create(
                gasto_operacion=nuevo,
                descripcion=m.descripcion,
                unidad=m.unidad,
                cantidad=m.cantidad,
                precio_unitario=m.precio_unitario,
                total=m.total,
            )

        # hijos: mano de obra
        for mo in ManoDeObra.objects.filter(gasto_operacion=original):
            ManoDeObra.objects.create(
                gasto_operacion=nuevo,
                descripcion=mo.descripcion,
                unidad=mo.unidad,
                cantidad=mo.cantidad,
                precio_unitario=mo.precio_unitario,
                total=mo.total,
            )

        # hijos: equipos
        for eq in EquipoHerramienta.objects.filter(gasto_operacion=original):
            EquipoHerramienta.objects.create(
                gasto_operacion=nuevo,
                descripcion=eq.descripcion,
                unidad=eq.unidad,
                cantidad=eq.cantidad,
                precio_unitario=eq.precio_unitario,
                total=eq.total,
            )

        # gastos generales: copiamos si existe, pero igual recalculamos
        gg = GastosGenerales.objects.filter(gasto_operacion=original).first()
        if gg:
            GastosGenerales.objects.update_or_create(
                gasto_operacion=nuevo,
                defaults={"totalgastosgenerales": gg.totalgastosgenerales, "total": gg.total},
            )

        # recalcular definitivo del nuevo item
        recalcular_item_gastos_generales(nuevo)

        return Response({"success": True, "nuevo_item_id": nuevo.id}, status=201)

    @action(detail=False, methods=["get"], url_path="unidades")
    def unidades(self, request):
        qs = GastoOperacion.objects.all()

        # seguridad igual que tu get_queryset()
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if not usuario_id:
                return Response([])
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return Response([])
            qs = qs.filter(modulo__proyecto__creado_por_id=usuario_id)

        unidades = (
            qs.exclude(unidad__isnull=True)
              .exclude(unidad__exact="")
              .values_list("unidad", flat=True)
              .distinct()
              .order_by("unidad")
        )
        return Response(list(unidades))

# =====================================================
# === =============  seccion 3   === ==================
# =====================================================

class MaterialesViewSet(viewsets.ModelViewSet):
    queryset = Materiales.objects.all().select_related(
        "gasto_operacion", "gasto_operacion__modulo", "gasto_operacion__modulo__proyecto"
    )
    serializer_class = MaterialesSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=self.request.user)
        else:
            usuario_id = self.request.query_params.get("usuario_id")
            if not usuario_id:
                return qs.none()
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return qs.none()
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return qs

        gasto_id = self.request.query_params.get("gasto_operacion")
        proyecto_id = self.request.query_params.get("proyecto")

        if gasto_id and gasto_id != "undefined":
            try:
                gasto_id = int(gasto_id)
                return qs.filter(gasto_operacion_id=gasto_id).order_by("id")
            except ValueError:
                return qs.none()

        if proyecto_id and proyecto_id != "undefined":
            try:
                proyecto_id = int(proyecto_id)
                return qs.filter(gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id).order_by(
                    "gasto_operacion_id", "id"
                )
            except ValueError:
                return qs.none()

        return qs.none()


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        material: Materiales = serializer.save()

        # calcular total
        material.total = redondear2(to_decimal(material.cantidad) * to_decimal(material.precio_unitario))
        material.save(update_fields=["total"])

        # recalcular solo el item padre
        recalcular_item_gastos_generales(material.gasto_operacion)

        return Response(self.get_serializer(material).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance: Materiales = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        material: Materiales = serializer.save()

        # recalcular total siempre
        material.total = redondear2(to_decimal(material.cantidad) * to_decimal(material.precio_unitario))
        material.save(update_fields=["total"])

        recalcular_item_gastos_generales(material.gasto_operacion)

        return Response(self.get_serializer(material).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance: Materiales = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        material: Materiales = serializer.save()

        # si tocaron cantidad o precio_unitario => total
        if ("cantidad" in request.data) or ("precio_unitario" in request.data):
            material.total = redondear2(to_decimal(material.cantidad) * to_decimal(material.precio_unitario))
            material.save(update_fields=["total"])

        recalcular_item_gastos_generales(material.gasto_operacion)

        return Response(self.get_serializer(material).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance: Materiales = self.get_object()
        item = instance.gasto_operacion

        instance.delete()

        recalcular_item_gastos_generales(item)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def actualizar_precio_descripcion(self, request):

        proyecto_id = request.data.get("proyecto")
        descripcion_raw = request.data.get("descripcion") or ""
        descripcion_norm = descripcion_raw.strip().upper()
        nuevo_precio = request.data.get("precio_unitario")

        if not proyecto_id or not descripcion_norm or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "Proyecto inválido"}, status=400)

        try:
            nuevo_precio = Decimal(str(nuevo_precio).replace(",", "."))
        except (InvalidOperation, ValueError, TypeError):
            return Response({"error": f"Precio inválido: {nuevo_precio}"}, status=400)

        proyecto = Proyecto.objects.filter(id_proyecto=proyecto_id).first()
        if not proyecto:
            return Response({"error": "Proyecto no encontrado"}, status=404)

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            if proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        # ✅ materiales afectados (comparación normalizada: TRIM + UPPER)
        mats = (
            Materiales.objects
            .filter(gasto_operacion__modulo__proyecto=proyecto)
            .annotate(desc_norm=Upper(Trim(F("descripcion"))))
            .filter(desc_norm=descripcion_norm)
            .select_related("gasto_operacion")
        )

        if not mats.exists():
            return Response({"success": True, "actualizados": 0}, status=200)

        # ids de items afectados
        items_afectados = set(mats.values_list("gasto_operacion_id", flat=True))

        # actualizar precio y total
        actualizados = 0
        for m in mats:
            m.precio_unitario = nuevo_precio
            m.total = redondear2(to_decimal(m.cantidad) * nuevo_precio)
            m.save(update_fields=["precio_unitario", "total"])
            actualizados += 1

        # recalcular SOLO items afectados
        items = GastoOperacion.objects.filter(id__in=list(items_afectados)).select_related(
            "modulo", "modulo__proyecto"
        )
        for item in items:
            recalcular_item_gastos_generales(item)

        return Response(
            {
                "success": True,
                "descripcion": descripcion_norm,
                "nuevo_precio": float(nuevo_precio),
                "actualizados": actualizados,
                "items_afectados": len(items_afectados),
            },
            status=200,
        )
    
    @action(detail=False, methods=["get"])
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id or proyecto_id == "undefined":
            return Response({"error": "proyecto requerido"}, status=400)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "proyecto inválido"}, status=400)

        qs = Materiales.objects.filter(gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id)

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if not usuario_id:
                return Response([], status=200)
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return Response([], status=200)
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        data = (
            qs.values("descripcion", "unidad")
            .annotate(precio_unitario=Max("precio_unitario"))
            .order_by("descripcion")
        )
        return Response(list(data), status=200)


class ManoDeObraViewSet(viewsets.ModelViewSet):
    queryset = ManoDeObra.objects.all().select_related(
        "gasto_operacion", "gasto_operacion__modulo", "gasto_operacion__modulo__proyecto"
    )
    serializer_class = ManoDeObraSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=self.request.user)
        else:
            usuario_id = self.request.query_params.get("usuario_id")
            if not usuario_id:
                return qs.none()
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return qs.none()
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return qs

        gasto_id = self.request.query_params.get("gasto_operacion")
        proyecto_id = self.request.query_params.get("proyecto")

        if gasto_id and gasto_id != "undefined":
            try:
                gasto_id = int(gasto_id)
                return qs.filter(gasto_operacion_id=gasto_id).order_by("id")
            except ValueError:
                return qs.none()

        if proyecto_id and proyecto_id != "undefined":
            try:
                proyecto_id = int(proyecto_id)
                return qs.filter(
                    gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id
                ).order_by("gasto_operacion_id", "id")
            except ValueError:
                return qs.none()

        return qs.none()


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mano: ManoDeObra = serializer.save()

        # calcular total
        mano.total = redondear2(to_decimal(mano.cantidad) * to_decimal(mano.precio_unitario))
        mano.save(update_fields=["total"])

        recalcular_item_gastos_generales(mano.gasto_operacion)

        return Response(self.get_serializer(mano).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):

        instance: ManoDeObra = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        mano: ManoDeObra = serializer.save()

        mano.total = redondear2(to_decimal(mano.cantidad) * to_decimal(mano.precio_unitario))
        mano.save(update_fields=["total"])

        recalcular_item_gastos_generales(mano.gasto_operacion)

        return Response(self.get_serializer(mano).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance: ManoDeObra = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        mano: ManoDeObra = serializer.save()

        if ("cantidad" in request.data) or ("precio_unitario" in request.data):
            mano.total = redondear2(to_decimal(mano.cantidad) * to_decimal(mano.precio_unitario))
            mano.save(update_fields=["total"])

        recalcular_item_gastos_generales(mano.gasto_operacion)

        return Response(self.get_serializer(mano).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):

        instance: ManoDeObra = self.get_object()
        item = instance.gasto_operacion

        instance.delete()

        recalcular_item_gastos_generales(item)

        return Response(status=status.HTTP_204_NO_CONTENT)


    
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def actualizar_precio_descripcion(self, request):

        proyecto_id = request.data.get("proyecto")
        descripcion_raw = request.data.get("descripcion") or ""
        descripcion_norm = descripcion_raw.strip().upper()
        nuevo_precio = request.data.get("precio_unitario")

        if not proyecto_id or not descripcion_norm or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "Proyecto inválido"}, status=400)

        try:
            nuevo_precio = Decimal(str(nuevo_precio).replace(",", "."))
        except (InvalidOperation, ValueError, TypeError):
            return Response({"error": f"Precio inválido: {nuevo_precio}"}, status=400)

        proyecto = Proyecto.objects.filter(id_proyecto=proyecto_id).first()
        if not proyecto:
            return Response({"error": "Proyecto no encontrado"}, status=404)

        if getattr(request, "user", None) and request.user.is_authenticated:
            if proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        # ✅ buscar por descripción normalizada (TRIM + UPPER)
        mos = (
            ManoDeObra.objects
            .filter(gasto_operacion__modulo__proyecto=proyecto)
            .annotate(desc_norm=Upper(Trim(F("descripcion"))))
            .filter(desc_norm=descripcion_norm)
            .select_related("gasto_operacion")
        )

        if not mos.exists():
            return Response({"success": True, "actualizados": 0}, status=200)

        # guardar ids de items afectados
        items_afectados = set(mos.values_list("gasto_operacion_id", flat=True))

        # actualizar precio y total
        actualizados = 0
        for mo in mos:
            mo.precio_unitario = nuevo_precio
            mo.total = redondear2(to_decimal(mo.cantidad) * nuevo_precio)
            mo.save(update_fields=["precio_unitario", "total"])
            actualizados += 1

        # recalcular SOLO items afectados
        items = GastoOperacion.objects.filter(id__in=list(items_afectados)).select_related(
            "modulo", "modulo__proyecto"
        )
        for item in items:
            recalcular_item_gastos_generales(item)

        return Response(
            {
                "success": True,
                "descripcion": descripcion_norm,
                "nuevo_precio": float(nuevo_precio),
                "actualizados": actualizados,
                "items_afectados": len(items_afectados),
            },
            status=200,
        )

    @action(detail=False, methods=["get"], url_path="ultimos_precios")
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id or proyecto_id == "undefined":
            return Response([], status=200)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response([], status=200)

        qs = ManoDeObra.objects.filter(
            gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id
        )

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if usuario_id:
                try:
                    usuario_id = int(usuario_id)
                    qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)
                except ValueError:
                    pass

        data = (
            qs.values("descripcion", "unidad")
              .annotate(precio_unitario=Max("precio_unitario"))
              .order_by("descripcion")
        )
        return Response(list(data), status=200)

    @action(detail=False, methods=["get"], url_path="unidades")
    def unidades(self, request):
        qs = ManoDeObra.objects.all()

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if not usuario_id:
                return Response([])
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return Response([])
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        unidades = (
            qs.exclude(unidad__isnull=True)
              .exclude(unidad__exact="")
              .values_list("unidad", flat=True)
              .distinct()
              .order_by("unidad")
        )
        return Response(list(unidades), status=200)


class EquipoHerramientaViewSet(viewsets.ModelViewSet):
    queryset = EquipoHerramienta.objects.all().select_related(
        "gasto_operacion", "gasto_operacion__modulo", "gasto_operacion__modulo__proyecto"
    )
    serializer_class = EquipoHerramientaSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # 🔒 Seguridad por dueño
        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            qs = qs.filter(
                gasto_operacion__modulo__proyecto__creado_por=self.request.user
            )
        else:
            usuario_id = self.request.query_params.get("usuario_id")
            if not usuario_id:
                return qs.none()
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return qs.none()
            qs = qs.filter(
                gasto_operacion__modulo__proyecto__creado_por_id=usuario_id
            )

        # ✅ PERMITIR DETAIL (IMPORTANTE)
        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return qs

        # 🔎 Filtros para LIST
        gasto_id = self.request.query_params.get("gasto_operacion")
        proyecto_id = self.request.query_params.get("proyecto")

        if gasto_id and gasto_id != "undefined":
            try:
                gasto_id = int(gasto_id)
                return qs.filter(gasto_operacion_id=gasto_id).order_by("id")
            except ValueError:
                return qs.none()

        if proyecto_id and proyecto_id != "undefined":
            try:
                proyecto_id = int(proyecto_id)
                return qs.filter(
                    gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id
                ).order_by("gasto_operacion_id", "id")
            except ValueError:
                return qs.none()

        return qs.none()


    @transaction.atomic
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        equipo: EquipoHerramienta = serializer.save()

        equipo.total = redondear2(to_decimal(equipo.cantidad) * to_decimal(equipo.precio_unitario))
        equipo.save(update_fields=["total"])

        recalcular_item_gastos_generales(equipo.gasto_operacion)

        return Response(self.get_serializer(equipo).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):

        instance: EquipoHerramienta = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        equipo: EquipoHerramienta = serializer.save()

        equipo.total = redondear2(to_decimal(equipo.cantidad) * to_decimal(equipo.precio_unitario))
        equipo.save(update_fields=["total"])

        recalcular_item_gastos_generales(equipo.gasto_operacion)

        return Response(self.get_serializer(equipo).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance: EquipoHerramienta = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        equipo: EquipoHerramienta = serializer.save()

        if ("cantidad" in request.data) or ("precio_unitario" in request.data):
            equipo.total = redondear2(to_decimal(equipo.cantidad) * to_decimal(equipo.precio_unitario))
            equipo.save(update_fields=["total"])

        recalcular_item_gastos_generales(equipo.gasto_operacion)

        return Response(self.get_serializer(equipo).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):

        instance: EquipoHerramienta = self.get_object()
        item = instance.gasto_operacion

        instance.delete()

        recalcular_item_gastos_generales(item)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def actualizar_precio_descripcion(self, request):

        proyecto_id = request.data.get("proyecto")
        descripcion_raw = request.data.get("descripcion") or ""
        descripcion_norm = descripcion_raw.strip().upper()
        nuevo_precio = request.data.get("precio_unitario")

        if not proyecto_id or not descripcion_norm or nuevo_precio is None:
            return Response({"error": "Datos incompletos"}, status=400)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({"error": "Proyecto inválido"}, status=400)

        try:
            nuevo_precio = Decimal(str(nuevo_precio).replace(",", "."))
        except (InvalidOperation, ValueError, TypeError):
            return Response({"error": f"Precio inválido: {nuevo_precio}"}, status=400)

        proyecto = Proyecto.objects.filter(id_proyecto=proyecto_id).first()
        if not proyecto:
            return Response({"error": "Proyecto no encontrado"}, status=404)

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            if proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        # ✅ buscar por descripción normalizada (TRIM + UPPER)
        equipos = (
            EquipoHerramienta.objects
            .filter(gasto_operacion__modulo__proyecto=proyecto)
            .annotate(desc_norm=Upper(Trim(F("descripcion"))))
            .filter(desc_norm=descripcion_norm)
            .select_related("gasto_operacion")
        )

        if not equipos.exists():
            return Response({"success": True, "actualizados": 0}, status=200)

        items_afectados = set(equipos.values_list("gasto_operacion_id", flat=True))

        actualizados = 0
        for eq in equipos:
            eq.precio_unitario = nuevo_precio
            eq.total = redondear2(to_decimal(eq.cantidad) * nuevo_precio)
            eq.save(update_fields=["precio_unitario", "total"])
            actualizados += 1

        # recalcular SOLO items afectados
        items = GastoOperacion.objects.filter(id__in=list(items_afectados)).select_related(
            "modulo", "modulo__proyecto"
        )
        for item in items:
            recalcular_item_gastos_generales(item)

        return Response(
            {
                "success": True,
                "descripcion": descripcion_norm,
                "nuevo_precio": float(nuevo_precio),
                "actualizados": actualizados,
                "items_afectados": len(items_afectados),
            },
            status=200,
        )

      
    
    @action(detail=False, methods=["get"], url_path="ultimos_precios")
    def ultimos_precios(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id or proyecto_id == "undefined":
            return Response([], status=200)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response([], status=200)

        qs = EquipoHerramienta.objects.filter(
            gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id
        )

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if usuario_id:
                try:
                    usuario_id = int(usuario_id)
                    qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)
                except ValueError:
                    pass

        data = (
            qs.values("descripcion", "unidad")
              .annotate(precio_unitario=Max("precio_unitario"))

              .order_by("descripcion")
        )
        return Response(list(data), status=200)
    
    @action(detail=False, methods=["get"], url_path="unidades")
    def unidades(self, request):
        qs = EquipoHerramienta.objects.all()

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if not usuario_id:
                return Response([])
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return Response([])
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        unidades = (
            qs.exclude(unidad__isnull=True)
              .exclude(unidad__exact="")
              .values_list("unidad", flat=True)
              .distinct()
              .order_by("unidad")
        )
        return Response(list(unidades), status=200)



class GastosGeneralesViewSet(viewsets.ModelViewSet):

    queryset = GastosGenerales.objects.all().select_related(
        "gasto_operacion",
        "gasto_operacion__modulo",
        "gasto_operacion__modulo__proyecto",
    )
    serializer_class = GastosGeneralesSerializer

    def get_queryset(self):

        qs = super().get_queryset()

        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=self.request.user)
        else:
            usuario_id = self.request.query_params.get("usuario_id")
            if not usuario_id:
                return qs.none()
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return qs.none()
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        gasto_id = self.request.query_params.get("gasto_operacion")
        proyecto_id = self.request.query_params.get("proyecto")

        if gasto_id and gasto_id != "undefined":
            try:
                return qs.filter(gasto_operacion_id=int(gasto_id))
            except ValueError:
                return qs.none()

        if proyecto_id and proyecto_id != "undefined":
            try:
                return qs.filter(gasto_operacion__modulo__proyecto__id_proyecto=int(proyecto_id))
            except ValueError:
                return qs.none()

        return qs

    def create(self, request, *args, **kwargs):
        return Response(
            {"error": "GastosGenerales se genera automáticamente. Use el endpoint /recalcular/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"error": "GastosGenerales se recalcula automáticamente. Use el endpoint /recalcular/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"error": "GastosGenerales se recalcula automáticamente. Use el endpoint /recalcular/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "No se elimina manualmente. Se gestiona automáticamente por el sistema."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["post"])
    def recalcular_item(self, request):
        item_id = request.data.get("gasto_operacion")
        if not item_id:
            return Response({"error": "gasto_operacion es requerido"}, status=400)

        try:
            item = (
                GastoOperacion.objects
                .select_related("modulo", "modulo__proyecto")
                .get(id=int(item_id))
            )
        except (ValueError, GastoOperacion.DoesNotExist):
            return Response({"error": "GastoOperacion no encontrado"}, status=404)

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            if item.modulo.proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        gg = recalcular_item_gastos_generales(item)
        return Response(self.get_serializer(gg).data, status=200)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def recalcular_proyecto(self, request):

        proyecto_id = request.data.get("proyecto")
        if not proyecto_id:
            return Response({"error": "proyecto es requerido"}, status=400)

        try:
            proyecto = Proyecto.objects.get(id_proyecto=int(proyecto_id))
        except (ValueError, Proyecto.DoesNotExist):
            return Response({"error": "Proyecto no encontrado"}, status=404)

        # seguridad
        if getattr(request, "user", None) and request.user.is_authenticated:
            if proyecto.creado_por_id != request.user.id:
                return Response({"error": "No autorizado"}, status=403)

        count = recalcular_proyecto_completo(proyecto)
        return Response({"success": True, "items_recalculados": count}, status=200)

    @action(detail=False, methods=["get"])
    def totals_por_proyecto(self, request):
        proyecto_id = request.query_params.get("proyecto")
        if not proyecto_id or proyecto_id == "undefined":
            return Response({}, status=200)

        try:
            proyecto_id = int(proyecto_id)
        except ValueError:
            return Response({}, status=200)

        qs = GastosGenerales.objects.filter(
            gasto_operacion__modulo__proyecto__id_proyecto=proyecto_id
        ).select_related("gasto_operacion")

        # seguridad (igual que get_queryset)
        if getattr(request, "user", None) and request.user.is_authenticated:
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por=request.user)
        else:
            usuario_id = request.query_params.get("usuario_id")
            if not usuario_id:
                return Response({}, status=200)
            try:
                usuario_id = int(usuario_id)
            except ValueError:
                return Response({}, status=200)
            qs = qs.filter(gasto_operacion__modulo__proyecto__creado_por_id=usuario_id)

        data = {}
        for gg in qs:
            gid = str(gg.gasto_operacion_id)
            data[gid] = {
                "totalgastosgenerales": float(gg.totalgastosgenerales or 0),
                "total": float(gg.total or 0),
            }
        return Response(data, status=200)