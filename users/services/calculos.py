# services/calculos.py

from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from users.models import (
    GastosGenerales,
    Materiales,
    ManoDeObra,
    EquipoHerramienta
)

def redondear2(valor):
    return Decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def recalcular_gastos_generales(proyecto):
    gastos_generales_pct = proyecto.gastos_generales
    margen_utilidad_pct = proyecto.margen_utilidad
    iva_tasa_nominal_pct = proyecto.iva_tasa_nominal
    carga_social_pct = proyecto.carga_social
    iva_efectiva_pct = proyecto.iva_efectiva
    herramientas_pct = proyecto.herramientas

    gastos_generales_qs = GastosGenerales.objects.filter(
        id_gasto_operacion__identificador=proyecto
    ).select_related('id_gasto_operacion')

    for gasto_gen in gastos_generales_qs:
        id_gasto_operacion = gasto_gen.id_gasto_operacion

        subtotal_materiales = Materiales.objects.filter(
            id_gasto_operacion=id_gasto_operacion
        ).aggregate(total=Sum('total'))['total'] or 0

        subtotal_mano_obra = ManoDeObra.objects.filter(
            id_gasto_operacion=id_gasto_operacion
        ).aggregate(total=Sum('total'))['total'] or 0

        subtotal_equipos = EquipoHerramienta.objects.filter(
            id_gasto_operacion=id_gasto_operacion
        ).aggregate(total=Sum('total'))['total'] or 0

        cargas = redondear2(subtotal_mano_obra * carga_social_pct / 100)
        iva = redondear2((subtotal_mano_obra + cargas) * iva_efectiva_pct / 100)
        total_mano = redondear2(subtotal_mano_obra + cargas + iva)

        herramientas_valor = redondear2(total_mano * herramientas_pct / 100)
        total_equipos = redondear2(subtotal_equipos + herramientas_valor)

        suma = redondear2(subtotal_materiales + total_mano + total_equipos)

        total_gg = redondear2(suma * gastos_generales_pct / 100)
        suma_gg = redondear2(suma + total_gg)

        base = 100 - iva_tasa_nominal_pct
        utilidad = redondear2(
            suma_gg * (margen_utilidad_pct / (base - margen_utilidad_pct))
        ) if base - margen_utilidad_pct != 0 else 0

        total_final = redondear2(suma_gg + utilidad)

        gasto_gen.totalgastosgenerales = suma_gg
        gasto_gen.total = total_final
        gasto_gen.save()
