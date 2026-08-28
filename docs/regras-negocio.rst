Regras de Negócio
==================

Tipos de relatório
----------------------

O módulo gera dez tipos de documento, definidos em
``apps/relatorios/models/constants.py::TIPOS_RELATORIOS``:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Código (``tipo``)
     - Documento gerado
   * - ``LAUDA_VAGAS``
     - Lauda de Vagas
   * - ``RELACAO_VAGAS``
     - Relação de Vagas
   * - ``SUMULA_NAO_ESCOLHAS``
     - Relatório de Não Escolhas
   * - ``LISTAGEM_ESCOLHAS_DRES``
     - Listagem de Escolhas por DREs
   * - ``SUMULA_RECONVOCACAO``
     - Súmula de Reconvocados
   * - ``SUMULA_ESCOLHAS``
     - Súmula de Escolhas
   * - ``LAUDA_CONVOCACAO``
     - Lauda de Convocação
   * - ``RESULTADO_ESCOLHA``
     - Resultado de Escolha de Vagas
   * - ``LISTA_CANDIDATOS_SESSAO``
     - Lista de Candidatos por Sessão
   * - ``ATA_ESCOLHA``
     - Ata de Escolha

Despacho por tipo (``RelatorioFactory``)
--------------------------------------------

``RelatorioFactory.obter_relatorio(tipo_slug)`` mapeia o código do tipo para
a classe geradora concreta correspondente, em ``services/relatorios/``. Se o
código informado não estiver no mapa, a criação falha com ``ValueError``
("O tipo '<tipo>' não é um relatório válido."), impedindo que a view chegue
a montar um relatório inexistente. Junto com a classe, a factory já resolve
a ``ConfiguracaoRelatorio`` do tipo (cabeçalho, rodapé) e a
``Parametrizacao`` mais recente (logotipo, cabeçalho padrão), repassadas ao
construtor de toda classe geradora (``RelatorioBase.__init__``).

Negociação de formato de saída
-----------------------------------

Todo relatório pode ser solicitado em mais de um formato — a escolha é
decidida em ``RelatorioViewSet.create()`` por parâmetro de query
(``?formato=pdf``) ou pelo cabeçalho HTTP ``Accept``, com ``html`` como
padrão quando nenhum dos dois é informado. Cada classe geradora implementa
o método abstrato ``gerar()`` e decide internamente como atender cada
formato suportado (renderização direta de HTML, ``render_to_pdf`` via
WeasyPrint, ou montagem de DOCX/XLSX).

Regra de cargo obrigatório (``CargoObrigatorioError``)
------------------------------------------------------------

Um processo de convocação pode abranger mais de um cargo. Quando isso
acontece, o relatório de Ata de Escolha não pode ser gerado sem que o
cargo desejado seja informado explicitamente — a ambiguidade impediria
saber qual cargo o documento deve descrever. Nesse caso,
``AtaEscolhaService`` levanta ``CargoObrigatorioError``, capturada pela
view (``api/views/relatorios.py``), que responde HTTP 400 com a lista dos
cargos possíveis para o solicitante escolher.

Cálculo do comparativo de vagas x escolhas
------------------------------------------------

``ExtracaoDadosService._montar_comparativo()`` produz os dados usados nos
relatórios comparativos entre anos/processos:

- **Diferença absoluta**: ``_diferenca_absoluta`` calcula a variação de
  vagas ou escolhas de um ano para o outro.
- **Percentual de preenchimento**: ``percentual_preenchimento =
  round((escolhas / vagas) * 100, 1)`` — mede quanto das vagas ofertadas
  foi efetivamente preenchido por escolha.
- **Normalização de DRE**: ``_chave_dre`` normaliza o nome da Diretoria
  Regional de Educação (maiúsculas, sem acentuação/pontuação variável) para
  garantir que registros da mesma DRE vindos de fontes diferentes sejam
  agrupados corretamente na comparação.

Histórico de classificação em reconvocação
------------------------------------------------

Quando um candidato é reconvocado (``foi_convocado=True`` em uma convocação
posterior à original), ``aplicar_historico_classificacao()`` recupera a
classificação/ordem de chamada que ele tinha na convocação anterior, em vez
de usar uma classificação recalculada do zero — preservando a posição
histórica do candidato nos relatórios de reconvocação e de resultado de
escolha.

Identificação de lacunas de classificação
------------------------------------------------

``AtaEscolhaService._identificar_lacunas()`` percorre a sequência de
classificação dos candidatos de um cargo e aponta números de ordem
ausentes (candidatos eliminados, desistentes ou não convocados) — essa
lista de lacunas é o que compõe as seções "não compareceram"/"não
convocados" da Ata de Escolha, sem exigir que o operador identifique essas
ausências manualmente.

Separação por categoria (GERAL / NNA / PCD)
------------------------------------------------

``AtaEscolhaService._separar_por_tipo()`` divide os candidatos de um cargo
entre as categorias **Geral**, **NNA** (Negros, Negras e Afrodescendentes) e
**PCD** (Pessoa com Deficiência), refletindo a reserva de vagas por
categoria já definida no edital do concurso — cada categoria é listada
separadamente nos documentos que exigem essa segregação.

Auditoria
------------

Todos os modelos do app ``relatorios`` são registrados via
``django-auditlog``, garantindo histórico completo de criação e alteração
de cada configuração de relatório, parametrização visual e relatório
gerado.
