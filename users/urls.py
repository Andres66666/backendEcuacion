from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ClienteViewSet, LoginView, RolViewSet, UsuarioViewSet

router = DefaultRouter()

# Registro de viewsets con nombres únicos y sin repeticiones
router.register(r'rol', RolViewSet)
router.register(r'permiso', views.PermisoViewSet)
router.register(r'usuario', UsuarioViewSet, basename='usuario')  # UsuarioViewSet con basename explícito
router.register(r'usuario_rol', views.UsuarioRolViewSet)
router.register(r'rol_permiso', views.RolPermisoViewSet)

router.register(r'cliente', ClienteViewSet, basename='cliente')  # ClienteViewSet con basename único

router.register(r'categoria', views.CategoriasViewSet)
router.register(r'materiales', views.MaterialesViewSet)
router.register(r'mano_de_obra', views.ManoDeObraViewSet)
router.register(r'equipo_herramienta', views.EquipoHerramientaViewSet)
router.register(r'ecuacion', views.EcuacionViewSet)
router.register(r'gastos', views.GastosGeneralesViewSet)
router.register(r'GastosOperaciones',views.GastoOperacionViewSet)
router.register(r'IDGeneral',views.IdentificadorInmuebleViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
]
