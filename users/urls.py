from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
# =====================================================
# === =============  seccion 3   === ==================
# =====================================================
router.register(r"materiales", views.MaterialesViewSet)
router.register(r"mano_de_obra", views.ManoDeObraViewSet)
router.register(r"equipo_herramienta", views.EquipoHerramientaViewSet)
router.register(r"gastos_generales", views.GastosGeneralesViewSet)

router.register(r"auditoria_db", views.AtacanteViewSet)

# =====================================================
# === =============  seccion 4   === ==================
# =====================================================
urlpatterns = [
    path("", include(router.urls)),
    path("login/", views.LoginView.as_view(), name="login"),
]
