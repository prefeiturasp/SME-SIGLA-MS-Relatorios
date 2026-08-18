"""Configuração específica para testes de relatórios.

Mocka dependências opcionais antes dos imports.
"""

import sys
from collections import defaultdict
from unittest.mock import MagicMock

# Mock weasyprint antes de importar qualquer coisa que dependa dele
if "weasyprint" not in sys.modules:
    mock_weasyprint = MagicMock()
    mock_html = MagicMock()
    mock_weasyprint.HTML = mock_html
    sys.modules["weasyprint"] = mock_weasyprint

# Mock docx antes de importar qualquer coisa que dependa dele
if "docx" not in sys.modules:
    mock_docx = MagicMock()
    mock_document = MagicMock()
    mock_docx.Document = mock_document

    # Mock docx.shared
    mock_shared = MagicMock()
    mock_shared.Pt = MagicMock(return_value=MagicMock())
    mock_shared.RGBColor = MagicMock(return_value=MagicMock())
    mock_shared.Inches = MagicMock(return_value=MagicMock())
    mock_docx.shared = mock_shared

    # Mock docx.enum.text
    mock_enum_text = MagicMock()
    mock_enum_text.WD_ALIGN_PARAGRAPH = MagicMock()
    mock_enum_text.WD_ALIGN_PARAGRAPH.CENTER = "CENTER"
    mock_enum_text.WD_ALIGN_PARAGRAPH.LEFT = "LEFT"

    # Mock docx.enum.section
    mock_enum_section = MagicMock()
    mock_wd_orient = MagicMock()
    mock_wd_orient.LANDSCAPE = 1
    mock_wd_orient.PORTRAIT = 0
    mock_enum_section.WD_ORIENT = mock_wd_orient

    mock_docx.enum = MagicMock()
    mock_docx.enum.text = mock_enum_text
    mock_docx.enum.section = mock_enum_section

    # Mock docx.oxml
    mock_oxml = MagicMock()
    mock_oxml.ns = MagicMock()
    mock_oxml.ns.qn = MagicMock(return_value="w:shd")
    mock_oxml.OxmlElement = MagicMock(return_value=MagicMock())
    mock_docx.oxml = mock_oxml

    sys.modules["docx"] = mock_docx
    sys.modules["docx.shared"] = mock_shared
    sys.modules["docx.enum"] = mock_docx.enum
    sys.modules["docx.enum.text"] = mock_enum_text
    sys.modules["docx.enum.section"] = mock_enum_section
    sys.modules["docx.oxml"] = mock_oxml
    sys.modules["docx.oxml.ns"] = mock_oxml.ns

# Mock openpyxl antes de importar qualquer coisa que dependa dele
if "openpyxl" not in sys.modules:
    mock_openpyxl = MagicMock()
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_ws.column_dimensions = defaultdict(MagicMock)
    mock_wb.active = mock_ws
    mock_wb.save = MagicMock(side_effect=lambda buf: buf.write(b"XLSX"))
    mock_openpyxl.Workbook = MagicMock(return_value=mock_wb)

    mock_styles = MagicMock()
    mock_styles.Font = MagicMock(return_value=MagicMock())
    mock_styles.PatternFill = MagicMock(return_value=MagicMock())
    mock_styles.Alignment = MagicMock(return_value=MagicMock())
    mock_styles.Border = MagicMock(return_value=MagicMock())
    mock_styles.Side = MagicMock(return_value=MagicMock())

    mock_drawing = MagicMock()
    mock_drawing_image = MagicMock()
    mock_drawing_image.Image = MagicMock(return_value=MagicMock())
    mock_drawing.image = mock_drawing_image

    sys.modules["openpyxl"] = mock_openpyxl
    sys.modules["openpyxl.styles"] = mock_styles
    sys.modules["openpyxl.drawing"] = mock_drawing
    sys.modules["openpyxl.drawing.image"] = mock_drawing_image
