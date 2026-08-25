"""Configuração do Sphinx do Módulo de Relatórios."""

project = "Módulo de Relatórios"
author = "SME - SIGLA"
copyright = "2026, SME - SIGLA"

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "pt_BR"

html_theme = "alabaster"

html_theme_options = {
    "description": (
        "Documentação do módulo de geração de relatórios da SIGLA."
    ),
    "github_button": False,
}
