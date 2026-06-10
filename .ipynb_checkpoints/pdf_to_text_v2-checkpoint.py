#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# DPL_PDF2TXT_260610


# PDF → Texto Plano
# 
# Aplicación interactiva en Streamlit para extraer texto limpio desde archivos PDF.
# 
# Funcionalidades:
# - Carga de archivos PDF desde el navegador.
# - Eliminación automática de encabezados y pies de página mediante márgenes configurables.
# - Detección y omisión opcional de índices o tablas de contenido.
# - Reconstrucción de palabras separadas por guiones entre líneas.
# - Limpieza de numeración de páginas, espacios y líneas residuales.
# - Visualización previa del texto extraído.
# - Descarga del resultado como archivo .txt.
# 
# Parámetros ajustables:
# - HEADER_MARGIN: porcentaje superior excluido (header).
# - FOOTER_MARGIN: porcentaje inferior excluido (footer).
# - SKIP_TOC: omitir páginas tipo índice.
# - FIX_HYPHENATION: unir palabras cortadas.
# - CLEAN_DOT_LINES: limpiar líneas tipo "Sección ..... 12".
# 
# Uso:
#     streamlit run app.py
# 
# Dependencias:
#     - streamlit
#     - pymupdf (fitz)

# In[2]:


import importlib
import subprocess
import sys
import re
import fitz
import streamlit as st


# In[ ]:


# ── Instalación silenciosa ────────────────────────────────────────
def ensure(pkg, import_as=None):
    name = import_as or pkg
    try:
        importlib.import_module(name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

ensure("pymupdf", "fitz")


# In[ ]:


# ── Configuración ─────────────────────────────────────────────────
HEADER_MARGIN = 0.14
FOOTER_MARGIN = 0.08

SKIP_TOC = True
TOC_DOT_THRESHOLD = 0.15

FIX_HYPHENATION = True
CLEAN_DOT_LINES = True

RE_HYPHEN = re.compile(r"-(\n)(\w)")
RE_DOTS = re.compile(r"\.{3,}.*?\d+\s*\n?")
RE_PAGENUM = re.compile(r"Página \d+ de \d+")
RE_SPACES = re.compile(r"[ \t]+")
RE_BLANK = re.compile(r"\n{3,}")


# In[ ]:


# ── Funciones ────────────────────────────────────────────────────
def is_toc_page(text):
    if not SKIP_TOC:
        return False
    return (text.count(".") / max(len(text), 1)) > TOC_DOT_THRESHOLD

def extract_text(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = len(doc)
    pages = []

    for page in doc:
        h = page.rect.height
        blocks = page.get_text("blocks")
        text_blocks = [
            b[4]
            for b in blocks
            if (
                b[6] == 0
                and b[1] > HEADER_MARGIN * h
                and b[3] < (1 - FOOTER_MARGIN) * h
            )
        ]

        raw = " ".join(text_blocks)
        if is_toc_page(raw):
            continue
        pages.append(raw)
    text = "\n\n".join(pages)

    if FIX_HYPHENATION:
        text = RE_HYPHEN.sub(r"\2", text)

    if CLEAN_DOT_LINES:
        text = RE_DOTS.sub("", text)

    text = RE_PAGENUM.sub("", text)
    text = RE_SPACES.sub(" ", text)
    text = RE_BLANK.sub("\n\n", text)

    return text.strip(), total, len(pages)


# In[1]:


# ── UI Streamlit ──────────────────────────────────────────────────
st.set_page_config(page_title="PDF → Texto",page_icon="📄",layout="wide")
st.title("📄 PDF → Texto Plano")
uploaded = st.file_uploader("Sube un PDF",type=["pdf"])

if uploaded:

    pdf_bytes = uploaded.read()
    size_kb = len(pdf_bytes) / 1024
    st.success(f"✔ {uploaded.name} ({size_kb:.1f} KB)")
    col1, col2 = st.columns([1, 3])
    with col1:
        procesar = st.button("⚙ Procesar PDF",use_container_width=True)
    if procesar:
        with st.spinner("Procesando..."):
            try:
                text, n_total, n_proc = extract_text(pdf_bytes)
            except Exception as e:
                st.error(str(e))
                st.stop()
        n_chars = len(text)
        est_tokens = n_chars // 4

        st.info(f"Páginas: {n_proc}/{n_total} | "f"Caracteres: {n_chars:,} | "f"Tokens ≈ {est_tokens:,}")
        out_name = (uploaded.name.rsplit(".", 1)[0]+ "_texto.txt")
        st.download_button("⬇ Descargar TXT",data=text,file_name=out_name,mime="text/plain")
        st.subheader("Vista previa")
        st.text_area("",value=text[:5000],height=350)

