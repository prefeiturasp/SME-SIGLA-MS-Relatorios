import pytest
from unittest.mock import patch, Mock, MagicMock
from django.http import HttpResponse

from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao


pytestmark = pytest.mark.django_db


@pytest.fixture
def configuracao_relatorio():
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo='LAUDA_VAGAS',  # Tipo genérico para testes
        defaults={
            'usar_logotipo': False,
            'usar_cabecalho_padrao': False,
            'cabecalho': '',
            'texto_final': '',
            'cabecalho_capa_ata': ''
        }
    )[0]


@pytest.fixture
def parametrizacao():
    """Fixture que cria uma Parametrizacao para testes."""
    return Parametrizacao.objects.create(
        cabecalho='Cabeçalho Padrão Teste',
        logo=None
    )


class DummyRelatorio(RelatorioBase):
    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = ''):
        return HttpResponse('ok'), {}


def test_render_to_pdf_success(monkeypatch, configuracao_relatorio, parametrizacao):
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio,
        parametrizacao=parametrizacao
    )

    # Mock render_to_string to return simple HTML
    with patch('relatorios.services.base.relatorio_base.render_to_string', return_value='<html><body>PDF</body></html>') as m_render, \
         patch('relatorios.services.base.relatorio_base.HTML') as m_html_cls:

        m_html = Mock()
        m_html_cls.return_value = m_html

        response = rel.render_to_pdf('tpl.html', {'x': 1}, filename='file.pdf')

    m_render.assert_called_once_with('tpl.html', {'x': 1})
    m_html_cls.assert_called_once()
    # write_pdf foi chamado
    assert m_html.write_pdf.call_count == 1
    # Resposta é um PDF
    assert isinstance(response, HttpResponse)
    assert response['Content-Type'] == 'application/pdf'
    assert 'attachment; filename="file.pdf"' in response['Content-Disposition']


def test_render_to_pdf_error_propagates(monkeypatch, configuracao_relatorio, parametrizacao):
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio,
        parametrizacao=parametrizacao
    )
    with patch('relatorios.services.base.relatorio_base.render_to_string', return_value='<html/>'), \
         patch('relatorios.services.base.relatorio_base.HTML') as m_html_cls:
        m_html = Mock()
        m_html.write_pdf.side_effect = RuntimeError('fail')
        m_html_cls.return_value = m_html
        with pytest.raises(RuntimeError):
            rel.render_to_pdf('x.html', {})


@pytest.mark.parametrize(
    'html,expected',
    [
        ('', ''),
        (None, ''),
        ('<p>Oi&nbsp;Mundo</p><br><p>Segunda&nbsp;&amp; Linha</p>',
         'Oi Mundo\n\nSegunda & Linha'),
        ('Texto sem tags', 'Texto sem tags'),
        ('<p>Um</p><p>Dois</p><p>Três</p>', 'Um\nDois\nTrês'),
        ('A&nbsp;&lt;B&gt; &quot;C&quot; &#39;D&#39;', 'A <B> "C" \'D\''),
        ('Linha1<br/><br />\n<br> Linha2', 'Linha1\n\n Linha2'),  # quebra dupla vira, no final, compactada
    ],
)
def test_processar_cabecalho_html(html, expected):
    result = RelatorioBase.processar_cabecalho_html(html)
    # Normaliza quebras múltiplas para comparar com expected
    assert result == expected.strip()


