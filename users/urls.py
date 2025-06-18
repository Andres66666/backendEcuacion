from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import RolViewSet

from . import views
ruter = DefaultRouter()
ruter.register(r'rol', RolViewSet)
ruter.register(r'permiso', views.PermisoViewSet)
ruter.register(r'usuario', views.UsuarioViewSet)
ruter.register(r'usuario_rol', views.UsuarioRolViewSet)
ruter.register(r'rol_permiso', views.RolPermisoViewSet)

ruter.register(r'categoria', views.CategoriasViewSet)
ruter.register(r'materiales', views.MaterialesViewSet)
ruter.register(r'mano_de_obra', views.ManoDeObraViewSet)
ruter.register(r'equipo_herramienta', views.EquipoHerramientaViewSet)
ruter.register(r'ecuacion', views.EcuacionViewSet)
ruter.register(r'gastos', views.GastosGeneralesViewSet)

urlpatterns = [
    path('', include(ruter.urls)),
]