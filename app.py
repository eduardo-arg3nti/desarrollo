import streamlit as st
import os
from reference_search_tool import find_references, SUPPORTED_KB_EXTENSIONS
from pdf_generator import generate_report_pdf # Importar la función de generación de PDF
import tempfile

# --- Configuración Inicial ---
# Inicializar st.session_state si no existe
if 'query_filename_for_report' not in st.session_state:
    st.session_state.query_filename_for_report = None
if 'extracted_text_for_report' not in st.session_state:
    st.session_state.extracted_text_for_report = None
if 'results_for_report' not in st.session_state:
    st.session_state.results_for_report = []

st.set_page_config(page_title="Sistema de Búsqueda de Referencias", layout="wide")
st.title("📚 Sistema de Búsqueda de Referencias Legales")

# Definir rutas por defecto (relativas al directorio donde se ejecuta app.py)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KB_DIR = os.path.join(APP_DIR, "default_knowledge_base")
DEFAULT_INDEX_FILE = os.path.join(APP_DIR, "default_index.json")

# Crear directorio de KB por defecto si no existe
if not os.path.exists(DEFAULT_KB_DIR):
    try:
        os.makedirs(DEFAULT_KB_DIR)
        st.success(f"Directorio de base de conocimiento por defecto creado en: {DEFAULT_KB_DIR}")
        # Añadir un .gitkeep o un README para que no esté vacío y se pueda subir a git si es necesario
        with open(os.path.join(DEFAULT_KB_DIR, ".gitkeep"), "w") as f:
            pass
    except Exception as e:
        st.error(f"No se pudo crear el directorio por defecto de la base de conocimiento: {e}")

# --- Panel Lateral (Sidebar) para Configuración ---
st.sidebar.header("⚙️ Configuración")

kb_dir_input = st.sidebar.text_input(
    "Directorio de la Base de Conocimiento (KB):",
    value=DEFAULT_KB_DIR,
    help="Ruta al directorio que contiene los documentos de su base de conocimiento (TXT, PDF, DOCX)."
)

index_file_input = st.sidebar.text_input(
    "Archivo de Índice:",
    value=DEFAULT_INDEX_FILE,
    help="Ruta al archivo JSON donde se guardará/cargará el índice de la KB."
)

if st.sidebar.button("Ver Documentos en la Base de Conocimiento"):
    if kb_dir_input and os.path.isdir(kb_dir_input):
        st.sidebar.markdown("---")
        st.sidebar.subheader("Archivos en la Base de Conocimiento:")
        try:
            found_files = []
            for item in os.listdir(kb_dir_input):
                item_path = os.path.join(kb_dir_input, item)
                if os.path.isfile(item_path):
                    _, file_extension = os.path.splitext(item_path)
                    if file_extension.lower() in SUPPORTED_KB_EXTENSIONS:
                        found_files.append(item)
            
            if found_files:
                with st.sidebar.expander(f"Documentos encontrados ({len(found_files)}):", expanded=False):
                    for f_name in found_files:
                        st.write(f"- {f_name}")
            else:
                st.sidebar.warning("No se encontraron documentos soportados (TXT, PDF, DOCX) en el directorio especificado.")
        except Exception as e:
            st.sidebar.error(f"Error al listar archivos: {e}")
    else:
        st.sidebar.error("El directorio de la Base de Conocimiento especificado no es válido.")

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **Guía Rápida:**
    1.  Verifique/modifique las rutas de la Base de Conocimiento y el archivo de Índice.
    2.  (Opcional) Haga clic en "Ver Documentos..." para previsualizar los archivos de su KB.
    3.  Cargue su documento de consulta en el panel principal.
    4.  Haga clic en "Buscar Referencias".
    """
)


# --- Panel Principal para Interacción ---
st.header("🔍 Búsqueda de Referencias")

uploaded_file = st.file_uploader(
    "Cargue su documento de consulta:",
    type=['txt', 'pdf', 'docx', 'png', 'jpg', 'jpeg'],
    help="Seleccione el archivo (trabajo práctico, caso, etc.) para el cual desea encontrar referencias."
)

if uploaded_file is not None:
    st.info(f"Archivo cargado: **{uploaded_file.name}** (Tipo: {uploaded_file.type}, Tamaño: {uploaded_file.size / 1024:.2f} KB)")

search_button = st.button("Buscar Referencias", type="primary", use_container_width=True)

if search_button:
    if uploaded_file is None:
        st.warning("Por favor, cargue un documento de consulta primero.")
    elif not kb_dir_input or not os.path.isdir(kb_dir_input):
        st.error("Por favor, especifique un directorio válido para la Base de Conocimiento en la configuración lateral.")
    elif not index_file_input:
        st.error("Por favor, especifique una ruta válida para el Archivo de Índice en la configuración lateral.")
    else:
        # Guardar el archivo cargado temporalmente para pasarlo a find_references
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            query_document_path = tmp_file.name
        
        st.markdown("---")
        st.subheader("Resultados de la Búsqueda:")
        
        # Mostrar un spinner durante la indexación/búsqueda
        with st.spinner(f"Procesando y buscando referencias para '{uploaded_file.name}'... Esto puede tardar unos momentos, especialmente la primera vez."):
            try:
                # Validar la existencia del directorio KB justo antes de llamar
                if not os.path.isdir(kb_dir_input):
                    st.error(f"El directorio de la Base de Conocimiento '{kb_dir_input}' no fue encontrado. Verifique la ruta en la configuración.")
                    # Eliminar archivo temporal si la KB no existe para no dejarlo huérfano
                    if os.path.exists(query_document_path):
                        os.remove(query_document_path)
                else:
                    # --- Llamada a la función principal ---
                    results = find_references(query_document_path, index_file_input, kb_dir_input)
                    # --- Fin de la llamada ---
                    
                    # Almacenar información para el informe en session_state
                    st.session_state.query_filename_for_report = uploaded_file.name
                    # Re-extraer texto aquí para mostrarlo y para el informe
                    from text_extractor.extractor import extract_text 
                    query_text_for_report_and_display = extract_text(query_document_path)
                    
                    if query_text_for_report_and_display and "Error:" not in query_text_for_report_and_display:
                        st.session_state.extracted_text_for_report = query_text_for_report_and_display
                        with st.expander("Ver extracto del documento de consulta procesado"):
                            st.text(st.session_state.extracted_text_for_report[:500] + "...")
                    else:
                        st.session_state.extracted_text_for_report = f"Error al extraer texto: {query_text_for_report_and_display}"
                        st.warning(f"No se pudo mostrar el extracto del documento de consulta: {query_text_for_report_and_display}")
                    
                    st.session_state.results_for_report = results

                    if results:
                        st.success(f"Se encontraron **{len(results)}** documentos relevantes:")
                        for doc_path in results:
                            st.markdown(f"- `{doc_path}`")
                    else:
                        if not os.path.exists(index_file_input) or (os.path.exists(index_file_input) and os.path.getsize(index_file_input) < 100):
                             st.info("No se encontraron referencias. Es posible que la base de conocimiento esté vacía o el índice se haya creado por primera vez. Intente de nuevo si añadió documentos a la KB.")
                        else:
                            st.info("No se encontraron referencias para el documento de consulta.")
            
            except Exception as e:
                st.error(f"Ocurrió un error inesperado durante la búsqueda: {e}")
                # Loggear el error completo en la consola del servidor para depuración
                import traceback
                traceback.print_exc()
                # Limpiar st.session_state en caso de error grave
                st.session_state.query_filename_for_report = None
                st.session_state.extracted_text_for_report = None
                st.session_state.results_for_report = []
            finally:
                if os.path.exists(query_document_path):
                    try:
                        os.remove(query_document_path)
                        print(f"INFO (Streamlit App): Archivo temporal de consulta '{query_document_path}' eliminado.")
                    except Exception as e_rm:
                        print(f"ERROR (Streamlit App): No se pudo eliminar el archivo temporal de consulta '{query_document_path}': {e_rm}")

# Botón de descarga de PDF (aparece si hay resultados y datos para el informe)
if st.session_state.query_filename_for_report and st.session_state.results_for_report:
    st.markdown("---")
    st.subheader("📄 Descargar Informe")
    
    # Usar un nombre de archivo temporal único para el PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf_file:
        report_pdf_path = tmp_pdf_file.name # Obtener la ruta antes de cerrar
    
    # Generar el PDF
    pdf_generated = generate_report_pdf(
        st.session_state.query_filename_for_report,
        st.session_state.extracted_text_for_report,
        st.session_state.results_for_report,
        report_pdf_path 
    )

    if pdf_generated:
        try:
            with open(report_pdf_path, "rb") as f_pdf:
                pdf_bytes = f_pdf.read()
            
            st.download_button(
                label="Descargar Informe en PDF",
                data=pdf_bytes,
                file_name=f"informe_referencias_{st.session_state.query_filename_for_report.split('.')[0]}.pdf",
                mime="application/pdf"
            )
        except Exception as e_read_pdf:
            st.error(f"Error al leer el archivo PDF generado para descarga: {e_read_pdf}")
        finally:
            # Limpiar el archivo PDF temporal después de leerlo para la descarga
            if os.path.exists(report_pdf_path):
                try:
                    os.remove(report_pdf_path)
                    print(f"INFO (Streamlit App): Archivo PDF temporal '{report_pdf_path}' eliminado.")
                except Exception as e_rm_pdf:
                    print(f"ERROR (Streamlit App): No se pudo eliminar el archivo PDF temporal '{report_pdf_path}': {e_rm_pdf}")
    else:
        st.error("No se pudo generar el informe PDF.")


# Ejemplo de cómo ejecutar:
# 1. Asegúrate de tener los archivos: app.py, reference_search_tool.py, search_system.py, text_extractor/extractor.py, pdf_generator.py
# 2. Crea el directorio 'default_knowledge_base' en la misma ruta que app.py si no se crea automáticamente.
# 3. Pon algunos archivos .txt, .pdf, .docx en 'default_knowledge_base'.
# 4. Ejecuta desde la terminal: streamlit run app.py

st.markdown("---")
st.caption("Desarrollado como parte de un proyecto de IA. Asegúrese de que Tesseract OCR esté instalado si usa PDFs o imágenes escaneadas.")

```
