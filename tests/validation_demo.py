
import json
from app.ai_generator import extract_constraints, validar_constraints, validar_comentarios, enforce_simple_constraints

# Comentarios de ejemplo (puedes editarlos y volver a ejecutar)
comentarios = "solo un día de pierna; al menos 4 ejercicios de bíceps; no máquinas; máximo 5 ejercicios por día"

# Plan de ejemplo con algunas violaciones intencionadas
plan = {
    "dias": [
        {
            "nombre": "Día 1 - Pecho/Bíceps",
            "grupo_principal": "pecho",
            "ejercicios": [
                {"nombre": "Press banca máquina", "series": 4, "reps": "8-10", "rir": "2", "musculo_principal": "pecho"},
                {"nombre": "Aperturas en polea", "series": 3, "reps": "12", "rir": "2", "musculo_principal": "pecho"},
                {"nombre": "Curl con barra", "series": 3, "reps": "8-10", "rir": "2", "musculo_principal": "bíceps"},
                {"nombre": "Curl martillo", "series": 3, "reps": "10-12", "rir": "1-2", "musculo_principal": "bíceps"},
                {"nombre": "Elevaciones laterales", "series": 3, "reps": "12-15", "rir": "1-2", "musculo_principal": "hombro"},
                {"nombre": "Face pull", "series": 2, "reps": "15", "rir": "2", "musculo_principal": "hombro"},
            ]
        },
        {
            "nombre": "Día 2 - Espalda/Bíceps",
            "grupo_principal": "espalda",
            "ejercicios": [
                {"nombre": "Remo con barra", "series": 4, "reps": "6-8", "rir": "2", "musculo_principal": "espalda"},
                {"nombre": "Jalón en polea", "series": 3, "reps": "10-12", "rir": "2", "musculo_principal": "espalda"},
                {"nombre": "Curl predicador", "series": 3, "reps": "10-12", "rir": "1-2", "musculo_principal": "bíceps"}
            ]
        },
        {
            "nombre": "Día 3 - Pierna/Glúteo",
            "grupo_principal": "pierna",
            "ejercicios": [
                {"nombre": "Sentadilla en máquina Smith", "series": 4, "reps": "6-8", "rir": "2", "musculo_principal": "pierna"},
                {"nombre": "Prensa de pierna", "series": 4, "reps": "8-10", "rir": "1-2", "musculo_principal": "pierna"},
                {"nombre": "Curl femoral en máquina", "series": 3, "reps": "12-15", "rir": "2", "musculo_principal": "pierna"}
            ]
        },
        {
            "nombre": "Día 4 - Pierna ligera/Core",
            "grupo_principal": "pierna",
            "ejercicios": [
                {"nombre": "Zancadas", "series": 3, "reps": "12", "rir": "2", "musculo_principal": "pierna"},
                {"nombre": "Plancha", "series": 3, "reps": "45s", "rir": "3", "musculo_principal": "core"}
            ]
        }
    ]
}

C = extract_constraints(comentarios)
errs_constraints = validar_constraints(plan, C)
errs_comments = validar_comentarios(plan, comentarios)
print("Comentarios:", comentarios)
print("Constraints:", json.dumps(C, ensure_ascii=False, indent=2))
print("\nViolaciones (constraints):")
for e in errs_constraints:
    print("-", e)
print("\nViolaciones (comentarios texto libre):")
for e in errs_comments:
    print("-", e)

# Intento de auto-ajuste simple antes de fallar (opcional)
plan_fixed = enforce_simple_constraints(plan, C)
errs_constraints_fixed = validar_constraints(plan_fixed, C)
errs_comments_fixed = validar_comentarios(plan_fixed, comentarios)
print("\nTras auto-ajuste simple:")
print("Violaciones (constraints):", errs_constraints_fixed)
print("Violaciones (comentarios texto libre):", errs_comments_fixed)
