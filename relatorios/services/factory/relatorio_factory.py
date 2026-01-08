"""
Factory para criação de instâncias de relatórios baseado no tipo.
"""
from relatorios.services.relatorios.lauda_vagas import LaudaVagas
from relatorios.services.relatorios.lauda_convocacao import LaudaConvocacao


class RelatorioFactory:
    """
    Factory responsável por criar instâncias dos diferentes tipos de relatórios.
    O mapeamento fica "escondido" dentro da Factory.
    """
    
    _MAPA = {
        'LAUDA_VAGAS': LaudaVagas,
        'LAUDA_CONVOCACAO': LaudaConvocacao,
        # TODO: Adicionar outros tipos quando implementados
        # 'RELACAO_VAGAS': RelacaoVagas,
        # 'ETIQUETAS_CONVOCADOS': EtiquetasConvocados,
        # 'CAPA_ATA_ESCOLHAS': CapaAtaEscolhas,
        # 'RESULTADO_ESCOLHA_VAGAS': ResultadoEscolhaVagas,
        # 'LISTAGEM_ESCOLHAS_DRES': ListagemEscolhasDres,
        # 'LISTA_CANDIDATOS_SESSAO': ListaCandidatosSessao,
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