
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



def wants_single_leg_day(datos: dict) -> bool:
    txt = (str(datos.get("ia_detalles","")) + " " + str(datos.get("comentarios",""))).lower()
    keys = [
        "un solo día de pierna", "solo un día de pierna", "pierna solo un día", "1 día de pierna",
        "un solo dia de pierna", "solo un dia de pierna", "1 dia de pierna"
    ]
    return any(k in txt for k in keys)


def _is_lower_exercise(name: str) -> bool:
    n = str(name).lower()
    lower_kw = [
        "sentadilla", "squat", "prensa", "zancad", "extension cu", "extensión cu",
        "peso muerto", "deadlift", "hip thrust", "glute", "femoral", "curl femoral", "rdl", "good morning",
    ]
    return any(k in n for k in lower_kw)

def _upper_accessory_pool():
    return [
        "Face pulls", "Pájaros mancuernas", "Remo en polea", "Curl bíceps barra",
        "Extensión tríceps polea", "Elevaciones laterales", "Press inclinado mancuernas",
        "Remo mancuerna a banco", "Dominadas asistidas", "Plancha", "Crunch máquina",
    ]

def enforce_single_leg_day(plan: dict) -> dict:
    if not isinstance(plan, dict): 
        return plan
    dias = plan.get("dias") or plan.get("semanal") or plan

    def replace_lower_with_upper(e_list):
        pool = _upper_accessory_pool()
        new_list = []
        for e in e_list:
            name = e.get("nombre") if isinstance(e, dict) else str(e)
            if _is_lower_exercise(name):
                rep = {"nombre": pool[len(new_list) % len(pool)], "series": 3, "reps": "10-15", "descanso": "60-90s"}
                new_list.append(rep)
            else:
                new_list.append(e)
        while len(new_list) < 6:
            new_list.append({"nombre": pool[len(new_list) % len(pool)], "series": 3, "reps": "12-15", "descanso": "60-90s"})
        return new_list

    if isinstance(dias, dict):
        leg_days = []
        for d, exs in dias.items():
            ex_list = exs if isinstance(exs, list) else exs.get("ejercicios", [])
            if any(_is_lower_exercise(e.get("nombre") if isinstance(e, dict) else e) for e in ex_list):
                leg_days.append(d)
        if len(leg_days) > 1:
            for d in leg_days[1:]:
                ex_list = dias[d] if isinstance(dias[d], list) else dias[d].get("ejercicios", [])
                new_list = replace_lower_with_upper(ex_list)
                if isinstance(dias[d], list):
                    dias[d] = new_list
                else:
                    dias[d]["ejercicios"] = new_list
    elif isinstance(dias, list):
        leg_idx = []
        for idx, day in enumerate(dias):
            ex_list = day.get("ejercicios", [])
            if any(_is_lower_exercise(e.get("nombre") if isinstance(e, dict) else e) for e in ex_list):
                leg_idx.append(idx)
        if len(leg_idx) > 1:
            for idx in leg_idx[1:]:
                ex_list = dias[idx].get("ejercicios", [])
                new_list = replace_lower_with_upper(ex_list)
                dias[idx]["ejercicios"] = new_list
    return plan
