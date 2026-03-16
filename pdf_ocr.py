"""
Módulo reutilizável para OCR em PDFs (gera PDFs pesquisáveis).

Funções públicas principais:
- buscar_tesseract_instalado() -> str
- obter_caminho_poppler(base_dir: Path) -> Optional[Path]
- converter_pdf(caminho_pdf: Path, pasta_saida: Path, poppler_path=None, tesseract_cmd="tesseract", dpi=300, lang='por') -> bool
- verificar_extracao(caminho_pdf: Path) -> int
- extract_text(pdf_path: Path) -> str
- save_text(text: str, out_path: Path) -> None

Também expõe um CLI quando executado como módulo.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional

from pdf2image import convert_from_path
import pypdf


def buscar_tesseract_instalado() -> str:
    caminhos_comuns = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]
    for caminho in caminhos_comuns:
        caminho = os.path.expandvars(caminho)
        if os.path.exists(caminho):
            return caminho

    # fallback para PATH
    from shutil import which

    found = which("tesseract")
    return found or "tesseract"


def obter_caminho_poppler(base_dir: Path) -> Optional[Path]:
    poppler_dir = base_dir / "poppler_bin"

    # Verifica se já existe
    for p in poppler_dir.rglob("pdftoppm.exe"):
        return p.parent

    # Tenta baixar automaticamente (Windows releases)
    poppler_dir.mkdir(parents=True, exist_ok=True)
    zip_path = poppler_dir / "poppler_temp.zip"
    url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"

    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(poppler_dir)
        try:
            zip_path.unlink()
        except Exception:
            pass

        for p in poppler_dir.rglob("pdftoppm.exe"):
            return p.parent
    except Exception:
        return None


def converter_pdf(
    caminho_pdf: Path,
    pasta_saida: Path,
    poppler_path: Optional[Path] = None,
    tesseract_cmd: str = "tesseract",
    dpi: int = 300,
    lang: str = "por",
    verbose: bool = True,
) -> bool:
    """Converte um PDF escaneado em PDF pesquisável usando Tesseract.

    Retorna True em sucesso, False em erro.
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)
    nome_saida = pasta_saida / caminho_pdf.name

    try:
        if verbose:
            print(f"Processing {caminho_pdf.name} (dpi={dpi}, lang={lang})")
        paginas = convert_from_path(str(caminho_pdf), dpi=dpi, poppler_path=str(poppler_path) if poppler_path else None)
        pdfs_paginas: List[Path] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for i, pagina in enumerate(paginas, start=1):
                if verbose:
                    print(f"  → Página {i}/{len(paginas)}")
                img_path = Path(tmpdir) / f"pagina_{i:04d}"
                img_png = img_path.with_suffix(".png")
                pagina.save(str(img_png), "PNG")

                # Executa Tesseract para gerar PDF por página
                proc = subprocess.run([tesseract_cmd, str(img_png), str(img_path), "-l", lang, "pdf"], capture_output=True, text=True)
                if proc.returncode != 0:
                    if verbose:
                        print(f"    Erro Tesseract (página {i}): {proc.stderr.strip()}")
                    return False

                pdfs_paginas.append(img_path.with_suffix(".pdf"))

            # Junta os PDFs de páginas
            escritor = pypdf.PdfWriter()
            for pdf_pag in pdfs_paginas:
                leitor = pypdf.PdfReader(str(pdf_pag))
                for pagina_obj in leitor.pages:
                    escritor.add_page(pagina_obj)

            with open(nome_saida, "wb") as f:
                escritor.write(f)

        if verbose:
            print(f"  ✓ Salvo: {nome_saida}")
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def verificar_extracao(caminho_pdf: Path) -> int:
    try:
        leitor = pypdf.PdfReader(str(caminho_pdf))
        texto = ""
        for pag in leitor.pages:
            texto += pag.extract_text() or ""
        return len(texto.strip())
    except Exception:
        return 0


def extract_text(pdf_path: Path) -> str:
    """Extrai e retorna o texto de um PDF pesquisável."""
    try:
        leitor = pypdf.PdfReader(str(pdf_path))
        texto = ""
        for pag in leitor.pages:
            texto += pag.extract_text() or ""
        return texto
    except Exception:
        return ""


def save_text(text: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")


def ocr_pdf_to_searchable_pdf(
    pdf_path: Path,
    out_dir: Path,
    dpi: int = 300,
    lang: str = "por",
    auto_poppler: bool = True,
    tesseract_cmd: Optional[str] = None,
) -> bool:
    base = pdf_path.parent
    poppler = None
    if auto_poppler:
        poppler = obter_caminho_poppler(base)

    t_cmd = tesseract_cmd or buscar_tesseract_instalado()
    return converter_pdf(pdf_path, out_dir, poppler_path=poppler, tesseract_cmd=t_cmd, dpi=dpi, lang=lang)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OCR PDF -> PDF pesquisável")
    parser.add_argument("--input", "-i", required=True, help="Arquivo PDF ou pasta com PDFs")
    parser.add_argument("--output", "-o", required=False, help="Pasta de saída (opcional)")
    parser.add_argument("--lang", default="por", help="Idioma do Tesseract (ex: por, eng)")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--save-text", action="store_true", help="Salvar texto extraído (.txt)")
    args = parser.parse_args()

    entrada = Path(args.input)
    saida = Path(args.output) if args.output else (entrada.parent / "LAB" if entrada.is_file() else entrada / "LAB")
    saida.mkdir(parents=True, exist_ok=True)

    if entrada.is_file():
        ok = ocr_pdf_to_searchable_pdf(entrada, saida, dpi=args.dpi, lang=args.lang, tesseract_cmd=None)
        print("OK" if ok else "Falha")
        if ok and args.save_text:
            texto = extract_text(saida / entrada.name)
            out_txt = (saida / entrada.with_suffix('.txt').name)
            save_text(texto, out_txt)
            print(f"Texto salvo em: {out_txt}")
    else:
        pdfs = sorted(entrada.glob("*.pdf"))
        for p in pdfs:
            print(f"Processando {p.name}...")
            ok = ocr_pdf_to_searchable_pdf(p, saida, dpi=args.dpi, lang=args.lang, tesseract_cmd=None)
            print("  OK" if ok else "  Falha")
            if ok and args.save_text:
                texto = extract_text(saida / p.name)
                out_txt = saida / p.with_suffix('.txt').name
                save_text(texto, out_txt)
                print(f"  Texto salvo em: {out_txt}")
