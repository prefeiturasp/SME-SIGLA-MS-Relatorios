Estrutura do Projeto
=======================

Visão da árvore principal
-----------------------------

.. code-block:: text

   relatorios/
   ├── apps/
   │   ├── core/
   │   └── relatorios/
   ├── config/
   ├── docs/
   ├── media/
   ├── requirements/
   ├── manage.py
   ├── Makefile
   └── pyproject.toml

Pasta ``apps/``
-------------------

``apps/core/``
~~~~~~~~~~~~~~~~~

**O que faz:** concentra recursos compartilhados entre os demais apps.

**Para que serve:** evitar duplicação dos campos comuns a todo modelo de
domínio do projeto.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Arquivo
     - Função
   * - ``models.py``
     - Define o modelo abstrato base herdado pelos modelos do app
       ``relatorios``

``apps/relatorios/``
~~~~~~~~~~~~~~~~~~~~~~~~

**O que faz:** gera os documentos formais do processo de convocação (laudas,
atas, súmulas, listagens) a partir de dados consultados em outros
microsserviços da SIGLA.

**Para que serve:** ponto único de geração de relatórios, com formato,
cabeçalho e identidade visual padronizados.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Camada / arquivo
     - Função
   * - ``models/``
     - ``Relatorio``, ``ConfiguracaoRelatorio``, ``Parametrizacao``,
       ``constants.py`` (``TIPOS_RELATORIOS``)
   * - ``repository.py``
     - Única camada autorizada a executar queries ORM sobre esses modelos
   * - ``services/base/``
     - ``RelatorioBase`` — classe abstrata com o contrato ``gerar()`` e
       utilitários comuns (``render_to_pdf``, tratamento de cabeçalho HTML)
   * - ``services/factory/``
     - ``RelatorioFactory`` — despacha o tipo de relatório para a classe
       geradora correspondente
   * - ``services/relatorios/``
     - Dez classes geradoras concretas, uma por tipo de documento (ata de
       escolha, laudas, súmulas, listagens, resultado de escolha)
   * - ``services/*_api_service.py``
     - Integração HTTP com MS-Processos, MS-Escolhas, MS-Convocacao,
       MS-Candidatos, MS-Concursos e MS-Agendas
   * - ``serializers/``
     - Validação de entrada e formatação de saída, por recurso
   * - ``api/views/``
     - ViewSets DRF, um arquivo por recurso
   * - ``templates/relatorios/``
     - Templates HTML usados na renderização de cada documento (base para
       HTML e para conversão em PDF via WeasyPrint)
   * - ``management/commands/``
     - ``criar_relatorios`` e ``limpar_relatorios``

**Exemplo:** ``Relatorio`` guarda o histórico de cada documento gerado —
tipo, processo relacionado, formato solicitado e status.

Pasta ``config/``
---------------------

Configuração do projeto Django.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Arquivo
     - Função
   * - ``settings.py``
     - Configurações de produção/desenvolvimento
   * - ``settings_test.py``
     - Configurações usadas pela suíte de testes (banco SQLite em memória)
   * - ``urls.py``
     - Roteamento raiz, healthcheck e schema OpenAPI/Swagger
   * - ``wsgi.py``
     - Ponto de entrada WSGI

Pasta ``requirements/``
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Propósito
   * - ``base.txt``
     - Dependências de produção: Django, DRF, PostgreSQL, sigla-sdk,
       WeasyPrint, python-docx, openpyxl, entre outras
   * - ``local.txt``
     - Inclui ``base.txt`` e adiciona ferramentas de desenvolvimento e teste
       (pytest, ruff, mypy, sphinx)
   * - ``production.txt``
     - Inclui ``base.txt`` e adiciona o servidor WSGI (gunicorn)

Pasta ``docs/``
-------------------

Documentação Sphinx do módulo — este mesmo material, gerado em HTML via
``make docs``.

Arquivos na raiz
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Função
   * - ``manage.py``
     - Utilitário de linha de comando do Django
   * - ``Makefile``
     - Atalhos de desenvolvimento (``test``, ``lint``, ``format``, ``docs``, etc.)
   * - ``pyproject.toml``
     - Configuração de ferramentas (ruff, mypy)

API — endpoints principais (referência)
-------------------------------------------

Todas as rotas abaixo estão sob o prefixo ``/api/v1/``.

.. list-table:: relatorios
   :header-rows: 1
   :widths: 50 50

   * - Rota
     - Recurso
   * - ``relatorios/``
     - Geração e listagem de relatórios
   * - ``parametrizacao/``
     - Parametrização visual (logotipo, cabeçalho padrão)
   * - ``personalizacao/``
     - Personalização de cabeçalho/rodapé por configuração de relatório
   * - ``extracao-dados/``
     - Extração de dados comparativos (vagas x escolhas)
