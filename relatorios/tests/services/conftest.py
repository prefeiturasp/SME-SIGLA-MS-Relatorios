"""
Configuração específica para testes de services.
Mocka dependências opcionais antes dos imports.
"""

import sys
from unittest.mock import MagicMock

# Mock weasyprint antes de importar qualquer coisa que dependa dele
if "weasyprint" not in sys.modules:
    mock_weasyprint = MagicMock()
    mock_html = MagicMock()
    mock_weasyprint.HTML = mock_html
    sys.modules["weasyprint"] = mock_weasyprint
