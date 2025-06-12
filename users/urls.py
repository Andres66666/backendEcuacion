from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import RolViewSet

from . import views
ruter = DefaultRouter()
ruter.register(r'rol', RolViewSet)

urlpatterns = [
    path('', include(ruter.urls)),
]