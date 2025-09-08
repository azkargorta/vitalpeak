
import os, json
from typing import Any, Dict
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def build_prompt(datos: Dict[str, Any]) -> str:
    return f"""
Eres un entrenador personal experto.
Genera una rutina semanal de gimnasio basada en estos datos del usuario (JSON):
{json.dumps(datos, ensure_ascii=False)}

REQUISITOS OBLIGATORIOS DE LA RESPUESTA:
- Devuélvela **solo** como JSON válido (sin texto adicional) con este esquema:
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
        {{"nombre":"", "series": int, "reps": "5|6-8|10-12|...", "intensidad": "RPE o % (opcional)", "descanso": "segundos o minutos"}}
      ],
      "notas": "opcional"
    }}
  ],
  "progresion": {{
    "principales": "regla de progresión",
    "accesorios": "regla de progresión",
    "deload_semana": 0
  }}
}}

REGLAS:
- 6-7 ejercicios por día, duración objetivo {datos.get('duracion', 60)} minutos.
- Balancea empujes/tirones en upper y cuádriceps/ischios en lower.
- Incluye descansos y rangos de repeticiones adecuados al objetivo.
- No repitas el mismo patrón pesado dos días seguidos.
- Ajusta a material disponible si se proporciona.
""""

def call_gpt(datos: Dict[str, Any]) -> Dict[str, Any]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = build_prompt(datos)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.6,
        messages=[
            {"role":"system","content":"Responde únicamente con JSON válido."},
            {"role":"user","content": prompt}
        ]
    )
    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": f"No se pudo parsear la respuesta del modelo: {e}", "raw": content}

