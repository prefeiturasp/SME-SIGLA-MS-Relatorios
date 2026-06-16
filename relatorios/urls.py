"""URL configuration for the relatorios module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExtracaoDadosViewSet,
    ParametrizacaoViewSet,
    PersonalizacaoViewSet,
    RelatorioViewSet,
)

router = DefaultRouter()
router.register(r"relatorios", RelatorioViewSet)
router.register(
    r"parametrizacao", ParametrizacaoViewSet, basename="parametrizacao"
)
router.register(
    r"personalizacao", PersonalizacaoViewSet, basename="personalizacao"
)
router.register(
    r"extracao-dados", ExtracaoDadosViewSet, basename="extracao-dados"
)

urlpatterns = [
    path("", include(router.urls)),
]
