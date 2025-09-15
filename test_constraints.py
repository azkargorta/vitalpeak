import json
from app import ai_generator

def run_test():
    comentarios = "solo un día de pierna y al menos 4 ejercicios de bíceps, rutina de 3 días"
    datos = {"comentarios": comentarios}

    C = ai_generator.extract_constraints(comentarios)
    print("Constraints extraídos:", json.dumps(C, ensure_ascii=False, indent=2))

    # Crear una rutina mínima de ejemplo (violará constraints)
    plan = {
        "dias": [
            {"grupo_principal":"pierna","ejercicios":[{"nombre":"Sentadilla","series":3,"reps":"10"}]},
            {"grupo_principal":"pecho","ejercicios":[{"nombre":"Press banca","series":3,"reps":"10"}]},
            {"grupo_principal":"espalda","ejercicios":[{"nombre":"Remo con barra","series":3,"reps":"10"}]}
        ]
    }

    errs = ai_generator.validar_constraints(plan, C)
    print("Errores detectados:", errs)

if __name__ == "__main__":
    run_test()
