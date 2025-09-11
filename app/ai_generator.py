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
    return (

def _compile_user_conditions(notas: str) -> dict:
    """
    Convierte comentarios del usuario en reglas accionables:
    - MUST: requisitos obligatorios (p. ej., "siempre incluir gemelos 2x/semana")
    - NEVER: prohibiciones (p. ej., "evitar peso muerto", "sin press militar")
    - LIMITS: límites cuantitativos (p. ej., "máximo: 18 series por sesión")
    """
    import re as _re
    must, never, limits = [], [], {}
    if not notas:
        return {"MUST": must, "NEVER": never, "LIMITS": limits}
    lines = [l.strip("-•* ").strip() for l in notas.splitlines() if l.strip()]
    for l in lines:
        low = l.lower()
        if any(t in low for t in ["no hacer", "evitar", "prohib", "sin "]):
            never.append(l)
        elif any(t in low for t in ["siempre", "oblig", "incluir", "asegúrate"]):
            must.append(l)
        m = _re.search(r"(máx(?:imo)?|min(?:imo)?)\s*:\s*(\d+)", low)
        if m:
            limits[m.group(1)] = int(m.group(2))
    return {"MUST": must, "NEVER": never, "LIMITS": limits}

        "Eres un entrenador personal experto. Prioridades, en orden estricto: "
        "1) REGLAS ESTRICTAS y CONDICIONES_USUARIO (MUST/NEVER). "
        "2) Preferencias del usuario (nice-to-have). "
        "Si hay conflicto, prioriza 1 sobre 2 y ajusta volumen/selección para seguir cumpliendo. "
        "Responde EXCLUSIVAMENTE con JSON válido, sin explicaciones ni texto extra."
    )

def build_prompt(datos: Dict[str, Any]) -> str:
    """Construye el prompt para la IA respetando reglas y preferencias del usuario."""
    agrup = datos.get("agrupacion", "Varios grupos principales por día")
    material = datos.get("material", [])
    notas = datos.get("comentarios", "")
    objetivo = datos.get("objetivo", "mixto")
    nivel = datos.get("nivel", "intermedio")

    schema_hint = """
ESQUEMA_SALIDA (obligatorio):
{
  "meta": { "nivel": "principiante|intermedio|avanzado", "dias": 1-6, "duracion_min": 30-120, "objetivo": "fuerza|hipertrofia|resistencia|mixto" },
  "progresion": { "principales": "string", "accesorios": "string", "deload_semana": 4-8 },
  "dias": [
    { "nombre": "string",
      "ejercicios": [
        { "nombre": "string", "series": 2-6, "reps": "5|6-8|8-10|10-12", "descanso": "45-180s", "intensidad": "RPE 6-9|%1RM 60-85" }
      ]
    }
  ],
  "verificacion": { "cumple_must": true, "cumple_never": true, "duracion_ok": true }
}
No incluyas texto fuera del JSON.
"""

    fewshot = """
EJEMPLO — Comentario 'evitar peso muerto' y 'incluir gemelos 2x/semana':
ENTRADA: nivel=intermedio, dias=3, objetivo=mixto, material=["todo"]
COMENTARIOS:
- Evitar peso muerto
- Siempre incluir gemelos 2x/semana
SALIDA (esqueleto, sin texto extra):
{
  "meta": {"nivel":"intermedio","dias":3,"duracion_min":60,"objetivo":"mixto"},
  "progresion": {"principales":"sube reps o carga semanal","accesorios":"añade reps","deload_semana":6},
  "dias": [
    {"nombre":"Lower A (cuádriceps)","ejercicios":[
      {"nombre":"Sentadilla trasera","series":4,"reps":"4-6","descanso":"120-180s"},
      {"nombre":"Prensa","series":3,"reps":"8-10","descanso":"90-120s"},
      {"nombre":"Elevación de talones en máquina","series":3,"reps":"10-12","descanso":"60-90s"}
    ]},
    {"nombre":"Upper (empuje/tirón balanceado)","ejercicios":[{"nombre":"Press banca","series":4,"reps":"6-8","descanso":"120s"}]},
    {"nombre":"Lower B (bisagra sin peso muerto)","ejercicios":[
      {"nombre":"Hip thrust","series":4,"reps":"6-8","descanso":"120s"},
      {"nombre":"Curl femoral tumbado","series":3,"reps":"10-12","descanso":"60-90s"},
      {"nombre":"Elevación de talones de pie","series":3,"reps":"10-12","descanso":"60-90s"}
    ]}
  ],
  "verificacion":{"cumple_must":true,"cumple_never":true,"duracion_ok":true}
}
"""

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
{("Notas del usuario: " + notas) if notas else ""}
""".strip("\n")

    # Compila comentarios en reglas MUST/NEVER/LIMITS
    conds = _compile_user_conditions(notas)
    cond_block = f"""
CONDICIONES_USUARIO — ESTRICTAS:
- MUST (obligatorio): {conds['MUST'] or '[]'}
- NEVER (prohibido): {conds['NEVER'] or '[]'}
- LIMITS: {conds['LIMITS'] or '{}'}
Si alguna NEVER choca con otros requisitos, reemplaza por alternativa equivalente y mantén la prohibición.
"""


    prompt = f"""
Eres un entrenador personal experto. Devuelve exclusivamente JSON válido, sin texto adicional.

Genera una rutina semanal siguiendo estas reglas base:
{RULES_TEXT.format(dur=datos.get('duracion', 60))}

{reglas_estrictas}
{cond_block}
{schema_hint}
{fewshot}


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

Antes de responder, verifica internamente que las NEVER están ausentes, los MUST se cumplen y la duración total ≈ duracion_min; ajusta volumen/descansos si no.
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

def call_gpt(datos: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    raw = _chat(client, build_prompt(datos))

    # Primer intento de parseo
    try:
        data = _try_parse_json(raw)
    except Exception as e:
        return {"ok": False, "error": f"JSON no válido: {e}", "raw": raw}

    # Validación de negocio
    coerced = _coerce_to_schema(data, datos)
    errs = validar_negocio(coerced)
    if not errs:
        return {"ok": True, "data": coerced}

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
        return {"ok": False, "error": f"Refinado fallido: JSON no válido ({e})", "raw": fixed_raw}

    errs2 = validar_negocio(fixed)
    if errs2:
        return {"ok": False, "error": f"Refinado aún con errores: {errs2}", "raw": fixed}

    return {"ok": True, "data": coerced}
