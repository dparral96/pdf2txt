#!/usr/bin/env python
# coding: utf-8

# # PDF → Texto Plano
# **Celda 1:** Arrastra el PDF. **Celda 2:** Procesa y descarga el `.txt`.

# In[1]:


# ── Instalación silenciosa (solo si falta) ────────────────────────────────────
import importlib, subprocess, sys

def ensure(pkg, import_as=None):
    name = import_as or pkg
    try:
        importlib.import_module(name)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg])

ensure('pymupdf', 'fitz')
ensure('ipywidgets', 'ipywidgets')

# ── Widget drag-and-drop ──────────────────────────────────────────────────────
import ipywidgets as widgets
from IPython.display import display, HTML

# Estado compartido entre celdas
state = {'filename': None, 'content': None}

uploader = widgets.FileUpload(
    accept='.pdf',
    multiple=False,
    description='📄 Subir PDF',
    layout=widgets.Layout(width='220px')
)

status_lbl = widgets.HTML(
    value='<span style="color:#888; font-family:monospace;">Sin archivo cargado.</span>'
)

def on_upload(change):
    if not uploader.value:
        return
    # API ipywidgets >= 7 y >= 8 difieren; manejo unificado
    uv = uploader.value
    if isinstance(uv, dict):          # v7: dict {filename: {...}}
        fname = list(uv.keys())[0]
        raw = uv[fname]['content']
    else:                              # v8: tuple de dicts
        item = uv[0]
        fname = item['name']
        raw = item['content']

    state['filename'] = fname
    state['content']  = bytes(raw)
    size_kb = len(state['content']) / 1024
    status_lbl.value = (
        f'<span style="color:#2a9; font-family:monospace; font-weight:bold;">'
        f'✔ {fname}</span> '
        f'<span style="color:#888; font-family:monospace;">({size_kb:.1f} KB) — '
        f'listo para procesar.</span>'
    )

uploader.observe(on_upload, names='value')

display(
    HTML('<h3 style="font-family:monospace; margin-bottom:8px;">① Cargar PDF</h3>'),
    uploader,
    status_lbl
)


# In[2]:


# ── Procesamiento y descarga ──────────────────────────────────────────────────
import re, base64, fitz
from IPython.display import display, HTML
import ipywidgets as widgets

# ── Parámetros configurables ──────────────────────────────────────────────────
# Calibrados para informes técnicos formato CMP/Códice Ingeniería
# (página A4/Letter con logos en header y pie de página con título + número)
#
# HEADER_MARGIN: fracción del alto de página excluida desde arriba.
#   0.05 → genérico (solo logos pequeños)
#   0.14 → informes CMP/Códice (logos + línea divisoria ocupan ~111pt en pág. de 792pt)
HEADER_MARGIN = 0.14
#
# FOOTER_MARGIN: fracción del alto de página excluida desde abajo.
#   0.05 → genérico
#   0.08 → informes CMP/Códice (footer "INFORME DE DISEÑO... Página X" en ~730pt)
FOOTER_MARGIN = 0.08
#
# SKIP_TOC: omitir páginas de índice/tabla de contenidos.
#   Detección: si >15% de los caracteres son puntos, se considera página de TOC.
SKIP_TOC = True
TOC_DOT_THRESHOLD = 0.15
#
# FIX_HYPHENATION: reunir palabras cortadas con guión al final de línea.
FIX_HYPHENATION = True
#
# CLEAN_DOT_LINES: eliminar líneas tipo "Sección ..... 12" residuales del TOC.
CLEAN_DOT_LINES = True
# ─────────────────────────────────────────────────────────────────────────────

RE_HYPHEN  = re.compile(r'-(\n)(\w)')
RE_DOTS    = re.compile(r'\.{3,}.*?\d+\s*\n?')   # líneas tipo "Título ..... 5"
RE_PAGENUM = re.compile(r'Página \d+ de \d+')     # residuo de footer si escapa el filtro
RE_SPACES  = re.compile(r'[ \t]+')
RE_BLANK   = re.compile(r'\n{3,}')


def is_toc_page(text: str) -> bool:
    """Detecta páginas de índice por alta densidad de puntos."""
    if not SKIP_TOC:
        return False
    return (text.count('.') / max(len(text), 1)) > TOC_DOT_THRESHOLD


def extract_text(pdf_bytes: bytes) -> tuple[str, int, int]:
    """Extrae texto limpio del PDF. Devuelve (texto, n_páginas_total, n_páginas_procesadas)."""
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    n_total = len(doc)
    pages_text = []

    for page in doc:
        h = page.rect.height
        blocks = page.get_text('blocks')  # (x0, y0, x1, y1, text, block_no, type)
        text_blocks = [
            b[4] for b in blocks
            if b[6] == 0                              # solo bloques de texto (no imágenes)
            and b[1] > HEADER_MARGIN * h             # excluir zona de header
            and b[3] < (1 - FOOTER_MARGIN) * h       # excluir zona de footer
        ]
        raw = ' '.join(text_blocks)

        if is_toc_page(raw):
            continue

        pages_text.append(raw)

    text = '\n\n'.join(pages_text)

    if FIX_HYPHENATION:
        text = RE_HYPHEN.sub(r'\2', text)
    if CLEAN_DOT_LINES:
        text = RE_DOTS.sub('', text)

    text = RE_PAGENUM.sub('', text)
    text = RE_SPACES.sub(' ', text)
    text = RE_BLANK.sub('\n\n', text)

    return text.strip(), n_total, len(pages_text)


def make_download_link(text: str, filename: str) -> str:
    """Genera link de descarga HTML sin depender de jupyter_server."""
    b64 = base64.b64encode(text.encode('utf-8')).decode()
    href = f'data:text/plain;charset=utf-8;base64,{b64}'
    stem = filename.rsplit('.', 1)[0]
    out_name = stem + '_texto.txt'
    return (
        f'<a href="{href}" download="{out_name}" '
        f'style="font-family:monospace; font-size:14px; padding:6px 14px; '
        f'background:#2a9; color:#fff; border-radius:4px; text-decoration:none;">'
        f'⬇ Descargar {out_name}</a>'
    )


# ── UI ────────────────────────────────────────────────────────────────────────
out_area = widgets.Output()
btn_proc = widgets.Button(
    description='⚙ Procesar PDF',
    button_style='primary',
    layout=widgets.Layout(width='160px')
)

def on_process(b):
    out_area.clear_output()
    with out_area:
        if state['content'] is None:
            display(HTML('<span style="color:red; font-family:monospace;">'
                         '✖ Ningún PDF cargado. Ejecuta primero la celda anterior.</span>'))
            return

        display(HTML('<span style="font-family:monospace; color:#888;">Procesando...</span>'))

        try:
            text, n_total, n_proc = extract_text(state['content'])
        except Exception as e:
            display(HTML(f'<span style="color:red; font-family:monospace;">Error: {e}</span>'))
            return

        n_chars     = len(text)
        est_tokens  = n_chars // 4

        out_area.clear_output()
        with out_area:
            display(HTML(
                f'<div style="font-family:monospace; margin-bottom:10px;">'
                f'<b>Páginas:</b> {n_proc} procesadas / {n_total} totales'
                f' &nbsp;|&nbsp; <b>Caracteres:</b> {n_chars:,}'
                f' &nbsp;|&nbsp; <b>Tokens ~:</b> {est_tokens:,}'
                f'</div>'
            ))
            display(HTML(make_download_link(text, state['filename'])))
            display(HTML('<hr style="margin:12px 0;"><b style="font-family:monospace;">Preview (500 chars):</b>'))
            display(HTML(
                f'<pre style="background:#f5f5f5; padding:10px; border-radius:4px; '
                f'font-size:12px; white-space:pre-wrap; max-height:200px; overflow-y:auto;">'
                f'{text[:500]}...</pre>'
            ))

btn_proc.on_click(on_process)

display(
    HTML('<h3 style="font-family:monospace; margin-bottom:8px;">② Procesar y descargar</h3>'),
    btn_proc,
    out_area
)

