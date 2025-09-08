# Página "📂 Biblioteca de PDFs"

Copia en tu proyecto:
- `app/pdf_store.py`
- `pages/06_Biblioteca de PDFs.py`

Al ejecutar, verás una **página nueva** en el menú de Streamlit con:
- Subida manual de PDFs (opcional).
- Listado de PDFs guardados por usuario.
- Descargar, eliminar y **renombrar** documentos.

Usa Postgres en Render para persistencia:
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
```
Si no lo defines, usa SQLite local.
