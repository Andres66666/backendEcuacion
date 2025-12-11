from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import  viewsGestionUsuarios, viewsGestionProyectos, viewsAporte

router = DefaultRouter()
# =====================================================
# === =============  seccion 1   === ==================
# =====================================================
router.register(r"rol", viewsGestionUsuarios.RolViewSet)
router.register(r"permiso", viewsGestionUsuarios.PermisoViewSet)
router.register(r"usuario", viewsGestionUsuarios.UsuarioViewSet)
router.register(r"usuario_rol", viewsGestionUsuarios.UsuarioRolViewSet)
router.register(r"rol_permiso", viewsGestionUsuarios.RolPermisoViewSet)
# =====================================================
# === =============  seccion 2   === ==================
# =====================================================

router.register(r"IdGeneral", viewsGestionProyectos.ProyectoViewSet)
router.register(r"modulos", viewsGestionProyectos.ModuloViewSet)
router.register(r"GastosOperaciones", viewsGestionProyectos.GastoOperacionViewSet)

router.register(r"materiales", viewsGestionProyectos.MaterialesViewSet)
router.register(r"mano_de_obra", viewsGestionProyectos.ManoDeObraViewSet)
router.register(r"equipo_herramienta", viewsGestionProyectos.EquipoHerramientaViewSet)
router.register(r"gastos_generales", viewsGestionProyectos.GastosGeneralesViewSet)

# =====================================================
# === =============  seccion 3   === ==================
# =====================================================
router.register(r"auditoria_db", viewsAporte.AtacanteViewSet)

urlpatterns = [
    path("", include(router.urls)),

    path("login/", viewsGestionUsuarios.LoginView.as_view(), name="login"),
    path("verificar-2fa/", viewsGestionUsuarios.Verificar2FAView.as_view(), name="verificar-2fa"),
    path("generar-qr/", viewsGestionUsuarios.GenerarQRView.as_view(), name="generar-qr"),
    path("enviar-codigo/", viewsGestionUsuarios.EnviarCodigoCorreoView.as_view(), name="enviar-codigo"),
    path("reset-password/", viewsGestionUsuarios.ResetPasswordView.as_view(), name="reset-password"),
    path("verificar-temp/",viewsGestionUsuarios.VerificarTempPasswordView.as_view(),name="verificar-temp",),
    path("cambiar-password-temp/",viewsGestionUsuarios.CambiarPasswordTempView.as_view(),name="cambiar-password-temp",),

    path("registro-cliente/", viewsGestionUsuarios.RegistroClienteView.as_view()),
    path("validar-correo/", viewsGestionUsuarios.ValidarCorreoView.as_view()),
    path("enviar-verificacion/", viewsGestionUsuarios.EnviarVerificacionView.as_view()),
    path("confirmar/<uuid:token>/", viewsGestionUsuarios.ConfirmarRegistroView.as_view()),


]
