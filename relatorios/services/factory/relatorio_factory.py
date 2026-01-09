"""
Factory para criação de instâncias de relatórios baseado no tipo.
"""
from relatorios.services.relatorios.lauda_vagas import LaudaVagas
from relatorios.services.relatorios.relacao_vagas import RelacaoVagas
from relatorios.services.relatorios.nao_escolhas import NaoEscolhas
from relatorios.services.relatorios.listagem_escolhas_dres import ListagemEscolhasDres
from relatorios.services.relatorios.reconvocacao import Reconvocacao

class RelatorioFactory:
    """
    Factory responsável por criar instâncias dos diferentes tipos de relatórios.
    O mapeamento fica "escondido" dentro da Factory.
    """
    
    _MAPA = {
        'LAUDA_VAGAS': LaudaVagas,
        'RELACAO_VAGAS': RelacaoVagas,
        'NAO_ESCOLHAS': NaoEscolhas,
        'LISTAGEM_ESCOLHAS_DRES': ListagemEscolhasDres,
        'RECONVOCACAO': Reconvocacao,
        # TODO: Adicionar outros tipos quando implementados
        # 'LAUDA_CONVOCACAO': LaudaConvocacao,
        # 'ETIQUETAS_CONVOCADOS': EtiquetasConvocados,
        # 'CAPA_ATA_ESCOLHAS': CapaAtaEscolhas,
        # 'RESULTADO_ESCOLHA_VAGAS': ResultadoEscolhaVagas,
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