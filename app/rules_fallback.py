
from typing import Dict, Any, List

def _upper_lower_template(dias:int, dur:int, objetivo:str) -> Dict[str, Any]:
    if dias >= 4:
        schedule = ["Upper A","Lower A","Upper B","Lower B"]
    elif dias == 3:
        schedule = ["FullBody A","FullBody B","FullBody C"]
    elif dias == 2:
        schedule = ["FullBody A","FullBody B"]
    else:
        schedule = ["FullBody A"]

    def ejercicios(day_name:str) -> List[Dict[str, Any]]:
        if "Upper" in day_name:
            return [
                {"nombre":"Press banca", "series":4, "reps":"5-6", "intensidad":"RPE 7-8", "descanso":"2-3m"},
                {"nombre":"Remo con barra", "series":4, "reps":"6-8", "descanso":"2m"},
                {"nombre":"Press inclinado mancuernas", "series":3, "reps":"8-10", "descanso":"90s"},
                {"nombre":"Jalón al pecho", "series":3, "reps":"8-10", "descanso":"90s"},
                {"nombre":"Elevación lateral", "series":3, "reps":"12-15", "descanso":"60-75s"},
                {"nombre":"Plancha", "series":3, "reps":"40-60s", "descanso":"45-60s"}
            ]
        elif "Lower" in day_name:
            return [
                {"nombre":"Sentadilla trasera", "series":4, "reps":"5-6", "intensidad":"RPE 7-8", "descanso":"2-3m"},
                {"nombre":"Peso muerto rumano", "series":4, "reps":"6-8", "descanso":"2-3m"},
                {"nombre":"Prensa", "series":3, "reps":"8-10", "descanso":"2m"},
                {"nombre":"Curl femoral", "series":3, "reps":"10-12", "descanso":"90s"},
                {"nombre":"Gemelos de pie", "series":3, "reps":"12-15", "descanso":"60-75s"},
                {"nombre":"Crunch cable", "series":3, "reps":"10-15", "descanso":"60s"}
            ]
        else:
            return [
                {"nombre":"Sentadilla frontal", "series":4, "reps":"5-6", "descanso":"2-3m"},
                {"nombre":"Press banca", "series":4, "reps":"5-6", "descanso":"2-3m"},
                {"nombre":"Remo mancuerna 1 brazo", "series":3, "reps":"8-10", "descanso":"90s"},
                {"nombre":"Peso muerto rumano", "series":3, "reps":"6-8", "descanso":"2m"},
                {"nombre":"Elevación lateral", "series":3, "reps":"12-15", "descanso":"60-75s"},
                {"nombre":"Plancha", "series":3, "reps":"40-60s", "descanso":"45-60s"}
            ]

    dias_out = [{"nombre": d, "ejercicios": ejercicios(d), "notas": ""} for d in schedule]
    return {
        "meta": {"nivel":"intermedio","dias":dias,"duracion_min":dur,"objetivo":objetivo},
        "dias": dias_out,
        "progresion": {
            "principales":"+2.5/5kg al completar 4x5 @≤RPE8",
            "accesorios":"doble progresión 8-12/12-15",
            "deload_semana": 5
        }
    }

def generate_fallback(datos: Dict[str, Any]) -> Dict[str, Any]:
    dias = int(datos.get("dias", 4))
    dur = int(datos.get("duracion", 60))
    objetivo = str(datos.get("objetivo","fuerza"))
    return _upper_lower_template(dias, dur, objetivo)
