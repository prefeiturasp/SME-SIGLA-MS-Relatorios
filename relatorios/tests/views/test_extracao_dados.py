from unittest.mock import Mock, patch

import pytest
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_extracao_dados_query_serializer_valid():
    from relatorios.serializers.extracao_dados import (
        ExtracaoDadosQuerySerializer,
    )

    serializer = ExtracaoDadosQuerySerializer(
        data={
            "concurso_uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            "ano": 2026,
        }
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["ano"] == 2026


def test_extracao_dados_query_serializer_ano_invalido():
    from relatorios.serializers.extracao_dados import (
        ExtracaoDadosQuerySerializer,
    )

    serializer = ExtracaoDadosQuerySerializer(
        data={
            "concurso_uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            "ano": 26,
        }
    )
    assert not serializer.is_valid()
    assert "ano" in serializer.errors


@patch("relatorios.views.extracao_dados.ExtracaoDadosService")
def test_extracao_dados_get_com_filtros(mock_service_cls, client):
    mock_service = Mock()
    mock_service.extrair.return_value = {
        "candidatos": {"habilitados": {"total": 10000}},
    }
    mock_service_cls.return_value = mock_service

    url = reverse("extracao-dados-list")
    response = client.get(
        url,
        {
            "concurso_uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            "ano": 2026,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["candidatos"]["habilitados"]["total"] == 10000
    mock_service.extrair.assert_called_once_with(
        concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        ano=2026,
    )


@patch("relatorios.views.extracao_dados.ExtracaoDadosService")
def test_extracao_dados_total_get(mock_service_cls, client):
    mock_service = Mock()
    mock_service.extrair_total.return_value = {
        "candidatos": {"habilitados": {"total": 50000}},
    }
    mock_service_cls.return_value = mock_service

    url = reverse("extracao-dados-total")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    mock_service.extrair_total.assert_called_once_with()


def test_extracao_dados_get_sem_parametros_invalido(client):
    url = reverse("extracao-dados-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("relatorios.views.extracao_dados.ExtracaoDadosService")
def test_extracao_dados_get_erro_microservico(mock_service_cls, client):
    mock_service = Mock()
    mock_service.extrair.side_effect = requests.RequestException("timeout")
    mock_service_cls.return_value = mock_service

    url = reverse("extracao-dados-list")
    response = client.get(
        url,
        {
            "concurso_uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            "ano": 2026,
        },
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY


@patch("relatorios.views.extracao_dados.ExtracaoDadosService")
def test_extracao_dados_total_get_erro_microservico(mock_service_cls, client):
    mock_service = Mock()
    mock_service.extrair_total.side_effect = requests.RequestException(
        "timeout"
    )
    mock_service_cls.return_value = mock_service

    url = reverse("extracao-dados-total")
    response = client.get(url)

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
