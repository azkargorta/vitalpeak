# app/pdf_export.py — PDF VitalPeak (marca + entrenamiento completo)
from __future__ import annotations

import os
from collections import defaultdict
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Marca (alineada con app/ui_theme.py)
INK = colors.HexColor("#142830")
INK_SOFT = colors.HexColor("#2A4450")
ACCENT = colors.HexColor("#3AA899")
ACCENT_SOFT = colors.HexColor("#E6F6F3")
SURFACE = colors.HexColor("#F5F9F7")
MUTED = colors.HexColor("#6A7F88")
WHITE = colors.white
GRID = colors.HexColor("#D5E2DE")
ROW_ALT = colors.HexColor("#FAFCFB")

BRAND = "VitalPeak"
TAGLINE = "Entrena con claridad"


def _site_url() -> str:
    return (os.getenv("APP_BASE_URL") or os.getenv("VITALPEAK_URL") or "vitalpeak").rstrip("/")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "vp_brand",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=WHITE,
            leading=26,
            alignment=TA_LEFT,
        ),
        "tagline": ParagraphStyle(
            "vp_tagline",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#D6F0EC"),
            leading=12,
            alignment=TA_LEFT,
        ),
        "title": ParagraphStyle(
            "vp_title",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=INK,
            leading=20,
            spaceBefore=4,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "vp_sub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=MUTED,
            leading=12,
            spaceAfter=8,
        ),
        "day": ParagraphStyle(
            "vp_day",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=INK,
            leading=15,
        ),
        "day_meta": ParagraphStyle(
            "vp_day_meta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=10,
            spaceAfter=4,
        ),
        "cell": ParagraphStyle(
            "vp_cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=INK_SOFT,
            leading=11,
        ),
        "th": ParagraphStyle(
            "vp_th",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=WHITE,
            leading=10,
        ),
        "footer": ParagraphStyle(
            "vp_footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "footer_right": ParagraphStyle(
            "vp_footer_r",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
    }


def _header_table(styles: dict) -> Table:
    left = [
        Paragraph(BRAND, styles["brand"]),
        Paragraph(TAGLINE, styles["tagline"]),
    ]
    right = Paragraph(
        f'<font color="#D6F0EC">{_site_url()}</font>',
        ParagraphStyle("vp_url", parent=styles["tagline"], alignment=TA_RIGHT, fontSize=8),
    )
    t = Table([[left, right]], colWidths=[12 * cm, 5.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), INK),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    return t


def _accent_bar() -> Table:
    t = Table([[""]], colWidths=[17.5 * cm], rowHeights=[3 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
    return t


def _day_block(day: Dict[str, Any], styles: dict, day_index: int) -> KeepTogether:
    name = str(day.get("name") or day.get("nombre") or f"Día {day_index}")
    focus = str(day.get("focus") or day.get("foco") or "")
    items = day.get("items") or day.get("ejercicios") or []

    head_bits = [Paragraph(f"Día {day_index}  ·  {name}", styles["day"])]
    if focus:
        head_bits.append(Paragraph(focus, styles["day_meta"]))

    show_weight = any(
        (it.get("weight") not in (None, "", 0, 0.0) for it in items)
    )
    if show_weight:
        headers = ["Ejercicio", "Series", "Reps", "Peso"]
        widths = [10.2 * cm, 2.2 * cm, 2.2 * cm, 2.9 * cm]
    else:
        headers = ["Ejercicio", "Series", "Reps"]
        widths = [12.5 * cm, 2.5 * cm, 2.5 * cm]

    data: List[List[Any]] = [[Paragraph(h, styles["th"]) for h in headers]]
    for it in items:
        ex = str(it.get("exercise") or it.get("nombre") or "")
        sets = str(it.get("sets") if it.get("sets") is not None else it.get("series", ""))
        reps = str(it.get("reps", ""))
        row = [
            Paragraph(ex, styles["cell"]),
            Paragraph(sets, styles["cell"]),
            Paragraph(reps, styles["cell"]),
        ]
        if show_weight:
            w = it.get("weight", "")
            row.append(Paragraph("" if w in (None, 0, 0.0, "0", "0.0") else str(w), styles["cell"]))
        data.append(row)

    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 1, ACCENT),
            ]
        )
    )

    badge = Table(
        [[Paragraph(f"  {day_index}  ", ParagraphStyle(
            "badge", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE, alignment=TA_CENTER
        ))]],
        colWidths=[1.1 * cm],
        rowHeights=[0.7 * cm],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ]
        )
    )
    title_row = Table([[badge, head_bits]], colWidths=[1.3 * cm, 16.2 * cm])
    title_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return KeepTogether(
        [
            title_row,
            table,
            Spacer(1, 0.45 * cm),
        ]
    )


def _draw_footer(canvas, doc) -> None:
    canvas.saveState()
    page_w, _ = A4
    y = 1.1 * cm
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(1.5 * cm, y + 0.55 * cm, page_w - 1.5 * cm, y + 0.55 * cm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5 * cm, y, f"{BRAND}  ·  {_site_url()}")
    canvas.drawRightString(page_w - 1.5 * cm, y, f"Pág. {doc.page}")
    canvas.restoreState()


def program_to_pdf_bytes(
    title: str,
    days: Sequence[Dict[str, Any]],
    *,
    subtitle: str = "",
    meta_line: str = "",
) -> bytes:
    """Genera PDF de un entrenamiento completo (varios días/rutinas)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.8 * cm,
    )
    styles = _styles()
    story: List[Any] = [
        _header_table(styles),
        _accent_bar(),
        Spacer(1, 0.45 * cm),
        Paragraph(title, styles["title"]),
    ]
    sub = subtitle or meta_line
    if sub:
        story.append(Paragraph(sub, styles["subtitle"]))
    else:
        story.append(Spacer(1, 0.15 * cm))

    story.append(
        HRFlowable(width="100%", thickness=0.6, color=GRID, spaceBefore=2, spaceAfter=10)
    )

    n_days = len(days)
    story.append(
        Paragraph(
            f"{n_days} {'sesión' if n_days == 1 else 'sesiones'} · Plantilla VitalPeak",
            styles["subtitle"],
        )
    )

    for i, day in enumerate(days, start=1):
        story.append(_day_block(day, styles, i))

    doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return buffer.getvalue()


def routines_to_pdf_bytes(
    routines: Sequence[Dict[str, Any]],
    *,
    title: Optional[str] = None,
    subtitle: str = "",
) -> bytes:
    """PDF desde rutinas guardadas ({name, items})."""
    days = []
    for r in routines:
        day_name = str(r.get("name") or "Sesión")
        if " — " in day_name and title:
            day_name = day_name.split(" — ", 1)[-1]
        days.append({"name": day_name, "items": list(r.get("items") or [])})
    prog_title = title or (routines[0].get("name") if routines else "Entrenamiento")
    return program_to_pdf_bytes(str(prog_title), days, subtitle=subtitle)


def group_routine_programs(routines: Sequence[Dict[str, Any]]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """Agrupa rutinas 'Prefijo — Día' y planes (kind=program). Devuelve [(título, [rutinas]), ...]."""
    from app.routines import is_program, program_sessions

    out: List[Tuple[str, List[Dict[str, Any]]]] = []
    claimed: set[str] = set()

    for r in routines:
        if not is_program(r):
            continue
        sessions = program_sessions(r)
        as_routines = [{"name": s["name"], "items": s["items"]} for s in sessions]
        if len(as_routines) >= 2:
            out.append((str(r["name"]), as_routines))
            claimed.add(str(r["name"]))
            for s in sessions:
                claimed.add(s["name"])
        else:
            out.append((str(r["name"]), [r]))
            claimed.add(str(r["name"]))

    groups: dict[str, List[Dict[str, Any]]] = defaultdict(list)
    singles: List[Dict[str, Any]] = []
    for r in routines:
        name = str(r.get("name") or "")
        if name in claimed or is_program(r):
            continue
        if " — " in name:
            prefix = name.split(" — ", 1)[0].strip()
            groups[prefix].append(r)
        else:
            singles.append(r)

    for prefix, items in sorted(groups.items()):
        items_sorted = sorted(items, key=lambda x: str(x.get("name") or ""))
        if len(items_sorted) >= 2:
            out.append((prefix, items_sorted))
        else:
            singles.extend(items_sorted)

    for r in singles:
        out.append((str(r.get("name") or "Rutina"), [r]))
    return out


def plan_days_to_pdf_bytes(plan: Dict[str, Any]) -> bytes:
    """PDF desde editor de plantilla ({name, days:[{name, focus, items}]})."""
    from app.routine_templates import day_to_routine_items

    title = str(plan.get("name") or "Entrenamiento")
    normalized = []
    for d in plan.get("days") or []:
        normalized.append(
            {
                "name": d.get("name") or "Día",
                "focus": d.get("focus") or "",
                "items": day_to_routine_items(d),
            }
        )
    meta = []
    if plan.get("level"):
        meta.append(str(plan["level"]))
    if plan.get("goal"):
        meta.append(str(plan["goal"]))
    if plan.get("days_per_week"):
        meta.append(f"{plan['days_per_week']} días/sem")
    if plan.get("duration_min"):
        meta.append(f"~{plan['duration_min']} min")
    return program_to_pdf_bytes(title, normalized, subtitle=" · ".join(meta))


def rutina_a_pdf_bytes(rutina: Dict[str, Any]) -> bytes:
    """Compatibilidad con planes IA (meta / dias / ejercicios)."""
    meta = rutina.get("meta") or {}
    title = f"Plan de entrenamiento — {meta.get('objetivo', '')}".strip(" —")
    if title == "Plan de entrenamiento":
        title = "Plan de entrenamiento VitalPeak"
    subtitle = " · ".join(
        p
        for p in [
            f"Nivel: {meta['nivel']}" if meta.get("nivel") else "",
            f"{meta['dias']} días/sem" if meta.get("dias") else "",
            f"{meta['duracion_min']} min" if meta.get("duracion_min") else "",
        ]
        if p
    )
    days = []
    for dia in rutina.get("dias") or []:
        ejercicios = []
        for ej in dia.get("ejercicios") or []:
            ejercicios.append(
                {
                    "exercise": ej.get("nombre", ""),
                    "sets": ej.get("series", ""),
                    "reps": ej.get("reps", ""),
                    "weight": ej.get("intensidad") or "",
                }
            )
        days.append(
            {
                "name": dia.get("nombre", "Día"),
                "focus": dia.get("notas", ""),
                "items": ejercicios,
            }
        )
    return program_to_pdf_bytes(title, days, subtitle=subtitle)
