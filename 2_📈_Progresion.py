import os
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional

import pandas as pd
import streamlit as st
import math

st.set_page_config(page_title="Progresión de Ejercicios", page_icon="📈", layout="wide")
st.title("📈 Progresión de Ejercicios")

st.caption("Visualiza la evolución de **peso** y **repeticiones** por ejercicio a lo largo del tiempo.")

@st.cache_data(show_spinner=False)
def discover_data_sources(base_dir: str):
    "Busca fuentes de datos posibles (SQLite/CSV) dentro del proyecto."
    dbs = []
    csvs = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            low = f.lower()
            if low.endswith((".db", ".sqlite", ".sqlite3")):
                dbs.append(os.path.join(root, f))
            if low.endswith(".csv"):
                csvs.append(os.path.join(root, f))
    return dbs, csvs

def _fetch_exercises_from_sqlite(db_path: str) -> Optional[List[str]]:
    "Intenta detectar nombres de tablas y columnas típicas para ejercicios."
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        # Descubrir tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        # Tablas candidatas
        candidates = [t for t in tables if any(k in t.lower() for k in ["serie","series","sets","entren","workout","training","registro"])]
        exercises = set()
        for t in candidates or tables:
            # Columnas candidatas
            cur.execute(f"PRAGMA table_info('{t}')")
            cols = [c[1].lower() for c in cur.fetchall()]
            # Heurística: columnas de interés
            has_ex = any(c in cols for c in ["ejercicio","exercise","nombre_ejercicio"])
            has_weight = any(c in cols for c in ["peso","weight","kg"])
            has_reps = any(c in cols for c in ["reps","repeticiones","rep"])
            if has_ex and (has_weight or has_reps):
                # Obtener valores únicos
                ex_col = "ejercicio" if "ejercicio" in cols else ("exercise" if "exercise" in cols else "nombre_ejercicio")
                cur.execute(f"SELECT DISTINCT {ex_col} FROM '{t}' WHERE {ex_col} IS NOT NULL AND TRIM({ex_col})<>'' LIMIT 5000")
                exercises.update([r[0] for r in cur.fetchall()])
        con.close()
        return sorted(e for e in exercises if e)
    except Exception:
        return None

def _fetch_progress_from_sqlite(db_path: str, exercise: str) -> Optional[pd.DataFrame]:
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        frames = []
        for t in tables:
            cur.execute(f"PRAGMA table_info('{t}')")
            cols_info = cur.fetchall()
            cols = [c[1] for c in cols_info]
            lcols = [c.lower() for c in cols]

            # map columns
            def pick(*opts):
                for o in opts:
                    if o in lcols:
                        return cols[lcols.index(o)]
                return None

            col_ex = pick("ejercicio","exercise","nombre_ejercicio")
            col_date = pick("fecha","date","created_at","day","session_date")
            col_weight = pick("peso","weight","kg")
            col_reps = pick("reps","repeticiones","rep","repetition")

            if not col_ex or not (col_weight or col_reps):
                continue

            # Construir SELECT
            select_cols = [col_ex]
            if col_date: select_cols.append(col_date)
            if col_weight: select_cols.append(col_weight)
            if col_reps: select_cols.append(col_reps)
            sql = f"SELECT {', '.join(select_cols)} FROM '{t}' WHERE {col_ex} = ?"
            try:
                df = pd.read_sql_query(sql, con, params=[exercise])
            except Exception:
                continue
            if df.empty:
                continue
            # Normalizar
            df.rename(columns={
                col_ex: "Ejercicio",
                col_date: "Fecha" if col_date else None,
                col_weight: "Peso",
                col_reps: "Reps",
            }, inplace=True)
            if "Fecha" in df.columns:
                # intentar convertir
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
                    try:
                        df["Fecha"] = pd.to_datetime(df["Fecha"], format=fmt, errors="ignore")
                    except Exception:
                        pass
                df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            else:
                df["Fecha"] = pd.NaT
            # limpiar
            if "Peso" in df.columns:
                df["Peso"] = pd.to_numeric(df["Peso"], errors="coerce")
            else:
                df["Peso"] = pd.NA
            if "Reps" in df.columns:
                df["Reps"] = pd.to_numeric(df["Reps"], errors="coerce")
            else:
                df["Reps"] = pd.NA
            frames.append(df[["Fecha","Peso","Reps"]])
        con.close()
        if not frames:
            return None
        out = pd.concat(frames, ignore_index=True)
        out = out.dropna(how="all", subset=["Fecha","Peso","Reps"])
        if out["Fecha"].notna().any():
            out = out.sort_values("Fecha")
        else:
            out = out.reset_index(drop=True)
        return out
    except Exception:
        return None

def _fetch_from_csvs(csv_paths: List[str]) -> List[str]:
    exs = set()
    for p in csv_paths:
        try:
            df = pd.read_csv(p)
        except Exception:
            try:
                df = pd.read_csv(p, sep=";")
            except Exception:
                continue
        lcols = [c.lower() for c in df.columns]
        def pick(*opts):
            for o in opts:
                if o in lcols:
                    return df.columns[lcols.index(o)]
            return None
        col_ex = pick("ejercicio","exercise","nombre_ejercicio")
        if col_ex is not None:
            exs.update(df[col_ex].dropna().astype(str).str.strip().unique().tolist())
    return sorted(e for e in exs if e)

def _progress_from_csvs(csv_paths: List[str], exercise: str) -> Optional[pd.DataFrame]:
    frames = []
    for p in csv_paths:
        try:
            df = pd.read_csv(p)
        except Exception:
            try:
                df = pd.read_csv(p, sep=";")
            except Exception:
                continue
        lcols = [c.lower() for c in df.columns]
        def pick(*opts):
            for o in opts:
                if o in lcols:
                    return df.columns[lcols.index(o)]
            return None
        col_ex = pick("ejercicio","exercise","nombre_ejercicio")
        if col_ex is None: 
            continue
        sub = df[df[col_ex].astype(str).str.strip() == exercise].copy()
        if sub.empty:
            continue
        col_date = pick("fecha","date","created_at","day","session_date")
        col_weight = pick("peso","weight","kg")
        col_reps = pick("reps","repeticiones","rep","repetition")
        sub.rename(columns={
            col_date: "Fecha" if col_date else None,
            col_weight: "Peso",
            col_reps: "Reps",
        }, inplace=True)
        if "Fecha" in sub.columns:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S","%Y/%m/%d %H:%M:%S"):
                try:
                    sub["Fecha"] = pd.to_datetime(sub["Fecha"], format=fmt, errors="ignore")
                except Exception:
                    pass
            sub["Fecha"] = pd.to_datetime(sub["Fecha"], errors="coerce")
        else:
            sub["Fecha"] = pd.NaT
        if "Peso" in sub.columns:
            sub["Peso"] = pd.to_numeric(sub["Peso"], errors="coerce")
        else:
            sub["Peso"] = pd.NA
        if "Reps" in sub.columns:
            sub["Reps"] = pd.to_numeric(sub["Reps"], errors="coerce")
        else:
            sub["Reps"] = pd.NA
        frames.append(sub[["Fecha","Peso","Reps"]])
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(how="all", subset=["Fecha","Peso","Reps"])
    if out["Fecha"].notna().any():
        out = out.sort_values("Fecha")
    else:
        out = out.reset_index(drop=True)
    return out

base_dir = os.path.dirname(__file__)
dbs, csvs = discover_data_sources(os.path.abspath(os.path.join(base_dir, "..")))

# Sugerir ejercicios detectados
detected_exercises = set()

# Probar SQLite primero
for db in dbs:
    exs = _fetch_exercises_from_sqlite(db)
    if exs:
        detected_exercises.update(exs)

# Probar CSV
if not detected_exercises:
    detected_exercises.update(_fetch_from_csvs(csvs))

if detected_exercises:
    ejercicio = st.selectbox("Elige un ejercicio", sorted(detected_exercises))
else:
    st.info("No se han detectado ejercicios automáticamente. Puedes escribir uno manualmente.")
    ejercicio = st.text_input("Nombre del ejercicio")

if ejercicio:
    df = None
    # Prioriza SQLite
    for db in dbs:
        df = _fetch_progress_from_sqlite(db, ejercicio)
        if df is not None and not df.empty:
            src = f"SQLite: {os.path.basename(db)}"
            break
    if (df is None or df.empty) and csvs:
        df = _progress_from_csvs(csvs, ejercicio)
        src = "CSV"
    if df is not None and not df.empty:
        st.success(f"Datos encontrados desde **{src}**.")

        # Métricas rápidas
        col1, col2, col3, col4 = st.columns(4)
        # 1RM estimado por Epley: 1RM ≈ peso * (1 + reps/30)
        if df["Peso"].notna().any() and df["Reps"].notna().any():
            df["1RM"] = df.apply(lambda r: r["Peso"] * (1 + (r["Reps"]/30)) if pd.notna(r["Peso"]) and pd.notna(r["Reps"]) else pd.NA, axis=1)
            best_1rm = df["1RM"].max(skipna=True)
            col1.metric("Mejor 1RM estimada", f"{best_1rm:.1f} kg" if isinstance(best_1rm, (int,float)) and not math.isnan(best_1rm) else "—")
        else:
            col1.metric("Mejor 1RM estimada", "—")

        max_peso = df["Peso"].max(skipna=True) if "Peso" in df.columns else None
        col2.metric("Máx. peso levantado", f"{max_peso:.1f} kg" if isinstance(max_peso, (int,float)) and not math.isnan(max_peso) else "—")

        if df["Fecha"].notna().any():
            first = df["Fecha"].min()
            last = df["Fecha"].max()
            col3.metric("Rango de fechas", f"{first.date()} → {last.date()}")
        else:
            col3.metric("Rango de fechas", "—")

        total_sessions = df.shape[0]
        col4.metric("Registros", f"{total_sessions}")

        st.subheader("Tendencia de Peso")
        if df["Fecha"].notna().any():
            st.line_chart(df.set_index("Fecha")[["Peso"]])
        else:
            st.line_chart(df[["Peso"]])

        st.subheader("Tendencia de Repeticiones")
        if df["Fecha"].notna().any():
            st.line_chart(df.set_index("Fecha")[["Reps"]])
        else:
            st.line_chart(df[["Reps"]])

        with st.expander("Ver tabla de datos"):
            st.dataframe(df)
    else:
        st.warning("No encontré datos de progresión. Asegúrate de tener registros con columnas de **ejercicio**, **peso** y **repeticiones** (y opcionalmente **fecha**).")
        st.markdown("""
**Cómo alimentar la progresión:**
- Si usas **SQLite**, asegúrate de que exista una tabla con columnas de *ejercicio*, *peso*, *reps* y opcionalmente *fecha*.
- Si usas **CSV**, coloca un archivo en el proyecto con esas columnas (por ejemplo, `workouts.csv`).
        """)
else:
    st.info("Selecciona o escribe un ejercicio para ver su progresión.")
