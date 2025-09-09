import os, json
from typing import Any, Dict
from openai import OpenAI
from .schema_rutina import validar_negocio

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
    return f"""
Genera una rutina semanal siguiendo estas reglas:
{RULES_TEXT.format(dur=datos.get('duracion', 60))} + f"""

REGLAS ESTRICTAS (debes cumplirlas sí o sí):
- Agrupación pedida: {datos.get("agrupacion","Varios grupos principales por día")}
- Si es "Un solo grupo principal por día":
  * EXACTAMENTE 1 grupo principal por día.
  * No mezclar dos grupos principales (por ejemplo, "pecho" y "espalda" juntos) en el mismo día.
  * Puedes añadir accesorios SUPEDITADOS a ese principal (ej.: bíceps en día de espalda), pero no contarlos como principales.
- Si es "Varios grupos principales por día":
  * Máximo 2 (como push/pull o torso/pierna) salvo que el usuario pida explícitamente 3.
  * Evitar solapar el mismo grupo dos días consecutivos si el volumen es alto.
- Material:
  * Si material incluye "todo": asume gimnasio comercial COMPLETO (barras, mancuernas, poleas, máquinas, rack, banco, discos, gomas, etc.).
  * Si es personalizado, usa SOLO el material listado.
- Respeta siempre los límites de lesiones/limitaciones.
- Ajusta volumen y selección de ejercicios al objetivo indicado.
{("\nNotas del usuario: " + datos.get("comentarios","")) if datos.get("comentarios") else ""}
"""


ENTRADA (datos del usuario, JSON):
{json.dumps(datos, ensure_ascii=False)}

SALIDA (solo JSON con este esquema mínimo):
{{
  "meta": {{
    "nivel": "principiante|intermedio|avanzado",
    "dias": int,
    "duracion_min": int,
    "objetivo": "fuerza|hipertrofia|resistencia|mixto"
  }},
  "dias": [
    {{
      "nombre": "Upper A | Lower A | FullBody | ...",
      "ejercicios": [
        {{"nombre":"", "series": 3, "reps": "6-8", "intensidad":"RPE 7-8 o 75-80%", "descanso":"90s|2-3m"}}
      ],
      "notas": ""
    }}
  ],
  "progresion": {{
    "principales": "regla",
    "accesorios": "regla",
    "deload_semana": 0
  }}
}}
"""

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
    return json.loads(text)

def call_gpt(datos: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    raw = _chat(client, build_prompt(datos))

    # Primer intento de parseo
    try:
        data = _try_parse_json(raw)
    except Exception as e:
        return {"ok": False, "error": f"JSON no válido: {e}", "raw": raw}

    # Validación de negocio
    errs = validar_negocio(data)
    if not errs:
        return {"ok": True, "data": data}

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

    return {"ok": True, "data": fixed}
