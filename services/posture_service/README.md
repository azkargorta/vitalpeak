# VitalPeak Posture Service (MVP gratis)

Microservicio FastAPI que analiza vídeos con **MediaPipe Pose** (sin OpenAI) para:

- **Sentadilla** (`squat`)
- **Peso muerto** (`deadlift`)
- **Press banca** (`bench_press`)

El MVP acepta **solo cámara lateral (side)** y devuelve un JSON con `score` y hasta 3 correcciones.

## Ejecutar en local

```bash
cd services/posture_service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Prueba:

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F exercise=squat \
  -F camera=side \
  -F video=@tu_video.mp4
```

## Desplegar (Docker)

Construir y ejecutar:

```bash
cd services/posture_service
docker build -t vitalpeak-posture .
docker run -p 8000:8000 vitalpeak-posture
```

## Conectar con Streamlit (VitalPeak)

En Streamlit Cloud → **Settings → Secrets**, añade:

```toml
POSTURE_API_URL = "https://TU-SERVICIO"  # ejemplo: https://vitalpeak-posture.onrender.com
```

> El endpoint usado por la app es `POSTURE_API_URL + /analyze`.
