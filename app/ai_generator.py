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
{("Notas del usuario: " + notas) if notas else ""}
""".strip("\n")

    prompt = f"""\n=== PARAMS ===\nnivel={nivel} | dias={dias} | objetivo={objetivo} | duracion_min={duracion_min} | material={material}\nsexo={sexo} | edad={edad} | peso={peso} | altura={altura} | lesiones={lesiones}\nexperiencia={experiencia} | tiempo_disponible={tiempo_disponible}\n=== /PARAMS ===\n\n
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

def call_gpt(datos: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    raw = _chat(client, build_prompt(datos))

    # Primer intento de parseo
    try:
        data = _try_parse_json(raw)
    except Exception as e:
        return {"ok": False, "prompt_used": (locals().get("prompt") if "prompt" in locals() else None), "system_prompt": build_system(), "error": f"JSON no válido: {e}", "raw": raw}

    # Validación de negocio
    coerced = _coerce_to_schema(data, datos)
    coerced = _sanitize_plan_reps(coerced)
    errs = validar_negocio(coerced)
    if not errs:
        return {"ok": True, "data": coerced, "prompt_used": prompt, "system_prompt": build_system()}

    # Intento de REFINADO: devolver al modelo el JSON + errores para que lo corrija
    fix_prompt = f"""\n=== PARAMS ===\nnivel={nivel} | dias={dias} | objetivo={objetivo} | duracion_min={duracion_min} | material={material}\nsexo={sexo} | edad={edad} | peso={peso} | altura={altura} | lesiones={lesiones}\nexperiencia={experiencia} | tiempo_disponible={tiempo_disponible}\n=== /PARAMS ===\n\n
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
        return {"ok": False, "prompt_used": (locals().get("prompt") if "prompt" in locals() else None), "system_prompt": build_system(), "error": f"Refinado fallido: JSON no válido ({e})", "raw": fixed_raw}

    errs2 = validar_negocio(fixed)
    if errs2:
        return {"ok": False, "prompt_used": (locals().get("prompt") if "prompt" in locals() else None), "system_prompt": build_system(), "error": f"Refinado aún con errores: {errs2}", "raw": fixed}

    return {"ok": True, "data": coerced, "prompt_used": prompt, "system_prompt": build_system()}


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
