"""
Document Parser
Extracts text from PDF, PPT/PPTX, and DOC/DOCX files.
Returns list of ChunkDetails objects (1 slide/page/paragraph = 1 chunk).
"""

import os
import re
import subprocess
import tempfile
from typing import List

from pydantic_classes import ChunkDetails

# Magic bytes: OLE2/Composite Document (old .ppt), ZIP (new .pptx)
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0"
_ZIP_MAGIC = b"PK"


def _detect_actual_format(file_path: str) -> str:
    """Detect actual file format from magic bytes (handles mislabeled extensions)."""
    with open(file_path, "rb") as f:
        header = f.read(4)
    if header.startswith(_ZIP_MAGIC):
        return "pptx"
    if header.startswith(_OLE2_MAGIC):
        return "ppt"
    return "unknown"


def _convert_ppt_to_pptx(file_path: str) -> str:
    """Convert old .ppt to .pptx using LibreOffice. Returns path to converted file."""
    out_dir = tempfile.mkdtemp(prefix="sims_teacher_convert_")
    try:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pptx",
                "--outdir",
                out_dir,
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed: {result.stderr or result.stdout}"
            )
        base = os.path.splitext(os.path.basename(file_path))[0]
        converted = os.path.join(out_dir, f"{base}.pptx")
        if not os.path.exists(converted):
            raise RuntimeError(f"Converted file not found: {converted}")
        return converted
    except FileNotFoundError:
        raise FileNotFoundError(
            "LibreOffice is not installed. Install it (e.g. apt install libreoffice) to support old .ppt files, "
            "or save your file as .pptx (PowerPoint 2007+ format) and re-upload."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("LibreOffice conversion timed out.")


def parse_document(file_path: str) -> List[ChunkDetails]:
    """
    Parse document and return list of ChunkDetails objects.
    For PPTs: 1 slide = 1 chunk
    For PDFs/DOCs: 1 page or 1 paragraph = 1 chunk

    Args:
        file_path: Path to the document file

    Returns:
        List of ChunkDetails objects
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext in [".ppt", ".pptx"]:
        return _parse_ppt(file_path)
    elif ext in [".doc", ".docx"]:
        return _parse_doc(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(file_path: str) -> List[ChunkDetails]:
    """Parse PDF file using PyMuPDF. Returns chunks (1 page = 1 chunk)."""
    import fitz

    doc = fitz.open(file_path)
    chunks = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            chunk_id = f"chunk_{page_num}"
            page_range = f"Page {page_num}"
            chunks.append(_create_chunk_details(chunk_id, text.strip(), page_range))

    doc.close()
    return chunks


def _parse_ppt(file_path: str) -> List[ChunkDetails]:
    """Parse PowerPoint file using python-pptx. Returns chunks (1 slide = 1 chunk)."""
    from pptx import Presentation
    from pptx.exc import PackageNotFoundError

    actual = _detect_actual_format(file_path)
    path_to_use = file_path
    temp_converted = None

    if actual == "ppt":
        # File has .pptx extension but is actually old .ppt format
        path_to_use = _convert_ppt_to_pptx(file_path)
        temp_converted = path_to_use

    try:
        prs = Presentation(path_to_use)
        chunks = []

        for slide_num, slide in enumerate(prs.slides, start=1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            if slide_text:
                content = "\n".join(slide_text)
                chunk_id = f"chunk_{slide_num}"
                page_range = f"Slide {slide_num}"
                chunks.append(_create_chunk_details(chunk_id, content, page_range))

        return chunks
    except PackageNotFoundError:
        if actual == "unknown":
            raise ValueError(
                "File is not a valid PowerPoint file. Ensure it is a .ppt or .pptx file."
            )
        raise
    finally:
        if temp_converted:
            try:
                import shutil

                shutil.rmtree(os.path.dirname(temp_converted), ignore_errors=True)
            except Exception:
                pass


def _parse_doc(file_path: str) -> List[ChunkDetails]:
    """Parse Word document using python-docx. Returns chunks (1 paragraph = 1 chunk)."""
    from docx import Document

    doc = Document(file_path)
    chunks = []

    for para_num, para in enumerate(doc.paragraphs, start=1):
        if para.text.strip():
            chunk_id = f"chunk_{para_num}"
            page_range = f"Paragraph {para_num}"
            chunks.append(
                _create_chunk_details(chunk_id, para.text.strip(), page_range)
            )

    return chunks


def _create_chunk_details(chunk_id: str, content: str, page_range: str) -> ChunkDetails:
    """Create ChunkDetails object with extracted metadata."""
    # Check for formulas and code (useful metadata)
    has_formula = bool(re.search(r"[=+\-*/^()]+", content))
    has_code = bool(re.search(r"[{};]|def |class |import |print\(", content))

    return ChunkDetails(
        chunk_id=chunk_id,
        content=content,
        difficulty_index=0.0,  # Placeholder - will be populated post-simulation
        page_range=page_range,
        has_formula=has_formula,
        has_code=has_code,
    )
