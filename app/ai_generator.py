from __future__ import annotations
__all__ = ["call_gpt", "build_prompt", "build_system"]
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # fallback to legacy openai package


import os
import re
import json
from typing import Any, Dict, List, Optional
from openai import OpenAI

JSON_MD_RE = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)

def _safe_json_search(regex, text):
    try:
        return regex.search(text) if regex else None
    except Exception:
        return None

        C["days_per_week"] = int(m.group(1))

    # Duración por sesión
    m = _re.search(r"(?:sesiones?|duraci[oó]n).{0,6}?(\d+)\s*min", txt)
    if m:
        C["session_target_minutes"] = int(m.group(1))
    m = _re.search(r"(?:no\s+m[aá]s\s+de|m[aá]ximo)\s*(\d+)\s*min", txt)
    if m:
        C["session_max_minutes"] = int(m.group(1))
    m = _re.search(r"(?:al\s+menos|min[ií]mo)\s*(\d+)\s*min", txt)
    if m and "session_min_minutes" not in C:
        C["session_min_minutes"] = int(m.group(1))

    # Descansos
    m = _re.search(r"descansos?\s+de\s*(\d+)\s*-\s*(\d+)\s*s", txt)
    if m:
        C["rest_seconds_range"] = (int(m.group(1)), int(m.group(2)))
    m = _re.search(r"descansos?\s+de\s*(\d+)\s*s", txt)
    if m and "rest_seconds_range" not in C:
        C["rest_seconds_range"] = (int(m.group(1)), int(m.group(1)))

    # Tempo
    m = _re.search(r"tempo\s+(\d[\-\d]*)", txt)
    if m:
        C["default_tempo"] = m.group(1)

    # RIR/RPE
    m = _re.search(r"rir\s*(\d)\s*-\s*(\d)", txt)
    if m:
        C["rir_range"] = (int(m.group(1)), int(m.group(2)))
    m = _re.search(r"rpe\s*(\d)\s*-\s*(\d)", txt)
    if m:
        C["rpe_range"] = (int(m.group(1)), int(m.group(2)))

    # Progresión
    if "progresi" in txt:
        if _re.search(r"lineal", txt):
            C["progression"] = "lineal"
        elif _re.search(r"doble", txt):
            C["progression"] = "doble"
        elif _re.search(r"ondulante|undulating|dup", txt):
            C["progression"] = "ondulante"
        elif _re.search(r"5\s*/\s*3\s*/\s*1", txt):
            C["progression"] = "531"

    # Splits
    if _re.search(r"push\s*[-/]\s*pull\s*[-/]\s*legs|ppl", txt):
        C["preferred_split"] = "PPL"
    if _re.search(r"upper\s*[-/]\s*lower|torso\s*[-/]\s*pierna", txt):
        C["preferred_split"] = "UL"
    if _re.search(r"full\s*body|cuerpo\s*entero", txt):
        C["preferred_split"] = "FB"
    if _re.search(r"pecho\s*[-/]\s*tr[íi]ceps", txt) or _re.search(r"espalda\s*[-/]\s*b[ií]ceps", txt) or _re.search(r"pierna\s*[-/]\s*gl[úu]teo", txt):
        C["preferred_split"] = "PT-EB-PG"

    # Calentamiento / movilidad / core
    if _re.search(r"incluir\s+calentamiento|con\s+calentamiento", txt):
        C["include_warmup"] = True
    m = _re.search(r"calentamiento\s*(\d+)\s*min", txt)
    if m:
        C["warmup_minutes"] = int(m.group(1))
    if _re.search(r"(incluir|con)\s+movilidad|movilidad\s+articular", txt):
        C["include_mobility"] = True
    if _re.search(r"(incluir|con)\s+core|abdominales", txt):
        C["include_core"] = True
    m = _re.search(r"core\s*(\d+)\s*d[ií]as", txt)
    if m:
        C["core_days_min"] = int(m.group(1))

    # Cardio con tipo
    if _re.search(r"hiit", txt):
        C["cardio_type"] = "HIIT"
    if _re.search(r"liss|suave|zona\s*2", txt):
        C["cardio_type"] = "LISS"

    # Preferencias de equipo
    if _re.search(r"solo\s+mancuernas?", txt):
        C["equipment_only_dumbbells"] = True
    if _re.search(r"solo\s+barra", txt):
        C["equipment_only_barbell"] = True
    if _re.search(r"(en\s+casa|domicilio|home)\s+(sin\s+)?m[aá]quinas?", txt):
        C["home_gym_minimal"] = True

    # Evitar ejercicios concretos (lista libre tras "no"/"evitar")
    avoid = []
    for m in _re.finditer(r"(?:no|evitar)\s+([a-záéíóúüñ\s]+?)(?:,|\.|;|$)", txt):
        ex = m.group(1).strip()
        if ex and len(ex) < 40:
            avoid.append(ex)
    if avoid:
        C["avoid_exercises"] = list(set(avoid))

    # Días nominales
    days_map = {"lunes":"mon","martes":"tue","miercoles":"wed","miércoles":"wed","jueves":"thu","viernes":"fri","sabado":"sat","sábado":"sat","domingo":"sun"}
    chosen = []
    for k in days_map.keys():
        if _re.search(rf"\b{k}\b", txt):
            chosen.append(days_map[k])
    if chosen:
        C["weekdays"] = sorted(list(set(chosen)))

    # Volumen por grupo (series/semana)
    grupos = {
        "pecho":["pecho","chest","pectorales","pectoral"],
        "espalda":["espalda","back","dorsal","lats"],
        "hombro":["hombro","hombros","deltoide","deltoides","shoulder"],
        "bíceps":["bíceps","biceps","bicep"],
        "tríceps":["tríceps","triceps","tricep"],
        "pierna":["pierna","piernas","legs","cuádriceps","cuadriceps","isquio","femoral","glúteo","gluteo"],
        "glúteo":["glúteo","gluteo","glutes"],
        "core":["core","abdominal","abdominales","abs"],
        "gemelo":["gemelo","gemelos","pantorrilla","pantorrillas","calf"]
    }
    vol = {}
    for g, aliases in grupos.items():
        for alias in aliases:
            m = _re.search(rf"\b{alias}\b\s*(\d+)\s*[-–]\s*(\d+)\s*series", txt)
            if m:
                vol[g] = (int(m.group(1)), int(m.group(2)))
            m = _re.search(rf"\b{alias}\b.*?(?:al\s+menos|min[ií]mo|como\s+min[ií]mo)\s*(\d+)\s*series", txt)
            if m:
                lo = int(m.group(1)); hi = vol.get(g, (None,None))[1]
                vol[g] = (lo, hi)
            m = _re.search(rf"\b{alias}\b.*?(?:m[aá]ximo|no\s+m[aá]s\s+de)\s*(\d+)\s*series", txt)
            if m:
                hi = int(m.group(1)); lo = vol.get(g, (None,None))[0]
                vol[g] = (lo, hi)
    if vol:
        C["volumen_series"] = vol

    # Orden de ejercicios
    if _re.search(r"bilaterales?\s+primero", txt):
        C.setdefault("order_rules", {})["bilateral_first"] = True
    if _re.search(r"(b[aá]sicos|compuestos)\s+antes\s+que\s+(accesorios|aislados?)", txt):
        C.setdefault("order_rules", {})["basics_first"] = True

    # Series/Reps globales por defecto
    m = _re.search(r"(\d+)\s*[-–]\s*(\d+)\s*series.*?(\d+)\s*[-–]\s*(\d+)\s*(rep|reps|repeticiones)", txt)
    if m:
        C["default_series_reps"] = {"series": (int(m.group(1)), int(m.group(2))), "reps": (int(m.group(3)), int(m.group(4)))}
    else:
        m = _re.search(r"(?:fuerza|hipertrofia|resistencia)?.*?(\d+)\s*[-–]\s*(\d+)\s*(rep|reps|repeticiones)", txt)
        if m:
            C["default_series_reps"] = {"reps": (int(m.group(1)), int(m.group(2)))}
        m = _re.search(r"(?:series)\s*(\d+)\s*[-–]\s*(\d+)", txt)
        if m:
            dsr = C.get("default_series_reps", {})
            dsr["series"] = (int(m.group(1)), int(m.group(2)))
            C["default_series_reps"] = dsr

    return C


def _extract_json(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Respuesta vacía")
    m = _safe_json_search(JSON_MD_RE, text)
    if m:
        return m.group(1)
    m = _safe_json_search(JSON_BLOCK_RE, text)
    if m:
        return m.group(0)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    raise ValueError("No se encontró bloque JSON")
def _ensure_descanso_for_ej(ej: Dict[str, Any]) -> Dict[str, Any]:
    # Normaliza un ejercicio garantizando 'descanso'
    if not isinstance(ej, dict):
        return {"nombre": str(ej), "series": 3, "reps": "10", "descanso": "60-90s"}
    nombre = ej.get("nombre") or ej.get("ejercicio") or ej.get("name") or "Ejercicio"
    try:
        series = int(ej.get("series", 3))
    except Exception:
        series = 3
    reps = str(ej.get("reps") or ej.get("repeticiones") or ej.get("rep") or "10")
    out = {"nombre": nombre, "series": series, "reps": reps}
    # Descanso por defecto si no viene
    def _infer_rest(reps_str: str) -> str:
        import re as _re
        s = reps_str.strip()
        m = _re.match(r"^(\d{1,2})\s*[–-]\s*(\d{1,2})$", s)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            avg = (a + b) / 2
        else:
            try:
                avg = float(s)
            except Exception:
                avg = 10
        if avg <= 6:
            return "120-180s"
        if avg <= 10:
            return "60-90s"
        return "45-75s"
    if "descanso" in ej and str(ej.get("descanso")).strip():
        out["descanso"] = str(ej.get("descanso"))
    else:
        out["descanso"] = _infer_rest(reps)
    # Extras si existen
    for k in ("rir","rpe","notas","tempo","intensidad"):
        if k in ej:
            out[k] = ej[k]
    return out
def _coerce_to_schema(raw: Dict[str, Any], datos: Dict[str, Any]) -> Dict[str, Any]:
    """Intenta mapear salidas variadas de la IA al esquema esperado: {'meta','dias','progresion'}."""
    data = dict(raw) if isinstance(raw, dict) else {}

    # Preferencia deload: si el usuario define semanas de ciclo, el deload por defecto se coloca al final del ciclo.
    try:
        semanas_ciclo = int(datos.get("semanas_ciclo") or 0)
        if semanas_ciclo < 1:
            semanas_ciclo = 0
    except Exception:
        semanas_ciclo = 0

    # --- META ---
    if "meta" not in data or not isinstance(data.get("meta"), dict):
        data["meta"] = {
            "nivel": datos.get("nivel", "intermedio"),
            "dias": int(datos.get("dias", 4) or 4),
            "duracion_min": int(datos.get("duracion", 60) or 60),
            "objetivo": datos.get("objetivo", "mixto"),
        }

    # --- PROGRESION ---
    pref_in = data.get("progresion")
    if isinstance(pref_in, dict) and {"principales","accesorios","deload_semana"} <= set(pref_in.keys()):
        pass
    else:
        pref = str(pref_in or datos.get("progresion_preferida", "lineal")).lower()
        if "doble" in pref:
            data["progresion"] = {
                "principales": "doble progresión en carga o repeticiones",
                "accesorios": "añadir 1-2 repeticiones por semana hasta rango tope",
                "deload_semana": (semanas_ciclo or 6)
            }
        elif "lineal" in pref:
            data["progresion"] = {
                "principales": "aumenta carga 2.5–5% cuando completes el rango de reps",
                "accesorios": "mantén técnica y suma reps gradualmente",
                "deload_semana": (semanas_ciclo or 6)
            }
        else:
            data["progresion"] = {
                "principales": "progresión simple: subir reps o carga cada semana si es posible",
                "accesorios": "reps adicionales o pausas más cortas",
                "deload_semana": (semanas_ciclo or 6)
            }

    
    # Asegurar que progresion sea dict válido
    pref_in = data.get("progresion")
    if not isinstance(pref_in, dict):
        pref = str(pref_in or datos.get("progresion_preferida", "lineal")).lower()
        if "doble" in pref:
            data["progresion"] = {
                "principales": "doble progresión en carga o repeticiones",
                "accesorios": "añadir 1-2 repeticiones por semana hasta rango tope",
                "deload_semana": (semanas_ciclo or 6)
            }
        elif "lineal" in pref:
            data["progresion"] = {
                "principales": "aumenta carga 2.5–5% cuando completes el rango de reps",
                "accesorios": "mantén técnica y suma reps gradualmente",
                "deload_semana": (semanas_ciclo or 6)
            }
        else:
            data["progresion"] = {
                "principales": "progresión simple: subir reps o carga cada semana si es posible",
                "accesorios": "reps adicionales o pausas más cortas",
                "deload_semana": (semanas_ciclo or 6)
            }


    # --- DIAS ---
    def _norm_ej(e):
        if not isinstance(e, dict):
            return {"nombre": str(e), "series": 3, "reps": "10"}
        nombre = e.get("nombre") or e.get("ejercicio") or e.get("name") or "Ejercicio"
        try:
            series = int(e.get("series", 3))
        except Exception:
            series = 3
        reps_val = e.get("reps") or e.get("repeticiones") or e.get("rep") or "10"
        reps = str(reps_val)
        out = {"nombre": nombre, "series": series, "reps": reps}
        # Descanso por defecto si no viene
        def _infer_rest(reps_str: str) -> str:
            import re as _re
            s = reps_str.strip()
            m = _re.match(r"^(\d{1,2})\s*[–-]\s*(\d{1,2})$", s)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                avg = (a + b) / 2
            else:
                try:
                    avg = float(s)
                except Exception:
                    avg = 10
            if avg <= 6:
                return "120-180s"
            if avg <= 10:
                return "60-90s"
            return "45-75s"
        if "descanso" in e and str(e.get("descanso")).strip():
            out["descanso"] = str(e.get("descanso"))
        else:
            out["descanso"] = _infer_rest(reps)
        # Campos opcionales si existen
        for k in ("rir","rpe","notas","tempo"):
            if k in e:
                out[k] = e[k]
        return out

    if "dias" not in data or not isinstance(data.get("dias"), list) or not data["dias"]:
        dias_list = []
        # Posibles estructuras alternativas
        if "rutina_semanal" in data and isinstance(data["rutina_semanal"], dict):
            for dia_nombre, dia_val in data["rutina_semanal"].items():
                ejercicios_src = dia_val.get("ejercicios") if isinstance(dia_val, dict) else dia_val
                ejercicios = [_norm_ej(e) for e in (ejercicios_src or [])]
                dias_list.append({"nombre": str(dia_nombre), "ejercicios": ejercicios})
        elif "semanal" in data and isinstance(data["semanal"], dict):
            for dia_nombre, ejercicios_src in data["semanal"].items():
                ejercicios = [_norm_ej(e) for e in (ejercicios_src or [])]
                dias_list.append({"nombre": str(dia_nombre), "ejercicios": ejercicios})
        elif "plan" in data and isinstance(data["plan"], dict):
            for dia_nombre, ejercicios_src in data["plan"].items():
                ejercicios = [_norm_ej(e) for e in (ejercicios_src or [])]
                dias_list.append({"nombre": str(dia_nombre), "ejercicios": ejercicios})
        else:
            # Último recurso: si el raw ya tiene aspecto de lista de días
            if isinstance(raw, dict) and any(k.lower().startswith(("lunes","martes","miércoles","miercoles","jueves","viernes","sábado","sabado","domingo")) for k in raw.keys()):
                for dia_nombre, ejercicios_src in raw.items():
                    ejercicios = [_norm_ej(e) for e in (ejercicios_src or [])]
                    dias_list.append({"nombre": str(dia_nombre), "ejercicios": ejercicios})

        data["dias"] = dias_list

    # Normalización SIEMPRE sobre dias si existen
    if isinstance(data.get("dias"), list):
        fixed_dias = []
        for dia in data["dias"]:
            nombre_dia = (dia.get("nombre") if isinstance(dia, dict) else str(dia)) or "Día"
            ejercicios_src = []
            if isinstance(dia, dict):
                ejercicios_src = dia.get("ejercicios") or []
            elif isinstance(dia, list):
                ejercicios_src = dia
            ejercicios = [_ensure_descanso_for_ej(ej) for ej in (ejercicios_src or [])]
            fixed_dias.append({"nombre": nombre_dia, "ejercicios": ejercicios, "notas": dia.get("notas","") if isinstance(dia, dict) else ""})
        data["dias"] = fixed_dias

    return data
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

RULES_TEXT = (
    "- Estructura por día: 6–7 ejercicios (1 principal fuerza, 1 secundario, 3–4 accesorios, 1 core/finisher).\n"
    "- Principales: 4–6 reps, descanso 2–3m, RPE 7–8 o 75–80%.\n"
    "- Secundarios: 6–10 reps, descanso ~2m.\n"
    "- Accesorios: 10–15 reps, descanso 60–90s.\n"
    "- Upper: balance empuje (press) y tirón (remo/dominada).\n"
    "- Lower A: cuádriceps dominante; Lower B: bisagra/isquios; sin ejercicios de tríceps.\n"
    "- No repitas el mismo patrón pesado dos días seguidos.\n"
    "- Duración objetivo: {dur} minutos. Ajusta descansos/volumen para cumplir.\n"
)



def validar_negocio(plan: Dict[str, Any]) -> List[str]:
    """Validación de negocio con coerción tolerante.
    Acepta: dict esperado, lista de días, o cadena JSON que contenga el plan.
    """
    errs: List[str] = []

    # --- Coerciones suaves ---
    if isinstance(plan, str):
        try:
            plan = _try_parse_json(plan)
        except Exception:
            try:
                plan = json.loads(plan)
            except Exception:
                return ["El plan debe ser un objeto JSON (dict)."]

    if isinstance(plan, dict) and not plan.get('dias') and any(k in plan for k in ('plan','data','payload','resultado')):
        for k in ('plan','data','payload','resultado'):
            if isinstance(plan.get(k), dict):
                plan = plan[k]
                break

    if isinstance(plan, list):
        plan = {"meta": {}, "dias": plan}

    if not isinstance(plan, dict):
        return ["El plan debe ser un objeto JSON (dict)."]

    meta = plan.get("meta", {})
    if not isinstance(meta, dict):
        errs.append("Falta 'meta' como objeto.")
        meta = {}
    dur = meta.get("duracion_min") or meta.get("duracion") or 60
    try:
        dur = int(dur)
    except Exception:
        errs.append("'meta.duracion_min' debe ser un número en minutos.")

    dias = plan.get("dias") or plan.get("dias_semana") or plan.get("workout") or plan.get("days")
    if not isinstance(dias, list) or len(dias) == 0:
        errs.append("'dias' debe ser una lista con al menos 1 día.")
        return errs

    for i, d in enumerate(dias, start=1):
        if not isinstance(d, dict):
            errs.append(f"Día {i}: el elemento debe ser un objeto.")
            continue
        ejercicios = d.get("ejercicios") or d.get("workout") or d.get("exercises") or []
        if not isinstance(ejercicios, list) or len(ejercicios) == 0:
            errs.append(f"Día {i}: lista de 'ejercicios' vacía.")
            continue

        seen_names = set()
        for j, ej in enumerate(ejercicios, start=1):
            if not isinstance(ej, dict):
                errs.append(f"Día {i} ej #{j}: debe ser un objeto.")
                continue
            nombre = ej.get("nombre") or ej.get("ejercicio") or ej.get("name")
            if not nombre or not str(nombre).strip():
                errs.append(f"Día {i} ej #{j}: falta 'nombre'.")
            else:
                nrm = str(nombre).strip().lower()
                if nrm in seen_names:
                    errs.append(f"Día {i}: ejercicio repetido '{nombre}'.")
                seen_names.add(nrm)

            if "series" in ej:
                try:
                    s = int(ej.get("series"))
                    if s <= 0 or s > 10:
                        errs.append(f"Día {i} '{nombre}': 'series' fuera de rango (1–10)." )
                except Exception:
                    errs.append(f"Día {i} '{nombre}': 'series' debe ser entero.")

            if "reps" in ej or "repeticiones" in ej:
                reps_val = str(ej.get("reps") or ej.get("repeticiones"))
                if not reps_val.strip():
                    errs.append(f"Día {i} '{nombre}': 'reps' vacío.")

            if "descanso" in ej and not str(ej.get("descanso")).strip():
                errs.append(f"Día {i} '{nombre}': 'descanso' está vacío.")

        if len(ejercicios) < 3:
            errs.append(f"Día {i}: muy pocos ejercicios (<3)." )
        if len(ejercicios) > 12:
            errs.append(f"Día {i}: demasiados ejercicios (>12)." )

    return errs
def build_system() -> str:
    return "Eres un entrenador personal experto. Devuelve exclusivamente JSON válido, sin texto adicional."





def analyze_user_data(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Analiza y normaliza los datos del usuario.

    Devuelve un dict con:
    - valores normalizados para el esquema
    - restricciones explícitas (para que el modelo las cumpla)
    - reglas específicas por objetivo (hipertrofia vs fuerza)
    """
    objetivo_raw = str(datos.get("objetivo") or "").strip().lower()
    nivel_raw = str(datos.get("nivel") or "intermedio").strip().lower()

    # --- Objetivo -> schema ---
    if "hiper" in objetivo_raw:
        objetivo = "hipertrofia"
    elif "fuer" in objetivo_raw:
        objetivo = "fuerza"
    elif any(k in objetivo_raw for k in ["resis", "cardio"]):
        objetivo = "resistencia"
    elif any(k in objetivo_raw for k in ["grasa", "perdida", "pérdida", "defini"]):
        objetivo = "resistencia"
    elif any(k in objetivo_raw for k in ["salud", "rendim"]):
        objetivo = "mixto"
    else:
        objetivo = objetivo_raw if objetivo_raw in ("fuerza","hipertrofia","resistencia","mixto") else "mixto"

    nivel = nivel_raw if nivel_raw in ("principiante","intermedio","avanzado") else "intermedio"

    # --- Días/semana ---
    dias_raw = datos.get("dias")
    if isinstance(dias_raw, (list, tuple)):
        dias = len(dias_raw)
    else:
        try:
            dias = int(dias_raw or 4)
        except Exception:
            dias = 4
    dias = max(1, min(6, dias))

    # --- Duración ---
    try:
        duracion = int(datos.get("duracion") or datos.get("duracion_min") or 60)
    except Exception:
        duracion = 60
    duracion = max(30, min(120, duracion))


    # --- Disponibilidad ---
    disp = datos.get("disponibilidad") or []
    if isinstance(disp, str):
        disp = [d.strip() for d in disp.split(",") if d.strip()]
    disp = list(disp) if isinstance(disp, (list, tuple)) else []

    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    label_mode = False

    if disp:
        cleaned = []
        for d in disp:
            d0 = str(d).strip()
            if not d0:
                continue
            low = d0.lower()
            if low in ("miercoles", "miércoles"):
                d0 = "Miércoles"
            elif low in ("sabado", "sábado"):
                d0 = "Sábado"
            else:
                d0 = d0[0].upper() + d0[1:] if len(d0) > 1 else d0.upper()
            cleaned.append(d0)

        # Si hay etiquetas que NO son días de la semana (p.ej. "Sesión 1"), las tratamos como etiquetas de sesión.
        if any(x not in dias_semana for x in cleaned):
            label_mode = True
            disp_norm = []
            for x in cleaned:
                if x not in disp_norm:
                    disp_norm.append(x)
            disp = disp_norm
        else:
            disp_norm = []
            for x in cleaned:
                if x in dias_semana and x not in disp_norm:
                    disp_norm.append(x)
            disp = disp_norm

    # Ajuste a número de días/sesiones
    if len(disp) != dias:
        if disp:
            disp = disp[:dias]
            if not label_mode:
                for d in dias_semana:
                    if len(disp) >= dias:
                        break
                    if d not in disp:
                        disp.append(d)
            else:
                while len(disp) < dias:
                    disp.append(f"Sesión {len(disp)+1}")
        else:
            defaults = ["Lunes","Martes","Jueves","Viernes","Miércoles","Sábado"]
            disp = defaults[:dias]

    # --- Material ---
    material = datos.get("material") or datos.get("equipo") or []
    if isinstance(material, str):
        material = [m.strip() for m in material.split(",") if m.strip()]
    material = [str(m).strip().lower() for m in material] if isinstance(material, (list, tuple)) else []
    full_gym = ("todo" in material) or any("gimnasio completo" in m for m in material)

    # Texto libre (para restricciones)
    ia_detalles = (datos.get("ia_detalles") or "").strip()
    comentarios = (datos.get("comentarios") or "").strip()
    txt = (ia_detalles + " " + comentarios).lower()

    # Restricciones explícitas por texto
    no_machines = bool(re.search(r"(?:no\s+máquinas|no\s+maquinas|solo\s+peso\s+libre)", txt))
    no_cables = bool(re.search(r"(?:no\s+poleas|sin\s+poleas|sin\s+cables|no\s+cables)", txt))
    no_smith = bool(re.search(r"(?:no\s+smith|sin\s+smith)", txt))
    no_bar = bool(re.search(r"(?:no\s+barra|sin\s+barra)", txt))
    no_db = bool(re.search(r"(?:no\s+mancuernas|sin\s+mancuernas)", txt))

    # --- Split preferido (normalización) ---
    split_pref = str(datos.get("split_pref") or "").strip()
    split_low = split_pref.lower()
    split_template: List[str] | None = None
    if "ppl" in split_low:
        # Para 4 días: PPL + 1 extra de tren superior (Push B por defecto)
        if dias == 4:
            split_template = ["Push", "Pull", "Legs", "Upper"]
        elif dias == 3:
            split_template = ["Push", "Pull", "Legs"]
        elif dias == 6:
            split_template = ["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B"]

    # Evitar
    evitar = datos.get("evitar") or []
    if isinstance(evitar, str):
        evitar = [s.strip() for s in evitar.split(",") if s.strip()]
    evitar = [str(s).strip() for s in evitar] if isinstance(evitar, (list, tuple)) else []

    limitaciones = (datos.get("limitaciones") or datos.get("lesiones") or "").strip()

    # Intensidad
    try:
        rir_obj = int(datos.get("rir_obj") if datos.get("rir_obj") is not None else 2)
    except Exception:
        rir_obj = 2
    rir_obj = max(0, min(4, rir_obj))

    # --- Reglas por objetivo ---
    if objetivo == "hipertrofia":
        reglas_obj = """REGLAS ESPECÍFICAS (HIPERTROFIA):
- Prioriza rangos 6-10 / 8-12 / 10-15 (aislados 12-20).
- Limita el rango 3-6 a como máximo 1 ejercicio por sesión (si lo usas, que sea el principal).
- Descansos orientativos: compuestos 90-150s, accesorios 45-90s.
- RIR objetivo: usa ~{rir} como referencia (más cerca de 0-2 en aislados; 1-3 en compuestos).
- Incluye semanalmente: tirón vertical, tirón horizontal, empuje horizontal, empuje vertical, bisagra, sentadilla/prensa, gemelos, core.
- Incluye al menos 1 trabajo de bíceps, tríceps y deltoide lateral a la semana.
- Ajusta el volumen para que la sesión quepa en {dur} min.
""".format(rir=rir_obj, dur=duracion)
    elif objetivo == "fuerza":
        reglas_obj = """REGLAS ESPECÍFICAS (FUERZA):
- Prioriza principales 3-6 reps con descansos 2-4 min.
- Secundarios 5-8 reps; accesorios 8-12.
- Menos ejercicios por día si hace falta para cumplir {dur} min.
- RIR objetivo: ~{rir} (principales típicamente 1-3).
""".format(rir=rir_obj, dur=duracion)
    else:
        reglas_obj = """REGLAS ESPECÍFICAS (GENERAL):
- Combina compuestos y accesorios con rangos 6-12 y algún 12-15.
- Ajusta volumen/descansos para cumplir {dur} min.
""".format(dur=duracion)

    # --- Restricciones (checklist) ---
    restricciones: List[str] = []
    restricciones.append(f"- NO INVENTAR: usa exactamente estos días: {disp} (y solo {dias} días).")
    restricciones.append(f"- Duración por sesión: {duracion} min (ajusta descansos/series para cumplir).")
    restricciones.append(f"- Nivel: {nivel}.")
    restricciones.append(f"- Objetivo: {objetivo}.")
    restricciones.append(f"- Material disponible: {material if material else ['(no especificado)']}" + (" (gimnasio completo)" if full_gym else ""))
    if limitaciones:
        restricciones.append(f"- Lesiones/limitaciones: {limitaciones} (respétalo estrictamente).")
    if evitar:
        restricciones.append(f"- Evitar: {evitar} (no los incluyas).")
    if no_machines:
        restricciones.append("- Restricción: SIN máquinas.")
    if no_cables:
        restricciones.append("- Restricción: SIN poleas/cables.")
    if no_smith:
        restricciones.append("- Restricción: SIN Smith.")
    if no_bar:
        restricciones.append("- Restricción: SIN barra.")
    if no_db:
        restricciones.append("- Restricción: SIN mancuernas.")

    if split_pref:
        restricciones.append(f"- Split preferido: {split_pref}. Respétalo y hazlo explícito en el nombre de cada día.")
        if split_template:
            restricciones.append(f"- Orden del split (obligatorio): {split_template}.")
    if datos.get("enfasis_accesorios"):
        restricciones.append(f"- Prioridades musculares: {datos.get('enfasis_accesorios')}. Aumenta volumen ahí sin romper el tiempo.")
    if datos.get("basicos_objetivo"):
        restricciones.append(f"- Básicos a mejorar (si objetivo fuerza): {datos.get('basicos_objetivo')}.")

    return {
        "objetivo": objetivo,
        "nivel": nivel,
        "dias": dias,
        "duracion": duracion,
        "disponibilidad": disp,
        "material": material,
        "full_gym": full_gym,
        "limitaciones": limitaciones,
        "evitar": evitar,
        "rir_obj": rir_obj,
        "split_pref": split_pref,
        "split_template": split_template,
        "reglas_objetivo": reglas_obj,
        "restricciones": restricciones,
    }





def build_prompt(datos: Dict[str, Any]) -> str:
    """Construye el prompt para la IA.

    Importante: aquí solo ensamblamos texto. La lógica/derivaciones están en analyze_user_data().
    """
    A = analyze_user_data(datos)
    nl = chr(10)

    ia_detalles = (datos.get("ia_detalles") or "").strip()
    notas = (datos.get("comentarios") or "").strip()

    reglas_generales = (
        "REGLAS GENERALES (siempre):" + nl +
        "- Devuelve EXCLUSIVAMENTE JSON válido (sin markdown, sin explicación)." + nl +
        "- Cada día debe tener 5-8 ejercicios (ideal 6-7)." + nl +
        "- Estructura por día: 1 principal (3-6 o 4-6), 1 secundario (6-10), 3-4 accesorios (10-15/12-20), 1 core o finisher." + nl +
        "- Incluye 'descanso' en TODOS los ejercicios." + nl +
        "- El último ejercicio de cada día DEBE ser el core/finisher y su nombre debe empezar por 'Core:' o 'Finisher:' (para verificación)." + nl +
        "- Upper (si aparece): balancea empuje y tirón." + nl +
        "- Lower (si aparece): evita meter tríceps como parte principal." + nl +
        "- Evita duplicar exactamente el mismo ejercicio en la misma semana." + nl +
        "- Ajusta volumen/descansos para que la sesión quepa en el tiempo por sesión." + nl
    )

    split_rules = ""
    if A.get("split_pref"):
        split_rules += "REGLAS DE SPLIT (OBLIGATORIO):" + nl
        if A.get("split_template"):
            # Se exige el orden, y que se refleje en el nombre del día/sesión para que la app lo valide.
            split_rules += f"- Usa este orden exacto de sesiones: {A['split_template']}." + nl
            dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
            if all(d in dias_semana for d in A.get("disponibilidad", [])):
                split_rules += "- El campo 'nombre' de cada día debe ser: '<DíaSemana> - <Sesión>' (ej: 'Lunes - Push')." + nl
            else:
                split_rules += "- El campo 'nombre' de cada sesión debe ser: '<Etiqueta> - <Sesión>' (ej: 'Sesión 1 - Push A')." + nl
        else:
            split_rules += f"- Split preferido: {A['split_pref']}. Respétalo." + nl
        split_rules += nl

    restricciones_txt = nl.join(A["restricciones"])

    detalles_usuario = ""
    if ia_detalles:
        detalles_usuario += (
            nl + "DETALLES_USUARIO (usar tal cual):" + nl +
            "<<<" + nl + ia_detalles + nl + ">>>" + nl
        )
    if notas:
        detalles_usuario += (
            nl + "NOTAS_ADICIONALES (usar tal cual):" + nl +
            "<<<" + nl + notas + nl + ">>>" + nl
        )

    # Importante: el schema usa 'duracion_min' y 'objetivo' en {fuerza|hipertrofia|resistencia|mixto}
    schema_hint = '''
ESQUEMA JSON (obligatorio):
{
  "meta": {"nivel": "principiante|intermedio|avanzado", "dias": N, "duracion_min": N, "objetivo": "fuerza|hipertrofia|resistencia|mixto"},
  "dias": [
    {"nombre": "Lunes", "ejercicios": [
      {"nombre": "...", "series": 3, "reps": "8-12", "intensidad": "RIR 1-2", "descanso": "60-90s"}
    ], "notas": "..."}
  ],
  "progresion": {"principales": "...", "accesorios": "...", "deload_semana": N}
}
'''

    prompt = (
        "CONTEXTO:" + nl +
        "Eres un entrenador personal experto. Diseña un plan que cumpla las restricciones del usuario y el objetivo." + nl + nl +
        "DATOS NORMALIZADOS:" + nl +
        f"- Objetivo: {A['objetivo']}" + nl +
        f"- Nivel: {A['nivel']}" + nl +
        f"- Días/semana: {A['dias']}" + nl +
        f"- Duración: {A['duracion']} min" + nl +
        f"- Días exactos: {A['disponibilidad']}" + nl + nl +
        reglas_generales + nl +
        split_rules +
        "REGLAS POR OBJETIVO:" + nl + A['reglas_objetivo'] + nl +
        "RESTRICCIONES Y CHECKLIST (OBLIGATORIO):" + nl + restricciones_txt + nl +
        detalles_usuario + nl +
        schema_hint + nl +
        "SALIDA: devuelve SOLO JSON válido." + nl
    )

    return prompt
def _client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _chat(client: OpenAI, prompt: str, *, temperature: float = 0.1) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        messages=[
            {"role":"system","content": build_system()},
            {"role":"user","content": prompt}
        ]
    )
    return resp.choices[0].message.content

def _try_parse_json(text: str) -> Dict[str, Any]:
    """Intenta parsear JSON tolerante a respuestas con texto adicional o fences."""
    # Respuesta vacía -> error claro
    if not text or not str(text).strip():
        raise ValueError("Respuesta de OpenAI vacía")
    try:
        # Intento directo
        return json.loads(text)
    except Exception:
        # Intento robusto: extraer bloque JSON o primer objeto balanceado
        return _extract_json(text)


# === Reglas adicionales derivadas de 'comentarios' del usuario ===
from typing import Any, Dict

MUSCLES_SYNONYMS = {
    "bíceps": ["bíceps","biceps","curl","martillo"],
    "tríceps": ["tríceps","triceps","fondos","jalón tríceps","jalon triceps","extensión tríceps","extension triceps"],
    "pecho": ["pecho","press banca","aperturas","inclinado","cruce","press"],
    "espalda": ["espalda","remo","dominad","jalón","jalon","pull","pullover"],
    "hombro": ["hombro","deltoid","elevación lateral","elevacion lateral","press militar","arnold"],
    "pierna": ["pierna","piernas","lower","inferior","sentadilla","prensa","zancada","femoral","peso muerto rumano","gemelos","cuádriceps","cuadriceps"],
    "glúteo": ["glúteo","gluteo","glutes","glute","hip thrust","puente de glúteo","puente de gluteo"]
}

def _norm(x: str) -> str:
    return (x or "").lower()

def _day_has_group(d: dict, group_key: str) -> bool:
    keys = MUSCLES_SYNONYMS.get(group_key, [group_key])
    name = _norm(d.get("nombre",""))
    if any(k in name for k in keys):
        return True
    for ej in d.get("ejercicios", []):
        n = _norm(ej.get("nombre",""))
        if any(k in n for k in keys):
            return True
    return False

def _count_days_for_group(plan: dict, group_key: str) -> int:
    return sum(1 for d in plan.get("dias", []) if _day_has_group(d, group_key))

def _count_exercises_for_group(plan: dict, group_key: str) -> int:
    keys = MUSCLES_SYNONYMS.get(group_key, [group_key])
    c = 0
    for d in plan.get("dias", []):
        for ej in d.get("ejercicios", []):
            n = _norm(ej.get("nombre",""))
            if any(k in n for k in keys):
                c += 1
    return c

CARDIO_KEYWORDS = ["cardio","cinta","trote","correr","run","running","elíptica","eliptica","bicicleta","spinning","remo","erg","hiit","saltos","jumping jacks","burpees","saltar comba","comba","escaladora","stepper","air bike"]
MACHINE_KEYWORDS = ["máquina","maquina","machine","prensa","polea","cable","smith","hack squat","pec deck","contractora","extensión de cuádriceps","extension de cuadriceps","curl femoral","jalón en polea","jalon en polea","cruce en polea","pulldown"]
BARBELL_KEYWORDS = ["barra","barbell"]
DUMBBELL_KEYWORDS = ["mancuerna","mancuernas","dumbbell","db"]

def _is_cardio_exercise(ej: dict) -> bool:
    n = _norm(ej.get("nombre",""))
    return any(k in n for k in CARDIO_KEYWORDS)

def _exercise_minutes(ej: dict) -> int | None:
    for k in ["duracion_minutos","duración_minutos","tiempo_minutos","minutos"]:
        v = ej.get(k)
        try:
            if isinstance(v, (int,float)) and v > 0:
                return int(v)
            if isinstance(v, str):
                import re as _re
                m = _re.search(r"(\\d+)\\s*(?:min|mins|minutos|’|')", v.lower())
                if m:
                    return int(m.group(1))
        except Exception:
            pass
    import re as _re
    text = " ".join([_norm(ej.get("nombre","")), _norm(ej.get("descripcion","")), _norm(ej.get("notas",""))])
    m = _re.search(r"(\\d+)\\s*(?:min|mins|minutos|’|')", text)
    if m:
        return int(m.group(1))
    return None

def _day_has_cardio_minutes(dia: dict, min_minutes: int) -> bool:
    for ej in dia.get("ejercicios", []):
        if _is_cardio_exercise(ej):
            mins = _exercise_minutes(ej)
            if mins is not None and mins >= min_minutes:
                return True
    return False

def _exercise_uses_any(ej: dict, keywords: list[str]) -> bool:
    n = _norm(ej.get("nombre",""))
    return any(k in n for k in keywords)


def validar_comentarios(plan: dict, comentarios: str) -> list[str]:
    """
    Reglas estrictas derivadas de 'comentarios' del usuario.
    """
    errs: list[str] = []
    if not comentarios or not isinstance(comentarios, str):
        return errs

    txt = comentarios.strip().lower()

    def _norm(s: str) -> str:
        return (s or "").strip().lower()

    def _exercise_minutes(e: dict):
        try:
            v = e.get("minutos", e.get("duracion_min"))
            return int(v) if v is not None and str(v).strip() != "" else None
        except Exception:
            return None

    def _day_has_cardio_minutes(d: dict, min_minutes: int) -> bool:
        for ej in d.get("ejercicios", []):
            n = _norm(ej.get("nombre", ""))
            if any(k in n for k in ("cardio","cinta","trote","correr","bicic","elípt","elipt","escalador","remo")):
                mins = _exercise_minutes(ej)
                if mins is not None and mins >= min_minutes:
                    return True
        return False

    if re.search(r"solo\\s+un\\s+d[ií]a\\s+de\\s+pierna", txt):
        leg_terms=("pierna","glúteo","gluteo","cuádriceps","cuadriceps","isquio","femoral","gemelo","glutes","legs")
        leg_days=0
        for d in plan.get("dias", []):
            ej=d.get("ejercicios", [])
            leg_like=sum(1 for e in ej if any(t in _norm(e.get("nombre","")) for t in leg_terms))
            if leg_like>=max(1, round(max(1,len(ej))*0.5)): leg_days+=1
        if leg_days>1: errs.append(f"Pediste 'solo un día de pierna' y hay {leg_days} días tipo pierna.")

    m=re.search(r"(?:m[áa]ximo|max|como\\s+mucho)\\s+(\\d+)\\s+ejercicios\\s+por\\s+(?:sesión|sesion|d[ií]a|dia)", txt)
    if m:
        limit=int(m.group(1))
        for i,d in enumerate(plan.get("dias", []), start=1):
            cnt=len(d.get("ejercicios", []))
            if cnt>limit: errs.append(f"Máximo {limit} ejercicios por sesión: el día {i} tiene {cnt}.")

    if re.search(r"no\\s+repetir\\s+ejercicio[s]?(?:\\s+exactos?)?\\s+en\\s+la\\s+semana|no\\s+repetir\\s+ejercicios", txt):
        seen=set(); dup=set()
        for d in plan.get("dias", []):
            for ej in d.get("ejercicios", []):
                n=_norm(ej.get("nombre",""))
                if not n: continue
                if n in seen: dup.add(n)
                seen.add(n)
        for n in sorted(dup): errs.append(f"No repetir ejercicios exactos: '{n}'.")

    m=re.search(r"(?:incluir|a(?:ñ|n)adir|meter)\\s+calentamiento\\s+de\\s+(\\d+)\\s*(?:min|mins|minutos)(?:\\s+cada\\s+d[ií]a)?", txt)
    if m:
        need=int(m.group(1))
        for i,d in enumerate(plan.get("dias", []), start=1):
            found=False
            for ej in d.get("ejercicios", []):
                if "calentamiento" in _norm(ej.get("nombre","")):
                    mins=_exercise_minutes(ej)
                    if mins is None or mins<need: errs.append(f"Calentamiento de {need} min requerido en día {i}.")
                    found=True; break
            if not found: errs.append(f"Incluir calentamiento de {need} min en el día {i}.")

    if re.search(r"(?:incluir|a(?:ñ|n)adir|meter)\\s+estiramientos", txt):
        for i,d in enumerate(plan.get("dias", []), start=1):
            ok=any("estir" in _norm(ej.get("nombre","")) for ej in d.get("ejercicios", []))
            if not ok: errs.append(f"Incluir estiramientos al final del día {i}.")

    m=re.search(r"m[ií]nimo\\s+(\\d+)\\s*(?:min|mins|’|')\\s+de\\s+cardio\\s+(\\d+)\\s+d[ií]as?", txt)
    if m:
        mins=int(m.group(1)); days=int(m.group(2))
        ok_days=sum(1 for d in plan.get("dias", []) if _day_has_cardio_minutes(d, mins))
        if ok_days<days: errs.append(f"Cardio mínimo {mins} min en {days} días: solo hay {ok_days} días OK.")

    m=re.search(r"m[aá]s\\s+ejercicios\\s+de\\s+([a-záéíóúñ\\s]+)", txt)
    if m:
        target=_norm(m.group(1)); count=0
        for d in plan.get("dias", []):
            for e in d.get("ejercicios", []):
                if target and target in _norm(e.get("nombre","")): count+=1
        if count<3: errs.append(f"Pediste más ejercicios de '{target}': hay {count}, se esperaban ≥ 3.")

    m=re.search(r"menos\\s+ejercicios\\s+de\\s+([a-záéíóúñ\\s]+)", txt)
    if m:
        target=_norm(m.group(1)); count=0
        for d in plan.get("dias", []):
            for e in d.get("ejercicios", []):
                if target and target in _norm(e.get("nombre","")): count+=1
        if count>2: errs.append(f"Pediste menos ejercicios de '{target}': hay {count}, se esperaban ≤ 2.")

    m=re.search(r"(?:meter|incluir|hacer)\\s+([a-záéíóúñ\\s]+?)\\s+(\\d+)\\s+(?:veces|d[ií]as)", txt)
    if m:
        target=_norm(m.group(1)); N=int(m.group(2)); days_with=0
        for d in plan.get("dias", []):
            if any(target in _norm(e.get("nombre","")) for e in d.get("ejercicios", [])): days_with+=1
        if days_with!=N: errs.append(f"'{target}' debe aparecer exactamente {N} días y aparece {days_with}.")

    no_machines=bool(re.search(r"(?:no\\s+máquinas|no\\s+maquinas|solo\\s+peso\\s+libre)", txt))
    no_cables  =bool(re.search(r"(?:no\\s+poleas|no\\s+cables?)", txt))
    no_smith="no smith" in txt or "sin smith" in txt
    no_bar=bool(re.search(r"(?:no\\s+barra[s]?|sin\\s+barra[s]?)", txt))
    no_db=bool(re.search(r"(?:no\\s+mancuernas|sin\\s+mancuernas)", txt))
    BARBELL_KEYWORDS=("barra","barbell"); DUMBBELL_KEYWORDS=("mancuerna","mancuernas","dumbbell","db")
    MACHINE_KEYWORDS=("máquina","maquina","machine","selectorizada"); CABLE_KEYWORDS=("polea","poleas","cable","cables")
    if any((no_machines,no_cables,no_smith,no_bar,no_db)):
        for i,d in enumerate(plan.get("dias", []), start=1):
            for ej in d.get("ejercicios", []):
                name=_norm(ej.get("nombre",""))
                if no_machines and any(k in name for k in MACHINE_KEYWORDS): errs.append(f"Sin máquinas: '{ej.get('nombre','')}' en día {i}.")
                if no_cables and any(k in name for k in CABLE_KEYWORDS): errs.append(f"Sin poleas/cables: '{ej.get('nombre','')}' en día {i}.")
                if no_smith and "smith" in name: errs.append(f"Sin Smith: '{ej.get('nombre','')}' en día {i}.")
                if no_bar and any(k in name for k in BARBELL_KEYWORDS): errs.append(f"Sin barra: '{ej.get('nombre','')}' en día {i}.")
                if no_db and any(k in name for k in DUMBBELL_KEYWORDS): errs.append(f"Sin mancuernas: '{ej.get('nombre','')}' en día {i}.")

    m=re.search(r"(?:al\\s+menos|min[ií]mo|como\\s+min[ií]mo)\\s*(\\d+)\\s*(?:ejercicios?\\s+)?de\\s+b[ií]ceps", txt)
    more_biceps=bool(re.search(r"(m[aá]s\\s+ejercicios\\s+de\\s+b[ií]ceps|m[aá]s\\s+b[ií]ceps)", txt))
    min_bi=int(m.group(1)) if m else (3 if more_biceps else None)
    if min_bi is not None:
        total_bi=0; bi_terms=("curl","predicador","martillo","hammer curl","inclinado con mancuernas")
        for d in plan.get("dias", []):
            for e in d.get("ejercicios", []):
                name=_norm(e.get("nombre",""))
                gp=_norm(e.get("musculo_principal","")) or _norm(e.get("grupo",""))
                sp=_norm(e.get("musculo_secundario",""))
                if "biceps" in name or "bíceps" in name or "bicep" in name or "bícep" in name: total_bi+=1
                elif any(t in name for t in bi_terms): total_bi+=1
                elif "biceps" in gp or "bíceps" in gp or "biceps" in sp or "bíceps" in sp: total_bi+=1
        if total_bi<min_bi: errs.append(f"Pediste bíceps ≥ {min_bi} y solo se detectan {total_bi} ejercicios de bíceps en la semana.")

    return errs


def validar_objetivo(plan: Dict[str, Any], A: Dict[str, Any]) -> List[str]:
    """Validaciones extra para asegurar que la rutina respeta el objetivo y las consignas."""
    errs: List[str] = []
    if not isinstance(plan, dict):
        return ['Plan inválido (no es dict).']

    objetivo = (A.get('objetivo') or '').lower()
    dias_user = A.get('disponibilidad') or []
    # Días exactos
    try:
        dias_plan = plan.get('dias') or []
        if isinstance(dias_plan, list) and dias_user and len(dias_plan) == len(dias_user):
            nombres = [str(d.get('nombre','')).strip() for d in dias_plan if isinstance(d, dict)]
            # si al menos 2 coinciden, exigimos que coincidan todos
            if any(n in dias_user for n in nombres):
                for i,(n_exp, n_got) in enumerate(zip(dias_user, nombres), start=1):
                    # Permitimos sufijos tipo "Lunes - Push A" siempre que incluya el día.
                    if n_got and (n_exp.lower() not in n_got.lower()):
                        errs.append(f"Día {i}: el nombre debe incluir '{n_exp}' (según disponibilidad), pero llegó '{n_got}'.")
    except Exception:
        pass

    # Heurística reps bajas
    def is_low_rep(reps: str) -> bool:
        try:
            r = str(reps).strip().replace('–','-')
            if '-' in r:
                a,b=r.split('-',1)
                a=int(a.strip()); b=int(b.strip())
                return b <= 6
            return int(r) <= 6
        except Exception:
            return False

    if objetivo == 'hipertrofia':
        # máximo 1 ejercicio "bajo" por día
        for i,d in enumerate(plan.get('dias', []) or [], start=1):
            lows = 0
            for ej in (d.get('ejercicios') or []):
                if is_low_rep(ej.get('reps','')):
                    lows += 1
            if lows > 1:
                errs.append(f"Día {i}: demasiados ejercicios en rango <=6 reps para hipertrofia (hay {lows}).")

        # cobertura básica brazos/hombro lateral (al menos 1/semana)
        names = ' '.join([(ej.get('nombre','') or '').lower() for d in plan.get('dias', []) or [] for ej in (d.get('ejercicios') or [])])
        if not any(k in names for k in ('curl', 'bíceps', 'biceps', 'martillo', 'predicador')):
            errs.append("Hipertrofia: falta trabajo directo de bíceps en la semana.")
        if not any(k in names for k in ('tríceps', 'triceps', 'jalón de tríceps', 'extensión de tríceps', 'fondos', 'pushdown', 'skull')):
            errs.append("Hipertrofia: falta trabajo directo de tríceps en la semana.")
        if not any(k in names for k in ('elevaciones laterales', 'lateral', 'deltoide lateral', 'laterales')):
            errs.append("Hipertrofia: falta trabajo directo de deltoide lateral (elevaciones laterales o equivalente).")

    elif objetivo == 'fuerza':
        # al menos 1 ejercicio bajo por día (principal)
        for i,d in enumerate(plan.get('dias', []) or [], start=1):
            lows = 0
            for ej in (d.get('ejercicios') or []):
                if is_low_rep(ej.get('reps','')):
                    lows += 1
            if lows == 0:
                errs.append(f"Fuerza: Día {i} debería incluir al menos 1 principal en 3-6 reps.")

    return errs


# --- Validaciones extra para evitar desvíos del prompt ---
_CORE_PREFIX = ("core:", "finisher:")
_CORE_KEYWORDS = ("plancha", "abdominal", "core", "hollow", "dead bug", "pallof", "crunch", "elevación de piernas", "elevacion de piernas", "farmer")
_TRICEPS_KEYWORDS = ("tríceps", "triceps", "extensión tríceps", "extension triceps", "pushdown", "jalón de tríceps", "jalon de triceps", "fondos", "press francés", "press frances", "skull")


def _nrm_name(s: str) -> str:
    return (s or "").strip().lower()


def _has_core_or_finisher(dia: dict) -> bool:
    for ej in dia.get("ejercicios", []) or []:
        nm = _nrm_name(ej.get("nombre", ""))
        if nm.startswith(_CORE_PREFIX):
            return True
        if any(k in nm for k in _CORE_KEYWORDS):
            return True
    return False


def _is_lower_day(dia: dict) -> bool:
    nm = _nrm_name(dia.get("nombre", ""))
    if any(k in nm for k in ("legs", "pierna", "lower")):
        return True
    # Heurística: si >=50% de ejercicios son de pierna, lo tratamos como lower
    leg_terms = ("sentadilla", "prensa", "zancada", "femoral", "isquio", "gemelo", "cuádriceps", "cuadriceps", "glúteo", "gluteo", "hip thrust", "peso muerto rumano")
    ej = dia.get("ejercicios", []) or []
    if not ej:
        return False
    leg_like = sum(1 for e in ej if any(t in _nrm_name(e.get("nombre", "")) for t in leg_terms))
    return leg_like >= max(1, round(len(ej) * 0.5))


def _parse_rest_to_seconds(rest: str) -> float:
    import re as _re
    s = _nrm_name(rest).replace(" ", "")
    if not s:
        return 60.0
    # 2-3m
    m = _re.match(r"^(\d+(?:\.\d+)?)\-(\d+(?:\.\d+)?)(?:m|min)$", s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return ((a + b) / 2.0) * 60.0
    # 120-180s
    m = _re.match(r"^(\d+(?:\.\d+)?)\-(\d+(?:\.\d+)?)(?:s|seg)$", s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return (a + b) / 2.0
    # 2m / 120s
    m = _re.match(r"^(\d+(?:\.\d+)?)(?:m|min)$", s)
    if m:
        return float(m.group(1)) * 60.0
    m = _re.match(r"^(\d+(?:\.\d+)?)(?:s|seg)$", s)
    if m:
        return float(m.group(1))
    return 60.0


def _estimate_day_minutes(dia: dict) -> float:
    """Estimación simple de duración basada en series + descanso.

    No es perfecta, pero sirve para detectar desviaciones grandes (>60 min) y forzar refino.
    """
    total_sec = 0.0
    for ej in dia.get("ejercicios", []) or []:
        try:
            sets = int(ej.get("series", 3) or 3)
        except Exception:
            sets = 3
        reps = _nrm_name(str(ej.get("reps", "10")))
        # trabajo por serie aproximado
        work = 45.0 if any(ch.isdigit() for ch in reps) and ("-" in reps or reps.isdigit()) and (int(reps.split("-")[-1]) if reps.split("-")[-1].isdigit() else 10) <= 10 else 35.0
        rest = _parse_rest_to_seconds(str(ej.get("descanso", "60s")))
        # tiempo de la serie + descanso (no contamos el descanso del final del ejercicio)
        total_sec += sets * work
        if sets > 1:
            total_sec += (sets - 1) * rest
        # pequeñas transiciones / setup
        total_sec += sets * 12.0
    # transiciones entre ejercicios
    total_sec += max(0, (len(dia.get("ejercicios", []) or []) - 1)) * 25.0
    return total_sec / 60.0


def _postprocess_plan(plan: dict, A: dict) -> dict:
    """Ajustes deterministas para reducir desvíos típicos.

    - Fuerza nombres de días a '<DíaSemana> - <Sesión>' si hay template.
    - Asegura que existe core/finisher diario (añadiéndolo si hay hueco).
    """
    try:
        dias = plan.get("dias") or []
        disp = A.get("disponibilidad") or []
        template = A.get("split_template")
        for i, d in enumerate(dias):
            if not isinstance(d, dict):
                continue
            # Nombres según disponibilidad + template
            if i < len(disp):
                if template and i < len(template):
                    d["nombre"] = f"{disp[i]} - {template[i]}"
                else:
                    d["nombre"] = disp[i]
            # Core/finisher
            ej = d.get("ejercicios") or []
            if isinstance(ej, list):
                if not _has_core_or_finisher(d):
                    core_name = "Core: Plancha" if i % 2 == 0 else "Core: Pallof press"
                    core_ej = {"nombre": core_name, "series": 3, "reps": "30-45", "descanso": "45-60s", "rir": "1-3", "notas": "core/finisher"}
                    if len(ej) < 8:
                        ej.append(core_ej)
                    elif ej:
                        ej[-1] = core_ej
                    d["ejercicios"] = ej
    except Exception:
        return plan
    return plan


def validar_estructura_split(plan: Dict[str, Any], A: Dict[str, Any], datos: Dict[str, Any]) -> List[str]:
    """Validación estricta para minimizar el desvío entre prompt y salida."""
    errs: List[str] = []
    dias = plan.get("dias") or []
    if not isinstance(dias, list):
        return ["Campo 'dias' inválido (no es lista)."]

    # 5-8 ejercicios y core/finisher diario
    for i, d in enumerate(dias, start=1):
        if not isinstance(d, dict):
            continue
        ej = d.get("ejercicios") or []
        if isinstance(ej, list):
            if len(ej) < 5 or len(ej) > 8:
                errs.append(f"Día {i}: debe tener 5-8 ejercicios (tiene {len(ej)}).")
        if not _has_core_or_finisher(d):
            errs.append(f"Día {i}: falta core/finisher (último ejercicio debe empezar por 'Core:' o 'Finisher:').")

    # Días exactos + split en nombre
    disp = A.get("disponibilidad") or []
    template = A.get("split_template")
    if disp and isinstance(template, list) and len(template) == len(disp) == len(dias):
        for i, (d_exp, s_exp) in enumerate(zip(disp, template), start=1):
            got = _nrm_name((dias[i-1].get("nombre") or ""))
            if _nrm_name(d_exp) not in got or _nrm_name(s_exp) not in got:
                errs.append(f"Día {i}: nombre debe ser '{d_exp} - {s_exp}'.")

    # No duplicar ejercicio exacto en la semana (salvo core/finisher)
    seen = set()
    dup = set()
    for d in dias:
        for ej in d.get("ejercicios", []) or []:
            nm = _nrm_name(ej.get("nombre", ""))
            if not nm:
                continue
            if nm.startswith(_CORE_PREFIX):
                continue
            if nm in seen:
                dup.add(nm)
            seen.add(nm)
    for n in sorted(dup):
        errs.append(f"No repetir ejercicio exacto en la semana: '{n}'.")

    # Lower: evitar tríceps
    for i, d in enumerate(dias, start=1):
        if _is_lower_day(d):
            for ej in d.get("ejercicios", []) or []:
                nm = _nrm_name(ej.get("nombre", ""))
                if any(k in nm for k in _TRICEPS_KEYWORDS):
                    errs.append(f"Día {i} (Lower): contiene tríceps '{ej.get('nombre','')}'.")

    # Duración estimada
    try:
        dur = int(A.get("duracion") or datos.get("duracion") or 60)
    except Exception:
        dur = 60
    for i, d in enumerate(dias, start=1):
        mins = _estimate_day_minutes(d)
        # tolerancia pequeña
        if mins > (dur + 5):
            errs.append(f"Día {i}: estimación de tiempo ~{mins:.0f} min (objetivo {dur} min). Reduce series/descansos o usa superseries solo en accesorios.")

    # Deload alineado con semanas de ciclo si existe
    try:
        semanas = int(datos.get("semanas_ciclo") or 0)
    except Exception:
        semanas = 0
    if semanas:
        try:
            dld = int((plan.get("progresion") or {}).get("deload_semana") or 0)
        except Exception:
            dld = 0
        if dld and dld != semanas:
            errs.append(f"Deload: debe ser en la semana {semanas} (se recibió {dld}).")

    return errs
def call_gpt(datos: Dict[str, Any]) -> Dict[str, Any]:

    # --- Pre-análisis y normalización (cumplir consignas) ---
    A = analyze_user_data(datos)
    datos = dict(datos)
    # Forzamos que el prompt y el schema reflejen exactamente las consignas normalizadas
    datos.update({
        "objetivo": A["objetivo"],
        "nivel": A["nivel"],
        "dias": A["dias"],
        "duracion": A["duracion"],
        "duracion_min": A["duracion"],
        "disponibilidad": A["disponibilidad"],
        "material": A["material"],
        "limitaciones": A.get("limitaciones") or "",
        "lesiones": A.get("limitaciones") or "",
        "evitar": A.get("evitar") or [],
        "rir_obj": A.get("rir_obj", 2),
    })
    datos["__analysis"] = A

    client = _client()
    _system = build_system()
    _prompt = build_prompt(datos)
    raw = _chat(client, _prompt, temperature=0.1)

    # Primer intento de parseo
    try:
        data = _try_parse_json(raw)
    except Exception as e:
        return {"ok": False, "error": f"JSON no válido: {e}", "raw": raw, "prompt": _prompt, "system": _system}

    # Validación + coerción
    coerced = _coerce_to_schema(data, datos)
    coerced = _sanitize_plan_reps(coerced)
    coerced = _postprocess_plan(coerced, A)
    errs = []
    errs += validar_negocio(coerced)
    try:
        errs += validar_comentarios(coerced, (datos.get("comentarios") or ""))
    except Exception:
        pass
    try:
        errs += validar_objetivo(coerced, A)
    except Exception:
        pass
    try:
        errs += validar_estructura_split(coerced, A, datos)
    except Exception:
        pass

    if not errs:
        return {"ok": True, "data": coerced, "prompt": _prompt, "system": _system}

    # Intento de REFINADO: bucle de corrección (máx 3) con temperatura baja.
    nl = chr(10)
    fixed = None
    last_raw = raw
    last_errs = errs
    for _attempt in range(3):
        fix_prompt = (
            "Corrige el JSON de rutina para que cumpla EXACTAMENTE todas las reglas.\n"
            "IMPORTANTE: Devuelve EXCLUSIVAMENTE JSON válido. Sin texto extra.\n\n"
            "REGLAS (resumen):\n"
            "- 5-8 ejercicios por día.\n"
            "- Último ejercicio de cada día: Core/Finisher y debe empezar por 'Core:' o 'Finisher:'.\n"
            "- Respetar el split y el nombre del día '<DíaSemana> - <Sesión>' si se especifica.\n"
            "- No repetir exactamente el mismo ejercicio en la semana (salvo core/finisher).\n"
            "- Ajustar volumen/descansos para cumplir el tiempo.\n\n"
            "ERRORES A CORREGIR (no ignores ninguno):\n" + json.dumps(last_errs, ensure_ascii=False, indent=2) + "\n\n"
            "PROMPT ORIGINAL (para referencia):\n" + _prompt + "\n\n"
            "JSON ORIGINAL:\n" + json.dumps(coerced if fixed is None else fixed, ensure_ascii=False)
        )
        fixed_raw = _chat(client, fix_prompt, temperature=0.0)
        last_raw = fixed_raw
        try:
            fixed = _try_parse_json(fixed_raw)
        except Exception:
            fixed = None
            continue

        fixed = _coerce_to_schema(fixed, datos)
        fixed = _sanitize_plan_reps(fixed)
        fixed = _postprocess_plan(fixed, A)

        errs2 = []
        errs2 += validar_negocio(fixed)
        try:
            errs2 += validar_comentarios(fixed, (datos.get("comentarios") or ""))
        except Exception:
            pass
        try:
            errs2 += validar_objetivo(fixed, A)
        except Exception:
            pass
        try:
            errs2 += validar_estructura_split(fixed, A, datos)
        except Exception:
            pass

        if not errs2:
            return {"ok": True, "data": fixed, "prompt": _prompt, "system": _system}
        last_errs = errs2
    # Si no pudo corregirse, devolvemos el último estado para depurar.
    return {"ok": False, "error": f"Refinado aún con errores: {last_errs}", "raw": last_raw, "prompt": _prompt, "system": _system}
import re as _re2

def _sanitize_reps_value(val) -> str:
    """
    Normaliza reps para cumplir regex esperado: "5" o "6-8" o "10-12".
    - Reemplaza guiones largos/en-dash por "-"
    - Quita texto como "reps", "por lado", "cada lado", etc.
    - Si hay >1 número, devuelve "a-b" (primer-par). Si solo 1, devuelve "n".
    """
    if val is None:
        return ""
    s = str(val).strip().lower()
    s = s.replace("–", "-").replace("—", "-")
    # Limpia palabras comunes
    for t in ["reps", "rep", "por lado", "cada lado", "lado", "c/u", "por brazo", "por pierna"]:
        s = s.replace(t, "")
    # Quita paréntesis residuales
    s = s.replace("(", " ").replace(")", " ")
    # Extrae números
    nums = _re2.findall(r"\d+", s)
    if not nums:
        return ""
    if len(nums) == 1:
        return nums[0]
    # Usa los dos primeros números como rango coherente
    a, b = int(nums[0]), int(nums[1])
    if a > b:
        a, b = b, a
    return f"{a}-{b}"

def _sanitize_plan_reps(plan: dict) -> dict:
    try:
        for d in plan.get("dias", []):
            for ej in d.get("ejercicios", []):
                repv = ej.get("reps", "")
                rep_clean = _sanitize_reps_value(repv)
                if rep_clean:
                    ej["reps"] = rep_clean
    except Exception:
        pass
    return plan


# Aviso: no se detectó patrón de validación; añade HARD-FAIL wrapper si usas otra función de generación.


# --- NUEVO: validador de constraints estructurados ---

def validar_constraints(plan, C):
    errs = []
    if not isinstance(C, dict):
        return errs

    def _norm(s): return (s or "").strip().lower()

    # Días por semana exactos
    if C.get("days_per_week") is not None:
        n = len(plan.get("dias", []))
        if n != int(C["days_per_week"]):
            errs.append(f"Se solicitaron {C['days_per_week']} días/semana y la rutina tiene {n}.")

    # Duración por sesión (si disponible)
    for i, d in enumerate(plan.get("dias", []), start=1):
        dur = d.get("duracion_min_dia")
        if dur is None:
            minutes = 0
            for e in d.get("ejercicios", []):
                try:
                    minutes += int(e.get("minutos", e.get("duracion_min", 0)) or 0)
                except Exception:
                    pass
            dur = minutes if minutes > 0 else None
        if dur is not None:
            if C.get("session_max_minutes") and dur > int(C["session_max_minutes"]):
                errs.append(f"Día {i} excede el máximo de {C['session_max_minutes']} min (tiene {dur}).")
            if C.get("session_min_minutes") and dur < int(C["session_min_minutes"]):
                errs.append(f"Día {i} no alcanza el mínimo de {C['session_min_minutes']} min (tiene {dur}).")

    # Descansos
    if C.get("rest_seconds_range"):
        lo, hi = C["rest_seconds_range"]
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                rest = e.get("descanso_s") or e.get("descanso")
                try:
                    rest = int(str(rest).replace("s","").strip()) if rest is not None else None
                except Exception:
                    rest = None
                if rest is not None and not (lo <= rest <= hi):
                    errs.append(f"Descanso fuera de rango en día {i}, '{e.get('nombre','')}' ({rest}s no está en {lo}-{hi}s).")

    # Tempo
    if C.get("default_tempo"):
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                if not (e.get("tempo") or "").strip():
                    errs.append(f"Falta tempo en día {i}, '{e.get('nombre','')}' (se pidió default {C['default_tempo']}).")

    # RIR / RPE
    import re as _re
    if C.get("rir_range"):
        lo, hi = C["rir_range"]
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                rir = str(e.get("rir","")).strip().lower()
                if rir and rir not in ("fallo","-1","0"):
                    m = _re.search(r"-?\d+", rir)
                    if m:
                        val = int(m.group(0))
                        if not (lo <= val <= hi):
                            errs.append(f"RIR {rir} fuera de rango {lo}-{hi} en día {i}, '{e.get('nombre','')}'.")
    if C.get("rpe_range"):
        lo, hi = C["rpe_range"]
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                try:
                    rpe = float(e.get("rpe")) if e.get("rpe") is not None else None
                except Exception:
                    rpe = None
                if rpe is not None and not (lo <= rpe <= hi):
                    errs.append(f"RPE {rpe} fuera de rango {lo}-{hi} en día {i}, '{e.get('nombre','')}'.")

    # Inclusiones
    if C.get("include_warmup"):
        has = any("calentamiento" in _norm(e.get("nombre","")) for d in plan.get("dias", []) for e in d.get("ejercicios", []))
        if not has: errs.append("Se pidió incluir calentamiento y no se detecta.")
    if C.get("include_mobility"):
        has = any("movilidad" in _norm(e.get("nombre","")) for d in plan.get("dias", []) for e in d.get("ejercicios", []))
        if not has: errs.append("Se pidió incluir movilidad y no se detecta.")
    if C.get("include_core"):
        has = any(any(t in _norm(e.get("nombre","")) for t in ("plancha","abdominal","core","hollow","dead bug","pallof"))
                  for d in plan.get("dias", []) for e in d.get("ejercicios", []))
        if not has: errs.append("Se pidió incluir core/abdominales y no se detecta.")
    if C.get("core_days_min"):
        need = int(C["core_days_min"]); got = 0
        for d in plan.get("dias", []):
            names = " ".join([_norm(e.get("nombre","")) for e in d.get("ejercicios", [])])
            if any(t in names for t in ("plancha","abdominal","core","hollow","dead bug","pallof")):
                got += 1
        if got < need:
            errs.append(f"Se pidieron {need} días con core y hay {got}.")

    # Cardio tipo
    if C.get("cardio_type") == "HIIT":
        found = any(any("hiit" in _norm(e.get("nombre","")) for e in d.get("ejercicios", [])) for d in plan.get("dias", []))
        if not found: errs.append("Se pidió cardio HIIT y no se detecta.")
    if C.get("cardio_type") == "LISS":
        found = any(any(t in _norm(e.get("nombre","")) for t in ("liss","caminata","zona 2","z2","suave","elíptica","eliptica","bici","carrera suave"))
                    for d in plan.get("dias", []) for e in d.get("ejercicios", []))
        if not found: errs.append("Se pidió cardio LISS/zona 2 y no se detecta.")

    # Equipo/home gym
    if C.get("equipment_only_dumbbells") or C.get("equipment_only_barbell") or C.get("home_gym_minimal"):
        allowed = []
        if C.get("equipment_only_dumbbells"): allowed += ["mancuerna","mancuernas","dumbbell"]
        if C.get("equipment_only_barbell"): allowed += ["barra","barbell"]
        if C.get("home_gym_minimal"): allowed += ["mancuerna","mancuernas","barra","bandas","peso corporal","bodyweight"]
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                nm = _norm(e.get("nombre",""))
                if not any(a in nm for a in allowed):
                    if not any(t in nm for t in ("flexiones","dominadas","zancadas","plancha","hip thrust")):
                        errs.append(f"Ejercicio no acorde al equipo solicitado en día {i}: '{e.get('nombre','')}'.")

    # Evitar ejercicios
    if C.get("avoid_exercises"):
        avoid = [a.strip().lower() for a in C["avoid_exercises"] if a.strip()]
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                nm = _norm(e.get("nombre",""))
                if any(a in nm for a in avoid):
                    errs.append(f"Se pidió evitar '{a}' y aparece en día {i}: '{e.get('nombre','')}'.")
                    break

    # Weekdays count
    if C.get("weekdays"):
        if len(C["weekdays"]) != len(plan.get("dias", [])):
            errs.append(f"Se indicaron {len(C['weekdays'])} días específicos pero la rutina tiene {len(plan.get('dias',[]))}.")

    # Volumen por grupo
    if C.get("volumen_series"):
        grupos = {
            "pecho":["pecho","pectorales","press banca","aperturas"],
            "espalda":["espalda","dorsal","remo","jalón","dominadas","pull down","pull-up"],
            "hombro":["hombro","deltoide","militar","overhead","elevaciones laterales","elevaciones frontales"],
            "bíceps":["bíceps","biceps","curl","martillo","predicador","inclinado"],
            "tríceps":["tríceps","triceps","fondos","extensión tríceps","jalón tríceps","press cerrado"],
            "pierna":["pierna","sentadilla","zancada","prensa","peso muerto","cuádriceps","isquio","femoral","glúteo","gluteo","hip thrust"],
            "glúteo":["glúteo","gluteo","hip thrust","patada de glúteo"],
            "core":["core","abdominal","plancha","hollow","dead bug","pallof"],
            "gemelo":["gemelo","pantorrilla","calf"]
        }
        series_por_grupo = {g:0 for g in C["volumen_series"].keys()}
        for d in plan.get("dias", []):
            for e in d.get("ejercicios", []):
                name = _norm(e.get("nombre",""))
                gp = _norm(e.get("musculo_principal","")) or _norm(e.get("grupo",""))
                try:
                    s = int(str(e.get("series")).strip()) if e.get("series") is not None else 0
                except Exception:
                    s = 0
                for g in series_por_grupo.keys():
                    aliases = grupos.get(g, [g])
                    if g in gp or any(a in name for a in aliases):
                        series_por_grupo[g] += s
                        break
        for g, rng in C["volumen_series"].items():
            lo, hi = rng if isinstance(rng, (list, tuple)) else (rng, None)
            val = series_por_grupo.get(g, 0)
            if lo is not None and val < lo:
                errs.append(f"Volumen insuficiente para {g}: {val} series (< {lo}).")
            if hi is not None and val > hi:
                errs.append(f"Volumen excesivo para {g}: {val} series (> {hi}).")

    # Orden de ejercicios
    if C.get("order_rules"):
        def is_unilateral(nm):
            nm = _norm(nm)
            return any(t in nm for t in ("unilateral","a una mano","a una pierna","alterno","alternas","búlgar","bulgara","zancada","split squat"))
        def is_basic(nm):
            nm = _norm(nm)
            basics = ("sentadilla","peso muerto","press banca","press militar","remo","dominadas","hip thrust","press inclinado","remo con barra","remo con mancuerna")
            return any(t in nm for t in basics)
        def is_accessory(nm):
            nm = _norm(nm)
            acc = ("curl","extensión tríceps","elevaciones","aperturas","cruces","pull over","face pull","patada tríceps","gemelo","pantorrilla")
            return any(t in nm for t in acc)
        for i, d in enumerate(plan.get("dias", []), start=1):
            names = [ (e.get("nombre","") or "") for e in d.get("ejercicios", []) ]
            if C["order_rules"].get("bilateral_first"):
                seen_unilateral = False
                for nm in names:
                    if is_unilateral(nm):
                        seen_unilateral = True
                    elif seen_unilateral:
                        errs.append(f"Orden incorrecto día {i}: ejercicio bilateral '{nm}' va después de un unilateral.")
                        break
            if C["order_rules"].get("basics_first"):
                first_basic = None
                first_acc = None
                for idx, nm in enumerate(names):
                    if is_basic(nm) and first_basic is None:
                        first_basic = idx
                    if is_accessory(nm) and first_acc is None:
                        first_acc = idx
                if first_acc is not None and (first_basic is None or first_acc < first_basic):
                    errs.append(f"Orden incorrecto día {i}: hay accesorios antes que básicos.")

    # Series/Reps por defecto
    if C.get("default_series_reps"):
        s_rng = C["default_series_reps"].get("series")
        r_rng = C["default_series_reps"].get("reps")
        import re as _re2
        def parse_reps(val):
            if val is None: return None, None
            txt = str(val).lower().strip()
            m = _re2.search(r"(\d+)\s*[-–x]\s*(\d+)", txt)
            if m: return int(m.group(1)), int(m.group(2))
            m = _re2.search(r"(\d+)", txt)
            if m: v = int(m.group(1)); return v, v
            return None, None
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                if s_rng:
                    try:
                        s = int(str(e.get("series")).strip()) if e.get("series") is not None else None
                    except Exception:
                        s = None
                    if s is not None and not (s_rng[0] <= s <= s_rng[1]):
                        errs.append(f"Series fuera de rango ({s}) en día {i}: '{e.get('nombre','')}', esperado {s_rng[0]}–{s_rng[1]}.")
                if r_rng:
                    r_lo, r_hi = parse_reps(e.get("reps"))
                    if r_lo is not None and not (r_rng[0] <= r_lo <= r_rng[1] and r_rng[0] <= r_hi <= r_rng[1]):
                        errs.append(f"Reps fuera de rango ({e.get('reps')}) en día {i}: '{e.get('nombre','')}', esperado {r_rng[0]}–{r_rng[1]}.")

    return errs

def enforce_simple_constraints(plan, C):
    """
    Realiza ajustes no destructivos y obvios para intentar cumplir:
    - recortar a max_exercises_per_day
    - si falta bíceps: añadir curls básicos al final del día de empuje/espalda (hasta cumplir mínimo)
    (Esto solo se aplica si no rompe otras reglas; si no se puede, se deja a validación/refine.)
    """
    if not isinstance(plan, dict) or not isinstance(C, dict):
        return plan
    plan = json.loads(json.dumps(plan))  # deep copy

    # Recorte por máximo ejercicios/día
    mx = C.get("max_exercises_per_day")
    if mx:
        for d in plan.get("dias", []):
            ej = d.get("ejercicios", [])
            if len(ej) > mx:
                d["ejercicios"] = ej[:mx]

    # Añadir bíceps si falta
    min_bi = C.get("biceps_min_total")
    if min_bi:
        def _norm(s): return (s or "").strip().lower()
        bi_terms = ("bíceps","biceps","curl","predicador","martillo","hammer curl","inclinado con mancuernas")
        def count_bi(p):
            c=0
            for d in p.get("dias", []):
                for e in d.get("ejercicios", []):
                    name=_norm(ej.get("nombre",""))
                    gp=_norm(e.get("musculo_principal","")) or _norm(e.get("grupo",""))
                    sp=_norm(e.get("musculo_secundario",""))
                    if "biceps" in name or "bíceps" in name or "bicep" in name or "bícep" in name:
                        c+=1
                    elif any(t in name for t in bi_terms):
                        c+=1
                    elif "biceps" in gp or "bíceps" in gp or "biceps" in sp or "bíceps" in sp:
                        c+=1
            return c
        cur = count_bi(plan)
        needed = int(min_bi) - cur
        if needed > 0:
            # Distribuir curls hasta cubrir
            templates = [
                {"nombre":"Curl con barra", "series":3, "reps":"8-12", "rir":"1-2", "musculo_principal":"bíceps"},
                {"nombre":"Curl martillo con mancuernas", "series":3, "reps":"10-12", "rir":"1-2", "musculo_principal":"bíceps"},
                {"nombre":"Curl en banco inclinado", "series":3, "reps":"10-12", "rir":"1-2", "musculo_principal":"bíceps"}
            ]
            di = 0
            for _ in range(needed):
                if not plan.get("dias"):
                    break
                d = plan["dias"][di % len(plan["dias"])]
                d.setdefault("ejercicios", []).append(templates[_ % len(templates)])
                di += 1

    return plan


def _extract_json(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Respuesta vacía")
    m = _safe_json_search(JSON_MD_RE, text)
    if m:
        return m.group(1)
    m = _safe_json_search(JSON_BLOCK_RE, text)
    if m:
        return m.group(0)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    raise ValueError("No se encontró bloque JSON")



def _client():
    """Return an OpenAI client for both SDK v1+ and legacy v0.28.

    If the modern class is not available, fall back to the legacy 'openai' module.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
    if OpenAI is not None:
        # New SDK
        if base_url:
            return OpenAI(api_key=api_key, base_url=base_url)
        return OpenAI(api_key=api_key)
    else:
        # Legacy SDK
        import openai as _openai
        _openai.api_key = api_key
        if base_url:
            try:
                _openai.base_url = base_url
            except Exception:
                pass
        return _openai



def _compute_primary_blocks(datos: dict) -> list[str]:
    dias_raw = datos.get("dias", 4)
    disponibilidad = datos.get("disponibilidad") or []
    if isinstance(dias_raw, (list, tuple)):
        n = max(1, len(dias_raw))
    elif isinstance(disponibilidad, (list, tuple)) and disponibilidad:
        n = len(disponibilidad)
    else:
        try:
            n = int(dias_raw)
        except Exception:
            n = 4
    base = ["Pecho", "Espalda", "Pierna", "Hombros", "Empuje", "Tirón"]
    plan = base[:n]
    if "Pierna" not in plan and n >= 1:
        insert_at = 2 if n >= 3 else n-1
        insert_at = max(0, insert_at)
        plan[min(insert_at, n-1)] = "Pierna"
    for i in range(1, len(plan)):
        if plan[i] == plan[i-1]:
            plan[i] = "Hombros"
    return plan
