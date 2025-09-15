import json
import re
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)

def _extract_json(text: str):
    """
    Extrae JSON de una respuesta de la IA intentando:
    1) bloque ```json ... ```
    2) primer objeto { ... } balanceado
    3) parseo directo
    """
    if not text or not str(text).strip():
        raise ValueError("Respuesta vacía")

    m = JSON_BLOCK_RE.search(text)
    if m:
        cand = m.group(1).strip()
        return json.loads(cand)

    first = text.find("{"); last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        cand = text[first:last+1]
        cand = re.sub(r",\s*([}\]])", r"\1", cand)  # arregla comas colgantes simples
        return json.loads(cand)

    return json.loads(text)
import os, json
from typing import Any, Dict
from openai import OpenAI
from .schema_rutina import validar_negocio



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
                "deload_semana": 5
            }
        elif "lineal" in pref:
            data["progresion"] = {
                "principales": "aumenta carga 2.5–5% cuando completes el rango de reps",
                "accesorios": "mantén técnica y suma reps gradualmente",
                "deload_semana": 6
            }
        else:
            data["progresion"] = {
                "principales": "progresión simple: subir reps o carga cada semana si es posible",
                "accesorios": "reps adicionales o pausas más cortas",
                "deload_semana": 6
            }

    
    # Asegurar que progresion sea dict válido
    pref_in = data.get("progresion")
    if not isinstance(pref_in, dict):
        pref = str(pref_in or datos.get("progresion_preferida", "lineal")).lower()
        if "doble" in pref:
            data["progresion"] = {
                "principales": "doble progresión en carga o repeticiones",
                "accesorios": "añadir 1-2 repeticiones por semana hasta rango tope",
                "deload_semana": 5
            }
        elif "lineal" in pref:
            data["progresion"] = {
                "principales": "aumenta carga 2.5–5% cuando completes el rango de reps",
                "accesorios": "mantén técnica y suma reps gradualmente",
                "deload_semana": 6
            }
        else:
            data["progresion"] = {
                "principales": "progresión simple: subir reps o carga cada semana si es posible",
                "accesorios": "reps adicionales o pausas más cortas",
                "deload_semana": 6
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

def build_system() -> str:
    return "Eres un entrenador personal experto. Devuelve exclusivamente JSON válido, sin texto adicional."

def build_prompt(datos: Dict[str, Any]) -> str:
    """Construye el prompt para la IA respetando reglas y preferencias del usuario."""
    agrup = datos.get("agrupacion", "Varios grupos principales por día")
    material = datos.get("material", [])
    notas = datos.get("comentarios", "")
    objetivo = datos.get("objetivo", "mixto")
    nivel = datos.get("nivel", "intermedio")

    reglas_estrictas = f"""
REGLAS ESTRICTAS (debes cumplirlas sí o sí):
- Agrupación pedida: {agrup}
- Si es "Un solo grupo principal por día":
  * EXACTAMENTE 1 grupo principal por día.
  * No mezclar dos grupos principales (p. ej., pecho y espalda) el mismo día.
  * Accesorios subordinados al principal (bíceps con espalda, tríceps con pecho) permitidos.
- Si es "Varios grupos principales por día":
  * Máximo 2 principales salvo que el usuario pida 3 explícitamente.
  * Evitar solapar el mismo grupo en días consecutivos si el volumen es alto.
- Material:
  * Si la lista incluye "todo": asume gimnasio comercial COMPLETO (barras, mancuernas, poleas, máquinas, rack, banco, discos, gomas, etc.).
  * Si es personalizado, usa SOLO el material listado.
- Respeta lesiones/limitaciones y el objetivo indicado.
- Ajusta volumen y selección de ejercicios al objetivo ({objetivo}) y nivel ({nivel}).
{("\n- INDICACIONES DEL USUARIO (OBLIGATORIAS):\n  " + notas) if notas else ""}
""".strip("\n")

    prompt = f"""
Eres un entrenador personal experto. Devuelve exclusivamente JSON válido, sin texto adicional.

Genera una rutina semanal siguiendo estas reglas base:
{RULES_TEXT.format(dur=datos.get('duracion', 60))}

{reglas_estrictas}

ENTRADA DEL USUARIO (estructura):
- Nivel: {nivel}
- Días/semana: {datos.get('dias')}
- Duración (min): {datos.get('duracion')}
- Objetivo: {objetivo}
- Material: {material}
- Lesiones/limitaciones: {datos.get('limitaciones','')}
- Disponibilidad: {datos.get('disponibilidad',[])}
- Progresión preferida: {datos.get('progresion_preferida','')}
- Tolerancia a volumen: {datos.get('volumen_tolerancia','')}
- Semanas del ciclo: {datos.get('semanas_ciclo','')}
- Superseries: {datos.get('superseries_ok')}
- Unidades: {datos.get('unidades','kg')}
- Idioma: {datos.get('idioma','es')}
- PR recientes: {datos.get('pr_recientes',{})}
- Énfasis accesorios: {datos.get('enfasis_accesorios',[])}
- Evitar: {datos.get('evitar',[])}
- Calentamiento: {datos.get('calentamiento','')}
- Agrupación: {agrup}

SALIDA (JSON): Sigue exactamente el esquema esperado por el validador; no incluyas texto fuera del JSON.
"""
    return prompt

def _client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _chat(client: OpenAI, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.4,
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
    Soporta expresiones como:
      - "solo N días de pierna" / "solo N días (por semana)"
      - "más ejercicios de X" (>=3 en la semana)
      - "menos ejercicios de X" (<=2 en la semana)
      - "no repetir X dos días seguidos" / "no X en días consecutivos"
      - "meter|incluir|hacer X N veces" (exactamente N días con X)
      - "no repetir ejercicios (exactos)"
      - "máximo N ejercicios por sesión/día"
      - "incluir calentamiento de N min (cada día)"
      - "añadir estiramientos"
      - "mínimo M min de cardio N días"
      - "no máquinas / solo peso libre / no poleas / no smith / no barras / no mancuernas"
    """
    if not comentarios or not str(comentarios).strip():
        return []
    errs: list[str] = []
    txt = _norm(comentarios)
    import re as _re

    # Total days exact
    m = _re.search(r"solo\\s+(\\d+)\\s*d[ií]as(?:\\s+por\\s+semana)?", txt)
    if m:
        n = int(m.group(1))
        total_days = len(plan.get("dias", []))
        if total_days != n:
            errs.append(f"El plan debe tener exactamente {n} día(s) totales, pero tiene {total_days}.")

    # Exact legs days
    m = _re.search(r"solo\\s+(\\d+)\\s*d[ií]a[s]?\\s+de\\s+(pierna|piernas|lower|inferior)", txt)
    if m:
        n = int(m.group(1))
        current = _count_days_for_group(plan, "pierna")
        if current != n:
            errs.append(f"El plan debe tener exactamente {n} día(s) de pierna, pero tiene {current}.")

    # More exercises of X
    m = _re.search(r"m[aá]s\\s+ejercicios\\s+de\\s+([a-záéíóúñ]+)", txt)
    if m:
        g = m.group(1)
        cnt = _count_exercises_for_group(plan, g)
        if cnt < 3:
            errs.append(f"Incluir más ejercicios de {g}: hay {cnt}, se requieren ≥3 en la semana.")

    # Fewer exercises of X
    m = _re.search(r"menos\\s+ejercicios\\s+de\\s+([a-záéíóúñ]+)", txt)
    if m:
        g = m.group(1)
        cnt = _count_exercises_for_group(plan, g)
        if cnt > 2:
            errs.append(f"Reducir ejercicios de {g}: hay {cnt}, máximo 2 en la semana.")

    # No consecutive days with X
    m = _re.search(r"(?:no\\s+repetir\\s+|no\\s+)([a-záéíóúñ]+)\\s+(?:dos|2)\\s+d[ií]as\\s+seguidos", txt)
    if not m:
        m = _re.search(r"no\\s+([a-záéíóúñ]+)\\s+en\\s+d[ií]as\\s+consecutivos", txt)
    if m:
        g = m.group(1)
        dias = plan.get("dias", [])
        for i in range(len(dias)-1):
            if _day_has_group(dias[i], g) and _day_has_group(dias[i+1], g):
                errs.append(f"No repetir {g} en días consecutivos: aparece en los días {i+1} y {i+2}.")
                break

    # Exactly N times X in the week (days)
    m = _re.search(r"(?:meter|incluir|hacer)\\s+([a-záéíóúñ]+)\\s+(\\d+)\\s+veces", txt)
    if m:
        g = m.group(1)
        n = int(m.group(2))
        c = _count_days_for_group(plan, g)
        if c != n:
            errs.append(f"{g.capitalize()} debe aparecer exactamente {n} día(s) a la semana, pero aparece {c}.")

    # No repetir ejercicios exactos
    if _re.search(r"no\\s+repetir\\s+ejercicio[s]?(?:\\s+exacto[s]?)?\\s+en\\s+la\\s+semana|no\\s+repetir\\s+ejercicios", txt):
        seen = set()
        duplicates = set()
        for d in plan.get("dias", []):
            for ej in d.get("ejercicios", []):
                n = _norm(ej.get("nombre",""))
                if not n:
                    continue
                if n in seen:
                    duplicates.add(n)
                else:
                    seen.add(n)
        if duplicates:
            errs.append("No repetir ejercicios exactos en la semana. Repetidos: " + ", ".join(sorted(duplicates)[:10]))

    # Máximo N ejercicios por sesión/día
    m = _re.search(r"(?:máximo|max|como\\s+mucho)\\s+(\\d+)\\s+ejercicios\\s+por\\s+(?:sesión|sesion|d[ií]a|dia)", txt)
    if m:
        limit = int(m.group(1))
        for i, d in enumerate(plan.get("dias", []), start=1):
            cnt = len(d.get("ejercicios", []))
            if cnt > limit:
                errs.append(f"Máximo {limit} ejercicios por sesión: el día {i} tiene {cnt}.")

    # Incluir calentamiento de N min (cada día)
    m = _re.search(r"(?:incluir|añadir|meter)\\s+calentamiento\\s+de\\s+(\\d+)\\s*(?:min|mins|minutos)(?:\\s+cada\\s+d[ií]a)?", txt)
    if m:
        need = int(m.group(1))
        for i, d in enumerate(plan.get("dias", []), start=1):
            found = False
            for ej in d.get("ejercicios", []):
                if "calentamiento" in _norm(ej.get("nombre","")):
                    mins = _exercise_minutes(ej)
                    if mins is None or mins < need:
                        errs.append(f"Calentamiento de {need} min requerido en día {i}.")
                    found = True
                    break
            if not found:
                errs.append(f"Incluir calentamiento de {need} min en el día {i}.")

    # Añadir estiramientos
    if _re.search(r"(?:incluir|añadir|meter)\\s+estiramientos", txt):
        for i, d in enumerate(plan.get("dias", []), start=1):
            ok = any("estir" in _norm(ej.get("nombre","")) for ej in d.get("ejercicios", []))
            if not ok:
                errs.append(f"Incluir estiramientos al final del día {i}.")

    # Cardio: mínimo M minutos N días
    m = _re.search(r"m[ií]nimo\\s+(\\d+)\\s*(?:min|mins|’|')\\s+de\\s+cardio\\s+(\\d+)\\s+d[ií]as?", txt)
    if m:
        mins = int(m.group(1))
        days = int(m.group(2))
        ok_days = 0
        for d in plan.get("dias", []):
            if _day_has_cardio_minutes(d, mins):
                ok_days += 1
        if ok_days < days:
            errs.append(f"Cardio de al menos {mins} min en {days} días: detectados {ok_days}. Añadir bloques explícitos con duración.")

    # Restricciones de material
    if _re.search(r"no\\s+m[aá]quinas|s[oó]lo\\s+peso\\s+libre|solo\\s+peso\\s+libre|no\\s+poleas|no\\s+smith|no\\s+barras|no\\s+mancuernas", txt):
        no_machines = _re.search(r"no\\s+m[aá]quinas|s[oó]lo\\s+peso\\s+libre|solo\\s+peso\\s+libre", txt) is not None
        no_poleas = _re.search(r"no\\s+poleas", txt) is not None
        no_smith = _re.search(r"no\\s+smith", txt) is not None
        no_bar = _re.search(r"no\\s+barras", txt) is not None
        no_db = _re.search(r"no\\s+mancuernas", txt) is not None

        for i, d in enumerate(plan.get("dias", []), start=1):
            for ej in d.get("ejercicios", []):
                name = _norm(ej.get("nombre",""))
                if no_machines and _exercise_uses_any(ej, MACHINE_KEYWORDS + ["cable","polea","smith"]):
                    errs.append(f"Sin máquinas/poleas/smith: '{ej.get('nombre','')}' en día {i}. Sustituir por peso libre.")
                if no_poleas and ("polea" in name or "cable" in name):
                    errs.append(f"Sin poleas/cables: '{ej.get('nombre','')}' en día {i}.")
                if no_smith and "smith" in name:
                    errs.append(f"Sin Smith: '{ej.get('nombre','')}' en día {i}.")
                if no_bar and any(k in name for k in BARBELL_KEYWORDS):
                    errs.append(f"Sin barra: '{ej.get('nombre','')}' en día {i}.")
                if no_db and any(k in name for k in DUMBBELL_KEYWORDS):
                    errs.append(f"Sin mancuernas: '{ej.get('nombre','')}' en día {i}.")

    

# Regla: "solo un día de pierna"
if _re.search(r"solo\s+un\s+d[íi]a\s+de\s+pierna", txt):
    leg_terms = ("pierna", "glúteo", "gluteo", "cuádriceps", "cuadriceps", "isquio", "femoral", "glutes", "legs")
    leg_days = 0
    for d in plan.get("dias", []):
        gp = _norm(d.get("grupo_principal", ""))
        if any(t in gp for t in leg_terms):
            leg_days += 1
            continue
        ej = d.get("ejercicios", [])
        if ej:
            leg_like = 0
            for e in ej:
                name = _norm(e.get("nombre",""))
                if any(t in name for t in leg_terms):
                    leg_like += 1
            if leg_like >= max(1, round(len(ej) * 0.5)):
                leg_days += 1
    if leg_days > 1:
        errs.append(f"Pediste 'solo un día de pierna' y hay {leg_days} días de pierna detectados.")




# Regla dinámica: "al menos N de bíceps" / "mínimo N bíceps" / "quiero más bíceps"
min_bi = None
m = _re.search(r"(?:al\s+menos|min[ií]mo|como\s+min[ií]mo)\s*(\d+)\s*(?:ejercicios?\s+)?de\s+b[ií]ceps", txt)
if m:
    try:
        min_bi = int(m.group(1))
    except Exception:
        min_bi = None
if _re.search(r"(m[aá]s\s+ejercicios\s+de\s+b[ií]ceps|quiero\s+m[aá]s\s+b[ií]ceps|m[aá]s\s+b[ií]ceps)", txt) or min_bi is not None:
    if min_bi is None:
        min_bi = 3
    bi_terms = ("bíceps", "biceps", "curl", "predicador", "martillo", "hammer curl", "inclinado con mancuernas")
    total_bi = 0
    for d in plan.get("dias", []):
        for e in d.get("ejercicios", []):
            name = _norm(e.get("nombre",""))
            gp = _norm(e.get("musculo_principal","")) or _norm(e.get("grupo",""))
            sp = _norm(e.get("musculo_secundario",""))
            if "biceps" in name or "bíceps" in name or "bicep" in name or "bícep" in name:
                total_bi += 1
            elif any(t in name for t in bi_terms):
                total_bi += 1
            elif "biceps" in gp or "bíceps" in gp or "biceps" in sp or "bíceps" in sp:
                total_bi += 1
    if total_bi < min_bi:
        errs.append(f"Pediste bíceps ≥ {min_bi} y solo se detectan {total_bi} ejercicios de bíceps en la semana.")
return errs


MAX_REFINE = 2

def call_gpt(datos: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    _system = build_system()
    _prompt = build_prompt(datos)
    raw = _chat(client, _prompt)

    # Primer intento de parseo
    try:
        data = _try_parse_json(raw)
    except Exception as e:
        return {"ok": False, "error": f"JSON no válido: {e}", "raw": raw}

    # Validación de negocio
    coerced = _coerce_to_schema(data, datos)
    coerced = _sanitize_plan_reps(coerced)
    errs = validar_negocio(coerced)
    try:
        errs += validar_comentarios(coerced, datos.get("comentarios",""))
    except Exception:
        pass
    if not errs:
        return {"ok": True, "data": coerced, "prompt": _prompt, "system": _system}

    # Intento de REFINADO: devolver al modelo el JSON + errores para que lo corrija
    fix_prompt = f"""
Corrige el siguiente JSON de rutina para cumplir las reglas. Devuelve solo JSON válido.
ERRORES:
{json.dumps(errs, ensure_ascii=False, indent=2)}
JSON ORIGINAL:
{json.dumps(data, ensure_ascii=False)}
"""
    fixed_raw = _chat(client, fix_prompt)

    try:
        fixed = _try_parse_json(fixed_raw)
    except Exception as e:
        return {"ok": False, "error": f"Refinado fallido: JSON no válido ({e})", "raw": fixed_raw, "prompt": _prompt, "system": _system}

    errs2 = validar_negocio(fixed)
    if errs2:
        return {"ok": False, "error": f"Refinado aún con errores: {errs2}", "raw": fixed, "prompt": _prompt, "system": _system}

    return {"ok": True, "data": coerced, "prompt": _prompt, "system": _system}


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
