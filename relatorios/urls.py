"""
URL configuration for the relatorios module.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
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

urlpatterns = [
    path("", include(router.urls)),
]
