# PDF OCR reutilizável

Este repositório contém um módulo simples para converter PDFs escaneados em PDFs pesquisáveis usando Tesseract OCR.

Instalação

1. Crie e ative um ambiente virtual (recomendado).
2. Instale dependências:

```bash
pip install -r requirements.txt
```

Observações:
- Em Windows, instale o Tesseract OCR separadamente (ex.: UB Mannheim build).
- O Poppler é necessário para `pdf2image`. O módulo tenta baixar automaticamente uma cópia do Poppler.

Uso como módulo

```py
from pdf_ocr import ocr_pdf_to_searchable_pdf

ocr_pdf_to_searchable_pdf(Path('entrada.pdf'), Path('saida'), dpi=300, lang='por')
```

Extrair texto de um PDF pesquisável

```py
from pdf_ocr import extract_text, save_text
texto = extract_text(Path('LAB/entrada.pdf'))
save_text(texto, Path('LAB/entrada.txt'))
```

Uso via CLI

```bash
python -m pdf_ocr -i /caminho/para/pdfs -o /caminho/para/saida --lang por --dpi 300
```

Salvar texto extraído junto ao PDF (opcional):

```bash
python -m pdf_ocr -i /caminho/para/pdfs -o /caminho/para/saida --lang por --dpi 300 --save-text
```

Arquivo principal do exemplo: `converter_pdf_ocr_lab2py.py` (usa o módulo `pdf_ocr`).

