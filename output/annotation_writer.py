"""
Annotation Writer
Adds footer notes/comments to PDF/PPT/DOCX files with gap information and principal notes.
For PDF/PPT: adds footer annotations
For DOCX: adds Word comments
"""

import os
from typing import Dict, List, Optional

from pydantic_classes import AggregatedResults


def add_footer_notes(file_path: str, chunk: str, annotation: str) -> None:
    """
    Add footer annotation/comment to specific page/slide/paragraph.

    Format: "⚠️ GAP: X% failed. Note: [principal_notes]"

    Args:
        file_path: Path to PDF/PPT/DOCX file
        chunk: Chunk ID (e.g., "chunk_3")
        annotation: Annotation text to add
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        _add_pdf_footer(file_path, chunk, annotation)
    elif ext in [".ppt", ".pptx"]:
        _add_ppt_footer(file_path, chunk, annotation)
    elif ext in [".doc", ".docx"]:
        _add_docx_comment(file_path, chunk, annotation)
    else:
        raise ValueError(f"Unsupported file type for annotations: {ext}")


def _add_pdf_footer(file_path: str, chunk_id: str, annotation: str) -> None:
    """Add footer note to PDF page."""
    import fitz

    # Extract page number from chunk_id (e.g., "chunk_3" -> 3)
    page_num = int(chunk_id.split("_")[1]) - 1  # 0-indexed

    doc = fitz.open(file_path)
    if page_num >= len(doc):
        doc.close()
        return

    page = doc[page_num]
    rect = page.rect

    # Draw white background box at bottom
    footer_height = 40
    footer_rect = fitz.Rect(
        rect.x0 + 10, rect.y1 - footer_height - 10, rect.x1 - 10, rect.y1 - 10
    )
    page.draw_rect(footer_rect, color=(1, 1, 1), fill=(1, 1, 1), width=1)

    # Add text
    text_point = fitz.Point(rect.x0 + 15, rect.y1 - 25)
    page.insert_text(
        text_point, annotation, fontsize=10, color=(0, 0, 0), fontname="helv"
    )

    doc.save(file_path)
    doc.close()


def _add_ppt_footer(file_path: str, chunk_id: str, annotation: str) -> None:
    """Add footer note to PPT slide."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt

    # Extract slide number from chunk_id (e.g., "chunk_3" -> 3)
    slide_num = int(chunk_id.split("_")[1]) - 1  # 0-indexed

    prs = Presentation(file_path)
    if slide_num >= len(prs.slides):
        return

    slide = prs.slides[slide_num]
    slide_height = prs.slide_height

    # Add white background box
    box_width = prs.slide_width - Inches(0.5)
    box_height = Inches(0.6)
    box_left = Inches(0.25)
    box_top = slide_height - box_height - Inches(0.25)

    footer_box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, box_left, box_top, box_width, box_height
    )
    footer_box.fill.solid()
    footer_box.fill.fore_color.rgb = RGBColor(255, 255, 255)
    footer_box.line.color.rgb = RGBColor(0, 0, 0)
    footer_box.line.width = Pt(1)

    # Add text
    text_frame = footer_box.text_frame
    text_frame.text = annotation
    text_frame.word_wrap = True
    paragraph = text_frame.paragraphs[0]
    paragraph.font.size = Pt(10)
    paragraph.font.color.rgb = RGBColor(0, 0, 0)

    prs.save(file_path)


def _add_docx_comment(file_path: str, chunk_id: str, annotation: str) -> None:
    """Add comment to DOCX paragraph."""
    from docx import Document

    # Extract paragraph number from chunk_id (e.g., "chunk_3" -> 3)
    para_num = int(chunk_id.split("_")[1])

    doc = Document(file_path)

    # Track paragraph index (only count non-empty paragraphs)
    para_idx = 0

    for paragraph in doc.paragraphs:
        if not paragraph.text.strip():
            continue

        para_idx += 1
        if para_idx == para_num and paragraph.runs:
            # Add comment anchored to the paragraph's runs
            doc.add_comment(
                runs=paragraph.runs,
                text=annotation,
                author="SIMS Teacher",
                initials="ST",
            )
            break

    doc.save(file_path)


def add_gap_annotations(
    file_path: str,
    aggregated_results: AggregatedResults,
    chunks: Optional[List[Dict]] = None,
) -> None:
    """
    Add footer annotations/comments for all gap chunks.

    Args:
        file_path: Path to PDF/PPT/DOCX file
        aggregated_results: AggregatedResults with gap information
        chunks: Optional list of chunk dictionaries (not currently used but kept for compatibility)
    """
    avg_understanding = aggregated_results.per_chunk_avg_understanding
    gap_chunks = aggregated_results.gap_chunks
    common_doubts = aggregated_results.common_doubts
    principal_notes = aggregated_results.principal_notes

    for chunk_id in gap_chunks:
        understanding = avg_understanding.get(chunk_id, 0.0)
        failure_rate = (1 - understanding / 5) * 100 if understanding > 0 else 100

        # Get principal notes for this chunk (if available)
        notes = ""
        if principal_notes:
            notes = principal_notes[0] if principal_notes else ""

        annotation = f"⚠️ GAP: {failure_rate:.0f}% failed. Note: {notes[:100]}"

        add_footer_notes(file_path, chunk_id, annotation)
