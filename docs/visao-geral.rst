Visão Geral
===========

O que é este módulo?
---------------------

O **Módulo de Relatórios** (MS-RELATORIOS) é o microsserviço da SIGLA
responsável por gerar todos os documentos formais usados ao longo do
processo de convocação de servidores da SME: laudas, atas, súmulas e
listagens que registram vagas ofertadas, escolhas realizadas e o resultado
de cada etapa do processo, nos formatos HTML, PDF, DOCX e XLSX.

Ele não é dono dos dados que apresenta — busca informações já persistidas em
outros microsserviços da SIGLA, monta o documento a partir de um modelo
(template) e devolve o arquivo pronto para download.

Para que serve?
----------------

Cada etapa do processo de convocação (oferta de vagas, sessão de escolha,
resultado, reconvocação) precisa ser formalizada em documentos que possam
ser impressos, assinados e arquivados pelas Diretorias Regionais de Educação
(DREs) e pela área central. Este módulo existe para que esses documentos
sejam gerados de forma **padronizada e consistente**, sem que cada DRE
precise montar manualmente planilhas ou textos a partir dos dados brutos.

Onde ele se encaixa no ecossistema SIGLA?
-------------------------------------------

Todas as integrações são feitas via HTTP, consultando os demais
microsserviços da SIGLA para montar o conteúdo de cada relatório.

.. list-table:: Integrações externas
   :header-rows: 1
   :widths: 25 20 55

   * - Sistema
     - Direção
     - Papel neste módulo
   * - MS-Processos
     - Consulta
     - Dados do processo de convocação (cargo, edital, cronograma)
   * - MS-Escolhas
     - Consulta
     - Vagas ofertadas e escolhas registradas por candidato/unidade
   * - MS-Convocacao
     - Consulta
     - Situação de convocação/reconvocação de cada candidato
   * - MS-Candidatos
     - Consulta
     - Dados cadastrais e de classificação dos candidatos
   * - MS-Concursos
     - Consulta
     - Dados do concurso e dos cargos vinculados
   * - MS-Agendas
     - Consulta
     - Sessões de escolha e seus horários/locais

Exemplo prático do dia a dia
-------------------------------

**Gerando um relatório:**

1. A área de negócio solicita um relatório informando o ``tipo`` (por
   exemplo ``ATA_ESCOLHA``) e o ``processo_uuid`` via
   ``POST /api/v1/relatorios/``.
2. ``RelatorioFactory.obter_relatorio(tipo_slug)`` identifica a classe
   geradora correspondente ao tipo informado, já carregando a configuração
   de cabeçalho/rodapé (``ConfiguracaoRelatorio``) e a parametrização visual
   vigente (``Parametrizacao`` — logotipo, cabeçalho padrão).
3. A classe geradora busca os dados necessários nos microsserviços listados
   acima, monta o contexto do template e chama ``gerar()``.
4. O documento é produzido no formato solicitado — HTML direto,
   ``render_to_pdf`` (WeasyPrint), ou geração via ``python-docx``/
   ``openpyxl`` para DOCX/XLSX — e devolvido para download.

Stack tecnológica (referência rápida)
----------------------------------------

- **Django 5.2** + **Django REST Framework** — API HTTP
- **PostgreSQL** — banco de dados relacional
- **sigla-sdk** — cliente HTTP compartilhado entre microsserviços SIGLA
- **WeasyPrint** — renderização de HTML para PDF
- **python-docx** — geração de documentos Word
- **openpyxl** — geração de planilhas Excel
- **django-auditlog** — histórico de alterações em todos os modelos
