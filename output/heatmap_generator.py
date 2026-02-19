"""
Heatmap Generator
Overlays color-coded heatmaps on PDF/PPT/DOCX files based on student understanding scores.
Only handles color overlays/highlighting. Use annotation_writer.py for adding notes/comments.
"""

import os
import shutil

from pydantic_classes import AggregatedResults


def generate_heatmap(original_file: str, aggregated_results: AggregatedResults) -> str:
    """
    Generate heatmap overlay on original PDF/PPT/DOCX file based on avg_understanding scores.

    Color scheme:
    - avg_understanding < 2: RED (critical confusion)
    - avg_understanding < 3: ORANGE/YELLOW (caution)
    - avg_understanding >= 3: GREEN (clear)

    Args:
        original_file: Path to original PDF/PPT/DOCX file
        aggregated_results: AggregatedResults with per_chunk_avg_understanding

    Returns:
        Path to annotated file
    """
    if not os.path.exists(original_file):
        raise FileNotFoundError(f"File not found: {original_file}")

    ext = os.path.splitext(original_file)[1].lower()

    # Create output filename
    base_name = os.path.splitext(original_file)[0]
    output_file = f"{base_name}_annotated{ext}"

    # Copy original file
    shutil.copy2(original_file, output_file)

    if ext == ".pdf":
        _add_pdf_heatmap(output_file, aggregated_results)
    elif ext in [".ppt", ".pptx"]:
        _add_ppt_heatmap(output_file, aggregated_results)
    elif ext in [".doc", ".docx"]:
        _add_docx_heatmap(output_file, aggregated_results)
    else:
        raise ValueError(f"Unsupported file type for heatmap: {ext}")

    return output_file


def _add_pdf_heatmap(file_path: str, aggregated_results: AggregatedResults) -> None:
    """Add color overlay to PDF pages based on understanding scores."""
    import fitz

    doc = fitz.open(file_path)
    avg_understanding = aggregated_results.per_chunk_avg_understanding

    for page_num, page in enumerate(doc, start=1):
        chunk_id = f"chunk_{page_num}"
        understanding = avg_understanding.get(chunk_id, 3.0)

        # Determine color
        if understanding < 2:
            color = (1.0, 0.2, 0.2)  # RED
        elif understanding < 3:
            color = (1.0, 0.6, 0.0)  # ORANGE
        else:
            color = (0.2, 0.8, 0.2)  # GREEN

        # Add semi-transparent overlay rectangle
        rect = page.rect
        overlay = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
        page.draw_rect(overlay, color=color, fill=color, width=0, fill_opacity=0.3)

    doc.save(file_path)
    doc.close()


def _add_ppt_heatmap(file_path: str, aggregated_results: AggregatedResults) -> None:
    """Add color overlay to PPT slides based on understanding scores."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor

    prs = Presentation(file_path)
    avg_understanding = aggregated_results.per_chunk_avg_understanding

    for slide_num, slide in enumerate(prs.slides, start=1):
        chunk_id = f"chunk_{slide_num}"
        understanding = avg_understanding.get(chunk_id, 3.0)

        # Determine color (RGB values 0-255)
        if understanding < 2:
            color_rgb = (255, 51, 51)  # RED
        elif understanding < 3:
            color_rgb = (255, 153, 0)  # ORANGE
        else:
            color_rgb = (51, 204, 51)  # GREEN

        # Get slide dimensions
        slide_width = prs.slide_width
        slide_height = prs.slide_height

        # Add semi-transparent rectangle overlay (1 = MSO_AUTO_SHAPE_TYPE.RECTANGLE)
        overlay = slide.shapes.add_shape(1, 0, 0, slide_width, slide_height)
        overlay.fill.solid()
        overlay.fill.fore_color.rgb = RGBColor(*color_rgb)
        overlay.fill.transparency = 0.7  # 70% transparent
        overlay.line.fill.background()  # No border

        # Move overlay to back
        slide.shapes._spTree.remove(overlay._element)
        slide.shapes._spTree.insert(2, overlay._element)

    prs.save(file_path)


def _add_docx_heatmap(file_path: str, aggregated_results: AggregatedResults) -> None:
    """Add color highlighting to DOCX paragraphs based on understanding scores."""
    from docx import Document
    from docx.enum.text import WD_COLOR_INDEX

    doc = Document(file_path)
    avg_understanding = aggregated_results.per_chunk_avg_understanding

    # Track paragraph index (only count non-empty paragraphs)
    para_idx = 0

    for paragraph in doc.paragraphs:
        if not paragraph.text.strip():
            continue

        para_idx += 1
        chunk_id = f"chunk_{para_idx}"
        understanding = avg_understanding.get(chunk_id, 3.0)

        # Determine highlight color
        if understanding < 2:
            highlight_color = WD_COLOR_INDEX.RED
        elif understanding < 3:
            highlight_color = WD_COLOR_INDEX.YELLOW  # Using YELLOW as ORANGE substitute
        else:
            highlight_color = WD_COLOR_INDEX.GREEN

        # Highlight all runs in the paragraph that have text
        for run in paragraph.runs:
            if run.text.strip():  # Only highlight runs with actual text
                run.font.highlight_color = highlight_color

    doc.save(file_path)
