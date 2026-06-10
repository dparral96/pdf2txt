# PDF → Texto Plano

Aplicación web desarrollada en Python + Streamlit para extraer texto limpio desde archivos PDF.

Basada en una versión modificada del código original **`pdf_to_text.ipynb`** desarrollado por **José Bustos Fonseca**, adaptada para ejecución mediante interfaz web en Streamlit.

## Funcionalidades

* Carga de archivos PDF desde el navegador.
* Extracción automática de texto.
* Eliminación opcional de encabezados y pies de página.
* Detección y omisión de páginas de índice.
* Corrección de palabras cortadas por guiones.
* Descarga del resultado como archivo `.txt`.

## Uso

Acceder a la aplicación desde:

https://pdf2txt-260610.streamlit.app/

Subir un archivo PDF y descargar el texto procesado.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tecnologías

* Python
* Streamlit
* PyMuPDF

## Autor

Daniel Eduardo Parra Leficura
