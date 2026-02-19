"""
Report Exporter
Exports aggregated results as JSON and PDF reports.
"""

import json
import os
from datetime import datetime
from typing import Dict, List

from pydantic_classes import AggregatedResults


def export_json_report(results: AggregatedResults, path: str) -> None:
    """
    Export aggregated results as JSON report.

    Args:
        results: AggregatedResults to export
        path: Output file path (should end with .json)
    """
    report_data = {
        "total_runs": results.total_runs,
        "per_chunk_avg_understanding": results.per_chunk_avg_understanding,
        "gap_chunks": results.gap_chunks,
        "common_doubts": results.common_doubts,
        "principal_notes": results.principal_notes,
        "exported_at": datetime.now().isoformat(),
    }

    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def export_pdf_report(results: AggregatedResults, path: str) -> None:
    """
    Export aggregated results as PDF report.

    Args:
        results: AggregatedResults to export
        path: Output file path (should end with .pdf)
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    doc = SimpleDocTemplate(path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("Simulation Results Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))

    # Summary
    summary_text = f"Total Runs: {results.total_runs}<br/>"
    summary_text += f"Gap Chunks Identified: {len(results.gap_chunks)}"
    summary = Paragraph(summary_text, styles["Normal"])
    story.append(summary)
    story.append(Spacer(1, 0.3 * inch))

    # Per-chunk understanding scores
    story.append(Paragraph("Per-Chunk Average Understanding", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))

    # Create table for understanding scores
    table_data = [["Chunk ID", "Avg Understanding", "Status"]]
    for chunk_id, understanding in sorted(results.per_chunk_avg_understanding.items()):
        if understanding < 2:
            status = "Critical"
        elif understanding < 3:
            status = "Caution"
        else:
            status = "Clear"
        table_data.append([chunk_id, f"{understanding:.2f}", status])

    table = Table(table_data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Gap chunks
    if results.gap_chunks:
        story.append(Paragraph("Gap Chunks (>40% Failure Rate)", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        for chunk_id in results.gap_chunks:
            understanding = results.per_chunk_avg_understanding.get(chunk_id, 0.0)
            gap_text = f"<b>{chunk_id}</b>: Avg Understanding = {understanding:.2f}"
            story.append(Paragraph(gap_text, styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

    # Common doubts
    if results.common_doubts:
        story.append(Paragraph("Common Doubts by Chunk", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        for chunk_id, doubts in results.common_doubts.items():
            if doubts:
                doubt_text = f"<b>{chunk_id}</b>:"
                story.append(Paragraph(doubt_text, styles["Normal"]))
                for doubt in doubts[:5]:  # Limit to 5 doubts per chunk
                    story.append(Paragraph(f"  • {doubt}", styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

    # Principal notes
    if results.principal_notes:
        story.append(Paragraph("Principal's Notes", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        for note in results.principal_notes:
            story.append(Paragraph(note, styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

    # Footer
    story.append(Spacer(1, 0.2 * inch))
    footer = Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"],
    )
    story.append(footer)

    doc.build(story)
