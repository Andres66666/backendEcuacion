
from rest_framework import viewsets
from .models import (Atacante)
from .serializers import (AtacanteSerializer)

class AtacanteViewSet(viewsets.ModelViewSet):
    queryset = Atacante.objects.all().order_by("-fecha")
    serializer_class = AtacanteSerializer

