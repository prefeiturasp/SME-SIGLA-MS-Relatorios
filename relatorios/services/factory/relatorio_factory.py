"""
Factory para criação de instâncias de relatórios baseado no tipo.
"""
from relatorios.services.relatorios import (
    LaudaVagas,
    RelacaoVagas,
    SumulaNaoEscolhas,
    ListagemEscolhasDres,
    SumulaReconvocacao,
    SumulaEscolhas,
    LaudaConvocacao,
    ListaCandidatosSessao,
)


class RelatorioFactory:
    """
    Factory responsável por criar instâncias dos diferentes tipos de relatórios.
    O mapeamento fica "escondido" dentro da Factory.
    """

    _MAPA = {
        'LAUDA_VAGAS': LaudaVagas,
        'RELACAO_VAGAS': RelacaoVagas,
        'SUMULA_NAO_ESCOLHAS': SumulaNaoEscolhas,
        'LISTAGEM_ESCOLHAS_DRES': ListagemEscolhasDres,
        'SUMULA_RECONVOCACAO': SumulaReconvocacao,
        'SUMULA_ESCOLHAS': SumulaEscolhas,
        'LAUDA_CONVOCACAO': LaudaConvocacao,
        'LISTA_CANDIDATOS_SESSAO': ListaCandidatosSessao,
        # TODO: Adicionar outros tipos quando implementados
        # 'ETIQUETAS_CONVOCADOS': EtiquetasConvocados,
        # 'RESULTADO_ESCOLHA_VAGAS': ResultadoEscolhaVagas,
    }

    @staticmethod
    def obter_relatorio(tipo_slug: str):
        """
        Esta é a 'central de inteligência'.
        Ela decide qual classe instanciar baseado no tipo fornecido.

        Args:
            tipo_slug: String com o tipo do relatório (ex: 'LAUDA_VAGAS')

        Returns:
            Instância da classe de relatório correspondente

        Raises:
            ValueError: Se o tipo fornecido não for um relatório válido
        """
        classe = RelatorioFactory._MAPA.get(tipo_slug.upper())

        if not classe:
            raise ValueError(f"O tipo '{tipo_slug}' não é um relatório válido.")

        return classe() 