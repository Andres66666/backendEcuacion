from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import  views_Aporte, views_GestionProyectos, views_GestionUsuarios

router = DefaultRouter()
# =====================================================
# === =============  seccion 1   === ==================
# =====================================================
router.register(r"rol", views_GestionUsuarios.RolViewSet)
router.register(r"permiso", views_GestionUsuarios.PermisoViewSet)
router.register(r"usuario", views_GestionUsuarios.UsuarioViewSet)
router.register(r"usuario_rol", views_GestionUsuarios.UsuarioRolViewSet)
router.register(r"rol_permiso", views_GestionUsuarios.RolPermisoViewSet)
# =====================================================
# === =============  seccion 2   === ==================
# =====================================================

router.register(r"IdGeneral", views_GestionProyectos.ProyectoViewSet)
router.register(r"modulos", views_GestionProyectos.ModuloViewSet)
router.register(r"GastosOperaciones", views_GestionProyectos.GastoOperacionViewSet)

router.register(r"materiales", views_GestionProyectos.MaterialesViewSet)
router.register(r"mano_de_obra", views_GestionProyectos.ManoDeObraViewSet)
router.register(r"equipo_herramienta", views_GestionProyectos.EquipoHerramientaViewSet)
router.register(r"gastos_generales", views_GestionProyectos.GastosGeneralesViewSet)

# =====================================================
# === =============  seccion 3   === ==================
# =====================================================
router.register(r"auditoria_db", views_Aporte.AtacanteViewSet)

urlpatterns = [
    path("", include(router.urls)),

    path("login/", views_GestionUsuarios.LoginView.as_view(), name="login"),
    path("verificar-2fa/", views_GestionUsuarios.Verificar2FAView.as_view(), name="verificar-2fa"),
    path("generar-qr/", views_GestionUsuarios.GenerarQRView.as_view(), name="generar-qr"),
    path("enviar-codigo/", views_GestionUsuarios.EnviarCodigoCorreoView.as_view(), name="enviar-codigo"),
    path("reset-password/", views_GestionUsuarios.ResetPasswordView.as_view(), name="reset-password"),
    path("verificar-temp/",views_GestionUsuarios.VerificarTempPasswordView.as_view(),name="verificar-temp",),
    path("cambiar-password-temp/",views_GestionUsuarios.CambiarPasswordTempView.as_view(),name="cambiar-password-temp",),

    path("registro-cliente/", views_GestionUsuarios.RegistroClienteView.as_view()),
    path("validar-correo/", views_GestionUsuarios.ValidarCorreoView.as_view()),
    path("enviar-verificacion/", views_GestionUsuarios.EnviarVerificacionView.as_view()),
    path("confirmar/<uuid:token>/", views_GestionUsuarios.ConfirmarRegistroView.as_view()),


]
