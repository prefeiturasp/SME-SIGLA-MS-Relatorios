"""Factory para criação de instâncias de relatórios baseado no tipo."""
from __future__ import annotations
from typing import Any
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios import AtaEscolha, LaudaConvocacao, LaudaVagas, ListaCandidatosSessao, ListagemEscolhasDres, RelacaoVagas, ResultadoEscolha, SumulaEscolhas, SumulaNaoEscolhas, SumulaReconvocacao

class RelatorioFactory:
    """Factory responsável por criar instâncias dos diferentes tipos de."""
    _MAPA = {'LAUDA_VAGAS': LaudaVagas, 'RELACAO_VAGAS': RelacaoVagas, 'SUMULA_NAO_ESCOLHAS': SumulaNaoEscolhas, 'LISTAGEM_ESCOLHAS_DRES': ListagemEscolhasDres, 'SUMULA_RECONVOCACAO': SumulaReconvocacao, 'SUMULA_ESCOLHAS': SumulaEscolhas, 'LAUDA_CONVOCACAO': LaudaConvocacao, 'RESULTADO_ESCOLHA': ResultadoEscolha, 'LISTA_CANDIDATOS_SESSAO': ListaCandidatosSessao, 'ATA_ESCOLHA': AtaEscolha}

    @staticmethod
    def obter_relatorio(tipo_slug: str) -> Any:
        """Esta é a 'central de inteligência'.
        
        Args:
            tipo_slug: String com o tipo do relatório (ex: 'LAUDA_VAGAS').
        
        Returns:
            Resultado da operação.
        
        Raises:
            ValueError: Se o tipo fornecido não for um relatório válido.
        """
        classe = RelatorioFactory._MAPA.get(tipo_slug.upper())
        configuracao = ConfiguracaoRelatorio.objects.get(tipo=tipo_slug.upper())
        parametrizacao = Parametrizacao.objects.first()
        if not classe:
            raise ValueError(f"O tipo '{tipo_slug}' não é um relatório válido.")
        return classe(tipo=tipo_slug, configuracao=configuracao, parametrizacao=parametrizacao)
