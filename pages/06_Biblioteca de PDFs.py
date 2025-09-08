import streamlit as st
import datetime as dt
from app.pdf_store import list_pdfs, get_pdf_content, delete_pdf, save_pdf, update_title

st.set_page_config(page_title="📂 Biblioteca de PDFs", page_icon="📂", layout="centered")
st.title("📂 Biblioteca de PDFs")

user = st.session_state.get("user", "default")

# Upload manual (opcional)
with st.expander("➕ Subir un PDF manualmente", expanded=False):
    up = st.file_uploader("Selecciona un PDF", type=["pdf"])
    title = st.text_input("Título", value=f"Documento {dt.date.today()}")
    if st.button("Guardar PDF"):
        if up is None:
            st.warning("Selecciona un PDF primero.")
        else:
            content = up.getvalue()
            doc_id = save_pdf(user, title, content)
            st.success(f"PDF guardado con id #{doc_id}")

st.markdown("---")
st.subheader("Tus documentos")

filtro = st.text_input("Buscar por título", placeholder="Escribe para filtrar...")
data = list_pdfs(user)
if not data:
    st.info("No hay PDFs guardados todavía.")
else:
    # simple filtro por texto
    data = [d for d in data if filtro.lower() in d["title"].lower()] if filtro else data
    for doc in data:
        with st.expander(f"#{doc['id']} — {doc['title']}  |  {round(doc['size']/1024,1)} KB"):
            col1, col2, col3, col4 = st.columns([1,1,1,2])
            with col1:
                content = get_pdf_content(doc["id"])
                st.download_button("⬇️ Descargar", data=content, file_name=f"{doc['title']}.pdf", mime="application/pdf", key=f"pdfdl_{doc['id']}")
            with col2:
                if st.button("🗑️ Eliminar", key=f"pdfdel_{doc['id']}"):
                    if delete_pdf(doc["id"]):
                        st.warning("Eliminado. Recarga la página para actualizar la lista.")
            with col3:
                new_title = st.text_input("Renombrar", value=doc["title"], key=f"pdfnew_{doc['id']}")
                if st.button("Guardar nombre", key=f"pdfname_{doc['id']}"):
                    if update_title(doc["id"], new_title):
                        st.success("Nombre actualizado. Recarga para ver los cambios.")
            with col4:
                st.caption(f"Creado: {doc.get('created_at','')}")
