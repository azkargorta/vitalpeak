# app/pdf_export.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import cm
from io import BytesIO
from typing import Dict, Any, List

def _meta_block(meta: dict) -> List[Any]:
    styles = getSampleStyleSheet()
    s = []
    title = Paragraph(f"<b>Plan de entrenamiento — {meta.get('objetivo','')}</b>", styles['Title'])
    info = Paragraph(
        f"Nivel: {meta.get('nivel','')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Días/semana: {meta.get('dias','')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Duración objetivo: {meta.get('duracion_min','')} min",
        styles['Normal']
    )
    s += [title, Spacer(1, 0.2*cm), info, Spacer(1, 0.4*cm)]
    return s

def _day_table(dia: dict) -> List[Any]:
    styles = getSampleStyleSheet()
    elems = []
    h = Paragraph(f"<b>{dia.get('nombre','Día')}</b>", styles['Heading2'])
    elems.append(h)
    elems.append(Spacer(1, 0.15*cm))

    data = [["Ejercicio", "Series", "Reps", "Descanso", "Intensidad"]]
    for ej in dia.get('ejercicios', []):
        nombre = str(ej.get('nombre', ''))
        series = str(ej.get('series', ''))
        reps = str(ej.get('reps',''))
        descanso = str(ej.get('descanso',''))
        intensidad = str(ej.get('intensidad','')) if ej.get('intensidad') else ""
        data.append([nombre, series, reps, descanso, intensidad])

    col_widths = [7.5*cm, 2*cm, 2.5*cm, 2.5*cm, 3.5*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f2f6")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#111111")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#c8d1dc")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfcfe")]),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elems.append(t)

    notas = dia.get('notas', '')
    if notas:
        elems.append(Spacer(1, 0.1*cm))
        elems.append(Paragraph(f"<i>Notas:</i> {notas}", styles['Italic']))

    elems.append(Spacer(1, 0.4*cm))
    return elems

def _progresion_block(progresion: dict) -> List[Any]:
    styles = getSampleStyleSheet()
    h = Paragraph("<b>Progresión</b>", styles['Heading3'])
    txt = Paragraph(
        f"Principales: {progresion.get('principales','')}<br/>"
        f"Accesorios: {progresion.get('accesorios','')}<br/>"
        f"Deload (semana): {progresion.get('deload_semana','')}",
        styles['Normal']
    )
    return [h, Spacer(1, 0.1*cm), txt]

def rutina_a_pdf_bytes(rutina: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=1.2*cm, leftMargin=1.2*cm, topMargin=1.2*cm, bottomMargin=1.2*cm
    )
    story: List[Any] = []

    meta = rutina.get('meta', {})
    story += _meta_block(meta)

    dias = rutina.get('dias', [])
    for i, dia in enumerate(dias):
        story += _day_table(dia)
        if (i+1) % 2 == 0 and (i+1) < len(dias):
            story.append(PageBreak())

    prog = rutina.get('progresion', {})
    if prog:
        story.append(PageBreak())
        story += _progresion_block(prog)

    doc.build(story)
    return buffer.getvalue()
