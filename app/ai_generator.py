import json

# --- NUEVO: extracción de constraints desde comentarios (cumplimiento 100%) ---
import re as _re

def extract_constraints(comentarios_txt: str):
    """
    Devuelve un dict con constraints normalizados que el modelo debe cumplir 100%.
    Ejemplos detectados:
    - "solo un día de pierna"
    - "al menos 4 ejercicios de bíceps" / "mínimo N de bíceps" / "más bíceps" (por defecto 3)
    - "máximo 6 ejercicios por día"
    - "solo peso libre" / "no máquinas / no smith / no poleas"
    - "no superseries" / "no clusters" / "no al fallo"
    - "cardio al menos 20 min 3 días"
    - "split: pecho-tríceps, espalda-bíceps, pierna-glúteo, core/cardio"
    """
    def _norm(s): return (s or "").strip().lower()
    txt = _norm(comentarios_txt)
    C = {"raw": comentarios_txt or ""}

    # Pierna: solo un día
    if _re.search(r"solo\s+un\s+d[íi]a\s+de\s+pierna", txt):
        C["legs_days_max"] = 1

    # Bíceps: mínimo N o "más bíceps" (fallback 3)
    m = _re.search(r"(?:al\s+menos|min[ií]mo|como\s+min[ií]mo)\s*(\d+)\s*(?:ejercicios?\s+)?de\s+b[ií]ceps", txt)
    if m:
        C["biceps_min_total"] = int(m.group(1))
    elif _re.search(r"(m[aá]s\s+ejercicios\s+de\s+b[ií]ceps|quiero\s+m[aá]s\s+b[ií]ceps|m[aá]s\s+b[ií]ceps)", txt):
        C["biceps_min_total"] = 3

    # Máximo ejercicios por día
    m = _re.search(r"max(?:imo)?\s*(\d+)\s*ejercicios?\s*por\s*d[ií]a", txt)
    if m:
        C["max_exercises_per_day"] = int(m.group(1))

    # Material
    if _re.search(r"solo\s+peso\s+libre", txt):
        C["equipment_only_free_weights"] = True
    if _re.search(r"no\s+m[aá]quinas", txt):
        C["forbid_machines"] = True
    if _re.search(r"no\s+smith", txt):
        C["forbid_smith"] = True
    if _re.search(r"no\s+poleas|no\s+cables?", txt):
        C["forbid_cables"] = True

    # Métodos
    if _re.search(r"no\s+superseries?", txt):
        C["forbid_supersets"] = True
    if _re.search(r"no\s+clusters?", txt):
        C["forbid_clusters"] = True
    if _re.search(r"no\s+(?:ir\s+a\s+fallo|fallar\s+series|al\s+fallo)", txt):
        C["forbid_failure"] = True

    # Cardio: "al menos 20 min 3 días"
    m = _re.search(r"cardio\s+(?:al\s+menos|min[ií]mo)\s*(\d+)\s*min(?:utos)?\s*(\d+)\s*d[ií]as", txt)
    if m:
        C["cardio_min_minutes"] = int(m.group(1))
        C["cardio_min_days"] = int(m.group(2))

    # Split clásico detectado (tolerante a guiones/espacios)
    if _re.search(r"pecho\s*[-/]\s*tr[íi]ceps", txt) or _re.search(r"espalda\s*[-/]\s*b[ií]ceps", txt) or _re.search(r"pierna\s*[-/]\s*gl[úu]teo", txt):
        C["preferred_split"] = "PT-EB-PG"

# --- Ampliación de comprensión de lenguaje natural ---
# Días por semana: "X días", "entreno 4 dias", "rutina de 3 días"
m = _re.search(r"(?:rutina|entreno|entrenamiento).{0,10}?(\d+)\s*d[ií]as", txt)
if m:
    C["days_per_week"] = int(m.group(1))

# Duración por sesión: "sesiones de 60 min", "no más de 75 minutos"
m = _re.search(r"(?:sesiones?|duraci[oó]n).{0,6}?(\d+)\s*min", txt)
if m:
    C["session_target_minutes"] = int(m.group(1))
m = _re.search(r"(?:no\s+m[aá]s\s+de|m[aá]ximo)\s*(\d+)\s*min", txt)
if m:
    C["session_max_minutes"] = int(m.group(1))
m = _re.search(r"(?:al\s+menos|min[ií]mo)\s*(\d+)\s*min", txt)
if m and "session_min_minutes" not in C:
    C["session_min_minutes"] = int(m.group(1))

# Descansos: "descansos de 60-90s", "descanso 90 s"
m = _re.search(r"descansos?\s+de\s*(\d+)\s*-\s*(\d+)\s*s", txt)
if m:
    C["rest_seconds_range"] = (int(m.group(1)), int(m.group(2)))
m = _re.search(r"descansos?\s+de\s*(\d+)\s*s", txt)
if m and "rest_seconds_range" not in C:
    C["rest_seconds_range"] = (int(m.group(1)), int(m.group(1)))

# Tempo: "tempo 3-1-1" (aplica como valor por defecto si no se especifica por ejercicio)
m = _re.search(r"tempo\s+(\d[\-\d]*)", txt)
if m:
    C["default_tempo"] = m.group(1)

# RIR/RPE globales: "RIR 2-3", "RPE 7-8"
m = _re.search(r"rir\s*(\d)\s*-\s*(\d)", txt)
if m:
    C["rir_range"] = (int(m.group(1)), int(m.group(2)))
m = _re.search(r"rpe\s*(\d)\s*-\s*(\d)", txt)
if m:
    C["rpe_range"] = (int(m.group(1)), int(m.group(2)))

# Progresión: "progresión lineal", "doble progresión", "ondulante", "5/3/1"
if "progresi" in txt:
    if _re.search(r"lineal", txt):
        C["progression"] = "lineal"
    elif _re.search(r"doble", txt):
        C["progression"] = "doble"
    elif _re.search(r"ondulante|undulating|dup", txt):
        C["progression"] = "ondulante"
    elif _re.search(r"5\s*/\s*3\s*/\s*1", txt):
        C["progression"] = "531"

# Splits comunes
if _re.search(r"push\s*[-/]\s*pull\s*[-/]\s*legs|ppl", txt):
    C["preferred_split"] = "PPL"
if _re.search(r"upper\s*[-/]\s*lower|torso\s*[-/]\s*pierna", txt):
    C["preferred_split"] = "UL"
if _re.search(r"full\s*body|cuerpo\s*entero", txt):
    C["preferred_split"] = "FB"

# Incluir calentamiento / movilidad / core
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

# Cardio con tipo: LISS/HIIT
if _re.search(r"hiit", txt):
    C["cardio_type"] = "HIIT"
if _re.search(r"liss|suave|zona\s*2", txt):
    C["cardio_type"] = "LISS"

# Preferencia de equipo: solo mancuernas / solo barra / domicilio
if _re.search(r"solo\s+mancuernas?", txt):
    C["equipment_only_dumbbells"] = True
if _re.search(r"solo\s+barra", txt):
    C["equipment_only_barbell"] = True
if _re.search(r"(en\s+casa|domicilio|home)\s+(sin\s+)?m[aá]quinas?", txt):
    C["home_gym_minimal"] = True

# Evitar ejercicios concretos: "no sentadilla", "evitar peso muerto"
avoid = []
for m in _re.finditer(r"(?:no|evitar)\s+([a-záéíóúüñ\s]+?)(?:,|\.|;|$)", txt):
    ex = m.group(1).strip()
    if ex and len(ex) < 40:
        avoid.append(ex)
if avoid:
    C["avoid_exercises"] = list(set(avoid))

# Días nominales: "entreno lunes, miércoles y viernes"
days_map = {"lunes":"mon","martes":"tue","miercoles":"wed","miércoles":"wed","jueves":"thu","viernes":"fri","sabado":"sat","sábado":"sat","domingo":"sun"}
chosen = []
for k in days_map.keys():
    if _re.search(rf"\\b{k}\\b", txt):
        chosen.append(days_map[k])
if chosen:
    C["weekdays"] = sorted(list(set(chosen)))

# Series/volumen por grupo: "bíceps 10-14 series", "pecho al menos 12 series", "hombros máximo 9 series"
vol = {}
for mm in _re.finditer(r"([a-záéíóúüñ]+)\s+(\d+)(?:\s*-\s*(\d+))?\s*series", txt):
    mus = mm.group(1).strip()
    lo = int(mm.group(2)) if mm.group(2) else None
    hi = int(mm.group(3)) if mm.group(3) else None
    vol[mus] = (lo,hi)
for mm in _re.finditer(r"([a-záéíóúüñ]+)\s+al\s+menos\s+(\d+)\s*series", txt):
    mus = mm.group(1).strip(); lo=int(mm.group(2)); vol[mus]=(lo,None)
for mm in _re.finditer(r"([a-záéíóúüñ]+)\s+m[aá]ximo\s+(\d+)\s*series", txt):
    mus = mm.group(1).strip(); hi=int(mm.group(2)); vol[mus]=(None,hi)
if vol: C["volumen_series"]=vol

# Orden ejercicios: bilaterales primero, básicos antes accesorios
if _re.search(r"bilateral(es)?\s+primero", txt):
    C.setdefault("order_rules",{})["bilateral_first"]=True
if _re.search(r"b[aá]sicos?\s+antes\s+que\s+accesorios", txt):
    C.setdefault("order_rules",{})["basics_first"]=True

# Series/reps objetivo global: "3-4 series de 8-10 repeticiones"
m = _re.search(r"(\d+)\s*-\s*(\d+)\s*series.*?(\d+)\s*-\s*(\d+)\s*rep", txt)
if m:
    C["default_series_reps"]={"series":(int(m.group(1)),int(m.group(2))),"reps":(int(m.group(3)),int(m.group(4)))}
m = _re.search(r"(?:hipertrofia|fuerza).*?(\d+)\s*-\s*(\d+)\s*rep", txt)
if m:
    C.setdefault("default_series_reps",{})["reps"]=(int(m.group(1)),int(m.group(2)))

# Volumen por grupo (series/semana): "bíceps 10–14 series", "pecho al menos 12 series", "hombros máximo 9 series"
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
# patrones: "<grupo> 10-14 series", "<grupo> al menos 12 series", "<grupo> maximo 9 series"
for g, aliases in grupos.items():
    for alias in aliases:
        # rango
        m = _re.search(rf"\\b{alias}\\b\\s*(\\d+)\\s*[-–]\\s*(\\d+)\\s*series", txt)
        if m:
            vol[g] = (int(m.group(1)), int(m.group(2)))
        # minimo
        m = _re.search(rf"\\b{alias}\\b.*?(?:al\\s+menos|min[ií]mo|como\\s+min[ií]mo)\\s*(\\d+)\\s*series", txt)
        if m:
            lo = int(m.group(1)); hi = vol.get(g, (None,None))[1]
            vol[g] = (lo, hi)
        # maximo
        m = _re.search(rf"\\b{alias}\\b.*?(?:m[aá]ximo|no\\s+m[aá]s\\s+de)\\s*(\\d+)\\s*series", txt)
        if m:
            hi = int(m.group(1)); lo = vol.get(g, (None,None))[0]
            vol[g] = (lo, hi)
if vol:
    C["volumen_series"] = vol

# Orden de ejercicios
if _re.search(r"bilaterales?\\s+primero", txt):
    C.setdefault("order_rules", {})["bilateral_first"] = True
if _re.search(r"(b[aá]sicos|compuestos)\\s+antes\\s+que\\s+(accesorios|aislados?)", txt):
    C.setdefault("order_rules", {})["basics_first"] = True

# Series/Reps globales por defecto: "3-4 series de 8-10 repeticiones", "fuerza: 4-6 reps"
m = _re.search(r"(\\d+)\\s*[-–]\\s*(\\d+)\\s*series.*?(\\d+)\\s*[-–]\\s*(\\d+)\\s*(rep|reps|repeticiones)", txt)
if m:
    C["default_series_reps"] = {"series": (int(m.group(1)), int(m.group(2))), "reps": (int(m.group(3)), int(m.group(4)))}
else:
    # solo reps
    m = _re.search(r"(?:fuerza|hipertrofia|resistencia)?.*?(\\d+)\\s*[-–]\\s*(\\d+)\\s*(rep|reps|repeticiones)", txt)
    if m:
        C["default_series_reps"] = {"reps": (int(m.group(1)), int(m.group(2)))}
    m = _re.search(r"(?:series)\\s*(\\d+)\\s*[-–]\\s*(\\d+)", txt)
    if m:
        dsr = C.get("default_series_reps", {})
        dsr["series"] = (int(m.group(1)), int(m.group(2)))
        C["default_series_reps"] = dsr







    return C


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


# --- NUEVO: validador de constraints estructurados ---
def validar_constraints(plan, C):
    errs = []
    if not isinstance(C, dict):

# Días por semana exactos
if C.get("days_per_week") is not None:
    n = len(plan.get("dias", []))
    if n != int(C["days_per_week"]):
        errs.append(f"Se solicitaron {C['days_per_week']} días/semana y la rutina tiene {n}.")

# Duración objetivo/máx/mín por sesión (si el plan provee 'duracion_min_dia' o suma de 'minutos')
for i, d in enumerate(plan.get("dias", []), start=1):
    dur = d.get("duracion_min_dia")
    if dur is None:
        # estimar via ejercicios (minutos o duracion_min)
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

# Descansos entre series
if C.get("rest_seconds_range"):
    lo, hi = C["rest_seconds_range"]
    for i, d in enumerate(plan.get("dias", []), start=1):
        for e in d.get("ejercicios", []):
            rest = e.get("descanso_s") or e.get("descanso") or None
            try:
                rest = int(str(rest).replace("s","").strip()) if rest is not None else None
            except Exception:
                rest = None
            if rest is not None and not (lo <= rest <= hi):
                errs.append(f"Descanso fuera de rango en día {i}, '{e.get('nombre','')}' ({rest}s no está en {lo}-{hi}s).")

# Tempo por defecto: exigir que exista si se definió
if C.get("default_tempo"):
    for i, d in enumerate(plan.get("dias", []), start=1):
        for e in d.get("ejercicios", []):
            tempo = (e.get("tempo") or "").strip()
            if not tempo:
                errs.append(f"Falta tempo en día {i}, ejercicio '{e.get('nombre','')}' (se pidió default {C['default_tempo']}).")

# RIR/RPE rango global (si los ejercicios lo incluyen)
if C.get("rir_range"):
    lo, hi = C["rir_range"]
    for i, d in enumerate(plan.get("dias", []), start=1):
        for e in d.get("ejercicios", []):
            rir = str(e.get("rir","")).strip().lower()
            if rir and rir not in ("fallo","-1","0"):
                try:
                    val = int(re.sub(r"[^0-9-]", "", rir))
                    if not (lo <= val <= hi):
                        errs.append(f"RIR {rir} fuera de rango {lo}-{hi} en día {i}, '{e.get('nombre','')}'.")
                except Exception:
                    pass
if C.get("rpe_range"):
    lo, hi = C["rpe_range"]
    for i, d in enumerate(plan.get("dias", []), start=1):
        for e in d.get("ejercicios", []):
            rpe = e.get("rpe")
            try:
                if rpe is not None:
                    val = float(rpe)
                    if not (lo <= val <= hi):
                        errs.append(f"RPE {rpe} fuera de rango {lo}-{hi} en día {i}, '{e.get('nombre','')}'.")
            except Exception:
                pass

# Split preferido: solo verificaciones básicas
if C.get("preferred_split") in ("PPL","UL","FB"):
    # Contaje de días con grupos característicos
    def _norm(s): return (s or "").strip().lower()
    if C["preferred_split"] == "PPL":
        # Debe existir al menos un día 'empuje', uno 'tirón', uno 'pierna'
        cats = {"push":0,"pull":0,"legs":0}
        push_terms = ("pecho","hombro","tríceps","triceps","empuje","press")
        pull_terms = ("espalda","bíceps","biceps","remo","jalón","tirón")
        leg_terms = ("pierna","glúteo","gluteo","cuádriceps","isquio","femoral","sentadilla","zancada","peso muerto")
        for d in plan.get("dias", []):
            names = " ".join([_norm(e.get("nombre","")) for e in d.get("ejercicios", [])])
            gp = _norm(d.get("grupo_principal",""))
            if any(t in gp or t in names for t in push_terms): cats["push"] += 1
            if any(t in gp or t in names for t in pull_terms): cats["pull"] += 1
            if any(t in gp or t in names for t in leg_terms): cats["legs"] += 1
        for k,v in cats.items():
            if v == 0:
                errs.append(f"Split PPL solicitado, pero falta día de {k}.")
    elif C["preferred_split"] == "UL":
        # Debe existir al menos un día upper y uno lower
        up_terms = ("pecho","hombro","espalda","bíceps","tríceps","biceps","triceps")
        lo_terms = ("pierna","glúteo","gluteo","cuádriceps","isquio","femoral")
        has_up = has_lo = False
        for d in plan.get("dias", []):
            gp = _norm(d.get("grupo_principal",""))
            if any(t in gp for t in up_terms): has_up = True
            if any(t in gp for t in lo_terms): has_lo = True
        if not has_up: errs.append("Split UL solicitado: falta día de torso.")
        if not has_lo: errs.append("Split UL solicitado: falta día de pierna.")
    elif C["preferred_split"] == "FB":
        # Mínimo 2 días con mezcla multi-grupo
        mixed = 0
        for d in plan.get("dias", []):
            gps = set()
            for e in d.get("ejercicios", []):
                gps.add(_norm(e.get("musculo_principal","")) or _norm(e.get("grupo","")))
            if len([g for g in gps if g]) >= 3:
                mixed += 1
        if mixed < 2:
            errs.append("Full Body solicitado: se esperaban ≥2 días con 3+ grupos diferentes.")

# Inclusiones
if C.get("include_warmup"):
    has = False
    for d in plan.get("dias", []):
        for e in d.get("ejercicios", []):
            name = (e.get("nombre","") or "").lower()
            if any(t in name for t in ("calentamiento","activación","activacion","movilidad")):
                has = True; break
    if not has:
        errs.append("Se pidió incluir calentamiento y no se detecta.")
if C.get("warmup_minutes"):
    need = int(C["warmup_minutes"])
    has_min = False
    for d in plan.get("dias", []):
        for e in d.get("ejercicios", []):
            name = (e.get("nombre","") or "").lower()
            if "calentamiento" in name:
                try:
                    mins = int(e.get("minutos", e.get("duracion_min", 0)) or 0)
                    if mins >= need: has_min = True
                except Exception:
                    pass
    if not has_min:
        errs.append(f"Calentamiento de ≥{need} min solicitado y no se cumple.")

if C.get("include_mobility"):
    has = False
    for d in plan.get("dias", []):
        for e in d.get("ejercicios", []):
            name = (e.get("nombre","") or "").lower()
            if "movilidad" in name:
                has = True; break
    if not has:
        errs.append("Se pidió incluir movilidad y no se detecta.")

if C.get("include_core"):
    has = False
    for d in plan.get("dias", []):
        for e in d.get("ejercicios", []):
            name = (e.get("nombre","") or "").lower()
            if any(t in name for t in ("plancha","abdominal","core","hollow","dead bug","pallof")):
                has = True; break
    if not has:
        errs.append("Se pidió incluir core/abdominales y no se detecta.")
if C.get("core_days_min"):
    need = int(C["core_days_min"]); got = 0
    for d in plan.get("dias", []):
        names = " ".join([ (e.get("nombre","") or "").lower() for e in d.get("ejercicios", []) ])
        if any(t in names for t in ("plancha","abdominal","core","hollow","dead bug","pallof")):
            got += 1
    if got < need:
        errs.append(f"Se pidieron {need} días con core y hay {got}.")

# Cardio tipo
if C.get("cardio_type"):
    typ = C["cardio_type"]
    if typ == "HIIT":
        found = any(any("hiit" in (e.get("nombre","") or "").lower() for e in d.get("ejercicios", [])) for d in plan.get("dias", []))
        if not found: errs.append("Se pidió cardio HIIT y no se detecta.")
    if typ == "LISS":
        # buscar caminata, bici suave, elíptica suave, z2
        found = False
        for d in plan.get("dias", []):
            for e in d.get("ejercicios", []):
                nm = (e.get("nombre","") or "").lower()
                if any(t in nm for t in ("liss","caminata","zona 2","z2","suave","bici","elíptica","eliptica","carrera suave")):
                    found = True; break
        if not found: errs.append("Se pidió cardio LISS/zona 2 y no se detecta.")

# Equipo preferido / home gym
if C.get("equipment_only_dumbbells") or C.get("equipment_only_barbell") or C.get("home_gym_minimal"):
    allowed = []
    if C.get("equipment_only_dumbbells"): allowed += ["mancuerna","mancuernas","dumbbell"]
    if C.get("equipment_only_barbell"): allowed += ["barra","barbell"]
    if C.get("home_gym_minimal"): allowed += ["mancuerna","mancuernas","barra","bandas","peso corporal","bodyweight"]
    for i, d in enumerate(plan.get("dias", []), start=1):
        for e in d.get("ejercicios", []):
            nm = (e.get("nombre","") or "").lower()
            if not any(a in nm for a in allowed):
                # permitir si es claramente peso corporal
                if not any(t in nm for t in ("flexiones","dominadas","sentadilla búlgara","bulgara","zancadas","planchas","hip thrust")):
                    errs.append(f"Ejercicio no acorde al equipo solicitado en día {i}: '{e.get('nombre','')}'.")

# Evitar ejercicios concretos
if C.get("avoid_exercises"):
    avoid = [a.strip().lower() for a in C["avoid_exercises"] if a.strip()]
    if avoid:
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                nm = (e.get("nombre","") or "").lower()
                if any(a in nm for a in avoid):
                    errs.append(f"Se pidió evitar '{a}' y aparece en día {i}: '{e.get('nombre','')}'.")
                    break

# Días nominales (solo verificar conteo si se dieron)
if C.get("weekdays"):
    if len(C["weekdays"]) != len(plan.get("dias", [])):
        errs.append(f"Se indicaron días específicos ({len(C['weekdays'])}) pero la rutina tiene {len(plan.get('dias',[]))}.")

# Volumen por grupo (sumar series por semana)
if C.get("volumen_series"):
    def _norm(s): return (s or "").strip().lower()
    grupos = {
        "pecho":["pecho","pectorales","pectoral","press banca","aperturas"],
        "espalda":["espalda","dorsal","remo","jalón","dominadas","pull down","pull-up","remo con barra","remo con mancuerna"],
        "hombro":["hombro","deltoide","militar","overhead","elevaciones laterales","elevaciones frontales"],
        "bíceps":["bíceps","biceps","curl","martillo","predicador","inclinado"],
        "tríceps":["tríceps","triceps","fondos","extensión tríceps","jalón tríceps","press cerrado"],
        "pierna":["pierna","sentadilla","zancada","prensa","peso muerto","cuádriceps","isquio","femoral","glúteo","gluteo","hip thrust"],
        "glúteo":["glúteo","gluteo","hip thrust","patada de glúteo"],
        "core":["core","abdominal","plancha","hollow","dead bug","pallof"],
        "gemelo":["gemelo","pantorrilla","calf"]
    }
    # Conteo de series por grupo
    series_por_grupo = {g:0 for g in C["volumen_series"].keys()}
    for d in plan.get("dias", []):
        for e in d.get("ejercicios", []):
            name = _norm(e.get("nombre",""))
            gp = _norm(e.get("musculo_principal","")) or _norm(e.get("grupo",""))
            s = e.get("series")
            try:
                s = int(str(s).strip()) if s is not None else None
            except Exception:
                s = None
            for g in series_por_grupo.keys():
                aliases = grupos.get(g, [g])
                if g in gp or any(a in name for a in aliases):
                    series_por_grupo[g] += (s or 0)
                    break
    # Validar rangos
    for g, (lo, hi) in C["volumen_series"].items():
        val = series_por_grupo.get(g, 0)
        if lo is not None and val < lo:
            errs.append(f"Volumen insuficiente para {g}: {val} series (< {lo}).")
        if hi is not None and val > hi:
            errs.append(f"Volumen excesivo para {g}: {val} series (> {hi}).")

# Orden de ejercicios: bilaterales primero, básicos antes que accesorios
if C.get("order_rules"):
    def is_unilateral(nm):
        nm = (nm or "").lower()
        return any(t in nm for t in ("unilateral","a una mano","a una pierna","alterno","alternas","búlgar","bulgara","zancada","split squat"))
    def is_basic(nm):
        nm = (nm or "").lower()
        basics = ("sentadilla","peso muerto","press banca","press militar","remo","dominadas","hip thrust","press inclinado","remo con barra","remo con mancuerna")
        return any(t in nm for t in basics)
    def is_accessory(nm):
        nm = (nm or "").lower()
        acc = ("curl","extensión tríceps","elevaciones","aperturas","cruces","pull over","face pull","patada tríceps","gemelo","pantorrilla")
        return any(t in nm for t in acc)

    for i, d in enumerate(plan.get("dias", []), start=1):
        names = [ (e.get("nombre","") or "") for e in d.get("ejercicios", []) ]
        # bilateral_first: no puede haber un bilateral después de que haya aparecido un unilateral
        if C["order_rules"].get("bilateral_first"):
            seen_unilateral = False
            for nm in names:
                if is_unilateral(nm):
                    seen_unilateral = True
                elif seen_unilateral:
                    errs.append(f"Orden incorrecto día {i}: ejercicio bilateral '{nm}' va después de un unilateral.")
                    break
        # basics_first: ningún accesorio antes que un básico
        if C["order_rules"].get("basics_first"):
            first_basic = None
            first_accessory = None
            for idx, nm in enumerate(names):
                if is_basic(nm) and first_basic is None:
                    first_basic = idx
                if is_accessory(nm) and first_accessory is None:
                    first_accessory = idx
            if first_accessory is not None and (first_basic is None or first_accessory < first_basic):
                errs.append(f"Orden incorrecto día {i}: hay accesorios antes que básicos.")
# Series/Reps por defecto: comprobar rangos si están presentes
if C.get("default_series_reps"):
    s_rng = C["default_series_reps"].get("series")
    r_rng = C["default_series_reps"].get("reps")
    def parse_reps(val):
        if val is None: return None, None
        txt = str(val).lower().strip()
        m = re.search(r"(\\d+)\\s*[-–x]\\s*(\\d+)", txt)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"(\\d+)", txt)
        if m:
            v = int(m.group(1)); return v, v
        return None, None
    for i, d in enumerate(plan.get("dias", []), start=1):
        for e in d.get("ejercicios", []):
            # series
            if s_rng:
                s = e.get("series")
                try:
                    s = int(str(s).strip()) if s is not None else None
                except Exception:
                    s = None
                if s is not None and not (s_rng[0] <= s <= s_rng[1]):
                    errs.append(f"Series fuera de rango ({s}) en día {i}: '{e.get('nombre','')}', esperado {s_rng[0]}–{s_rng[1]}.")
            # reps
            if r_rng:
                r_lo, r_hi = parse_reps(e.get("reps"))
                if r_lo is not None and not (r_rng[0] <= r_lo <= r_rng[1] and r_rng[0] <= r_hi <= r_rng[1]):
                    errs.append(f"Reps fuera de rango ({e.get('reps')}) en día {i}: '{e.get('nombre','')}', esperado {r_rng[0]}–{r_rng[1]}.")




        return errs
    def _norm(s): return (s or "").strip().lower()

    # legs_days_max
    if C.get("legs_days_max") is not None:
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
        if leg_days > int(C["legs_days_max"]):
            errs.append(f"Se pidió 'solo {C['legs_days_max']}' día(s) de pierna y se detectan {leg_days}.")

    # biceps_min_total
    if C.get("biceps_min_total") is not None:
        min_bi = int(C["biceps_min_total"])
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
            errs.append(f"Bíceps ≥ {min_bi} requerido y hay {total_bi}.")

    # max_exercises_per_day
    if C.get("max_exercises_per_day") is not None:
        mx = int(C["max_exercises_per_day"])
        for i, d in enumerate(plan.get("dias", []), start=1):
            n = len(d.get("ejercicios", []))
            if n > mx:
                errs.append(f"Día {i} supera el máximo de {mx} ejercicios ({n}).")

    # equipment forbids
    eq_forb = []
    if C.get("equipment_only_free_weights"): eq_forb += ["máquina","maquina","polea","cable","smith"]
    if C.get("forbid_machines"): eq_forb += ["máquina","maquina"]
    if C.get("forbid_smith"): eq_forb += ["smith"]
    if C.get("forbid_cables"): eq_forb += ["polea","cable"]
    if eq_forb:
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                name = _norm(e.get("nombre",""))
                if any(b in name for b in eq_forb):
                    errs.append(f"Material prohibido detectado en día {i}: '{e.get('nombre','')}'.")

    # methods forbids
    if C.get("forbid_supersets"):
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                if "super" in _norm(e.get("nombre","")):
                    errs.append(f"Se prohíben superseries y aparece '{e.get('nombre','')}' en día {i}.")
    if C.get("forbid_clusters"):
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                if "cluster" in _norm(e.get("nombre","")):
                    errs.append(f"Se prohíben clusters y aparece '{e.get('nombre','')}' en día {i}.")
    if C.get("forbid_failure"):
        for i, d in enumerate(plan.get("dias", []), start=1):
            for e in d.get("ejercicios", []):
                rir = str(e.get("rir","")).strip().lower()
                if rir in ("0","-1","fallo"):
                    errs.append(f"Se prohíbe ir al fallo y hay RIR {rir} en '{e.get('nombre','')}' día {i}.")

    # cardio
    if C.get("cardio_min_minutes") and C.get("cardio_min_days"):
        need_min = int(C["cardio_min_minutes"])
        need_days = int(C["cardio_min_days"])
        got_days = 0
        for d in plan.get("dias", []):
            minutes = 0
            for e in d.get("ejercicios", []):
                name = _norm(e.get("nombre",""))
                if "cardio" in name or "cinta" in name or "elíptica" in name or "eliptica" in name or "bicicleta" in name or "row" in name:
                    try:
                        minutes = max(minutes, int(e.get("minutos", e.get("duracion_min", 0)) or 0))
                    except Exception:
                        pass
            if minutes >= need_min:
                got_days += 1
        if got_days < need_days:
            errs.append(f"Cardio ≥ {need_min} min en {need_days} días requerido y solo hay {got_days}.")

    # preferred_split is advisory in prompt; we do not hard-fail unless strict keyword present
    return errs



# --- NUEVO: auto-ajuste simple antes de hard-fail ---
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
                    name=_norm(e.get("nombre",""))
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

