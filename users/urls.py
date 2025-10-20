from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from two_factor.urls import urlpatterns as two_factor_urlpatterns

router = DefaultRouter()
# =====================================================
# === =============  seccion 1   === ==================
# =====================================================
router.register(r"rol", views.RolViewSet)
router.register(r"permiso", views.PermisoViewSet)
router.register(r"usuario", views.UsuarioViewSet)
router.register(r"usuario_rol", views.UsuarioRolViewSet)
router.register(r"rol_permiso", views.RolPermisoViewSet)
# =====================================================
# === =============  seccion 2   === ==================
# =====================================================

router.register(r"IdGeneral", views.ProyectoViewSet)
router.register(r"GastosOperaciones", views.GastoOperacionViewSet)
router.register(r"modulos", views.ModuloViewSet)
# =====================================================
# === =============  seccion 3   === ==================
# =====================================================
router.register(r"materiales", views.MaterialesViewSet)
router.register(r"mano_de_obra", views.ManoDeObraViewSet)
router.register(r"equipo_herramienta", views.EquipoHerramientaViewSet)
router.register(r"gastos_generales", views.GastosGeneralesViewSet)

router.register(r"auditoria_db", views.AtacanteViewSet)
router.register(r"auditoria_eventos", views.AuditoriaEventoViewSet)


# =====================================================
# === =============  seccion 4   === ==================
# =====================================================

urlpatterns = [
    path("", include(router.urls)),
    path("login/", views.LoginView.as_view(), name="login"),
    path("verificar-2fa/", views.Verificar2FAView.as_view(), name="verificar-2fa"),
    path(
        "enviar-codigo/", views.EnviarCodigoCorreoView.as_view(), name="enviar-codigo"
    ),
    path("generar-qr/", views.GenerarQRView.as_view(), name="generar-qr"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),
    path(
        "verificar-temp/",
        views.VerificarTempPasswordView.as_view(),
        name="verificar-temp",
    ),  # ← NUEVO
    path(
        "cambiar-password-temp/",
        views.CambiarPasswordTempView.as_view(),
        name="cambiar-password-temp",
    ),  # ← NUEVO
]
