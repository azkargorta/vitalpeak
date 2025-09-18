from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, conint, validator

Nivel = Literal["principiante","intermedio","avanzado"]
Objetivo = Literal["fuerza","hipertrofia","resistencia","mixto"]

class Meta(BaseModel):
    nivel: Nivel
    dias: conint(ge=1, le=6)
    duracion_min: conint(ge=30, le=120)
    objetivo: Objetivo

class Ejercicio(BaseModel):
    nombre: str = Field(min_length=2)
    series: conint(ge=2, le=6)
    reps: str  # "5" o "6-8" o "10-12"
    intensidad: Optional[str] = None  # "RPE 7-8", "75-80%"
    descanso: str  # "60-90s", "2-3m"

    @validator("reps")
    def validar_reps(cls, v):
        import re
        v = v.strip()
        if re.fullmatch(r"\d{1,2}", v):
            return v
        if re.fullmatch(r"\d{1,2}\s*[–-]\s*\d{1,2}", v):
            return v
        if re.search(r"s$", v):
            return v
        raise ValueError("Formato de reps no válido. Usa p.ej. '5' o '6-8' o '10-12'")

class Dia(BaseModel):
    nombre: str
    ejercicios: List[Ejercicio] = Field(min_items=5, max_items=8)
    notas: Optional[str] = ""

class Progresion(BaseModel):
    principales: str
    accesorios: str
    deload_semana: int

class Rutina(BaseModel):
    meta: Meta
    dias: List[Dia]
    progresion: Progresion

def validar_negocio(data: Dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rutina = Rutina(**data)

    if len(rutina.dias) != rutina.meta.dias:
        errors.append(f"Número de días no coincide con meta.dias ({len(rutina.dias)} != {rutina.meta.dias})")

    for dia in rutina.dias:
        if any(k.lower() in dia.nombre.lower() for k in ["lower","pierna","piernas","inferior"]):
            for ej in dia.ejercicios:
                if "tríceps" in ej.nombre.lower() or "triceps" in ej.nombre.lower():
                    errors.append(f"'{dia.nombre}' incluye tríceps en ejercicio '{ej.nombre}'")

    def es_empuje(n): 
        n=n.lower(); 
        return any(t in n for t in ["press","banca","militar","hombro","fondos","apertura"])
    def es_tiron(n):
        n=n.lower()
        return any(t in n for t in ["remo","dominad","jalón","jalon","pull"])

    for dia in rutina.dias:
        if any(k.lower() in dia.nombre.lower() for k in ["upper","torso","superior"]):
            emp = any(es_empuje(ej.nombre) for ej in dia.ejercicios)
            tir = any(es_tiron(ej.nombre) for ej in dia.ejercicios)
            if not (emp and tir):
                errors.append(f"'{dia.nombre}' no balancea empuje/tirón")

    rep_set = set(ej.reps for d in rutina.dias for ej in d.ejercicios if not ej.reps.endswith("s"))
    if len(rep_set) <= 1:
        errors.append("Todas las reps son iguales; usa rangos distintos para principales/ secundarios/ accesorios.")

    for dia in rutina.dias:
        if not (5 <= len(dia.ejercicios) <= 7):
            errors.append(f"'{dia.nombre}' tiene {len(dia.ejercicios)} ejercicios (recomendado 6–7).")

            return errors
