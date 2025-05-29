import os
import shutil # Para la limpieza de directorios
from text_extractor.extractor import extract_text
from search_system import SearchIndex # Asumiendo que search_system.py está en el mismo dir o PYTHONPATH

# Extensiones soportadas para la base de conocimiento
SUPPORTED_KB_EXTENSIONS = ['.txt', '.pdf', '.docx']

def find_references(query_document_path, index_file_path, knowledge_base_dir):
    """
    Encuentra documentos de referencia en una base de conocimiento que son relevantes
    para un documento de consulta dado.

    Args:
        query_document_path (str): Ruta al documento de consulta.
        index_file_path (str): Ruta al archivo JSON del índice.
        knowledge_base_dir (str): Ruta al directorio con los documentos de la BC.

    Returns:
        list: Una lista de rutas de archivo de los documentos relevantes.
              Devuelve una lista vacía si no se encuentran referencias o en caso de error.
    """
    print(f"INFO: Iniciando búsqueda de referencias para: '{query_document_path}'")
    print(f"INFO: Usando archivo de índice: '{index_file_path}'")
    print(f"INFO: Directorio de base de conocimiento: '{knowledge_base_dir}'")

    # 0. Validar rutas de entrada
    if not os.path.exists(query_document_path):
        print(f"Error: El documento de consulta '{query_document_path}' no existe.")
        return []
    if not os.path.isdir(knowledge_base_dir): # El directorio para el index_file_path se crea si no existe por save_index
        print(f"Error: El directorio de la base de conocimiento '{knowledge_base_dir}' no existe o no es un directorio.")
        return []

    search_index = SearchIndex(index_file_path=index_file_path) # Intenta cargar el índice

    # 1. Cargar o construir el índice
    # SearchIndex ya intenta cargar en __init__. Si el índice no está poblado (ej. nuevo o carga fallida), lo construimos.
    # Una forma de verificar si el índice está "vacío" o no fue cargado es ver si self.documents tiene elementos.
    # Sin embargo, un índice cargado podría estar vacío si la BC estaba vacía.
    # Mejor, verificamos si el archivo de índice existía ANTES de llamar a SearchIndex.
    # Pero SearchIndex maneja la no existencia internamente.
    # Una solución más simple: si después de __init__, no hay documentos, intentamos construir.
    
    # Si el índice no se cargó (o estaba vacío) y el directorio KB existe, indexar.
    # Comprobamos si el índice tiene documentos. Si no, y el archivo de índice no existía originalmente,
    # o si simplemente queremos re-indexar si el índice parece vacío.
    # La lógica actual de SearchIndex es que si el archivo no existe, se crea uno vacío.
    # Si existe y es válido, se carga. Si existe pero es inválido, se crea uno vacío.

    # Si el índice está vacío (no se cargó o la BC original estaba vacía)
    if not search_index.documents:
        print(f"INFO: El índice '{index_file_path}' está vacío o no se pudo cargar. Intentando construir desde '{knowledge_base_dir}'...")
        
        if not os.listdir(knowledge_base_dir):
            print(f"Advertencia: El directorio de la base de conocimiento '{knowledge_base_dir}' está vacío. No se construirá ningún índice.")
            # No necesariamente un error si se espera que la BC pueda estar vacía.
            # Si el documento de consulta también está vacío, la búsqueda devolverá [].
        else:
            files_indexed = 0
            for item in os.listdir(knowledge_base_dir):
                item_path = os.path.join(knowledge_base_dir, item)
                if os.path.isfile(item_path):
                    _, file_extension = os.path.splitext(item_path)
                    if file_extension.lower() in SUPPORTED_KB_EXTENSIONS:
                        print(f"INFO: Añadiendo '{item_path}' al índice...")
                        doc_id = search_index.add_document(item_path)
                        if doc_id:
                            files_indexed +=1
                            print(f"INFO: Documento '{item_path}' añadido al índice con ID {doc_id}.")
                        else:
                            print(f"Advertencia: No se pudo procesar o indexar el documento '{item_path}'.")
            
            if files_indexed > 0:
                search_index.save_index(index_file_path)
                print(f"INFO: Nuevo índice construido y guardado en '{index_file_path}' con {files_indexed} archivos.")
            else:
                print("INFO: No se indexaron nuevos archivos. El índice permanece vacío.")


    # 2. Procesar el documento de consulta
    print(f"INFO: Extrayendo texto del documento de consulta '{query_document_path}'...")
    query_text = extract_text(query_document_path)

    if query_text is None or "Error:" in query_text or not query_text.strip():
        print(f"Error: No se pudo extraer texto del documento de consulta '{query_document_path}'. Detalle: {query_text}")
        return []
    
    query_text_preview = query_text[:200].replace('\n', ' ')
    print(f"INFO: Texto extraído de la consulta (primeros 200 chars): '{query_text_preview}...'")

    # 3. Realizar la búsqueda
    print("INFO: Realizando búsqueda en el índice...")
    relevant_documents = search_index.search(query_text)

    if not relevant_documents:
        print("INFO: No se encontraron documentos relevantes en la base de conocimiento.")
    else:
        print(f"INFO: Se encontraron {len(relevant_documents)} documentos relevantes.")

    # 4. Devolver resultados
    return relevant_documents


if __name__ == '__main__':
    print("--- Iniciando Prueba de Búsqueda de Referencias ---")

    # Directorios y archivos temporales para la prueba
    TEST_DIR = "temp_reference_search_test"
    KB_DIR = os.path.join(TEST_DIR, "knowledge_base")
    QUERY_DOC_DIR = os.path.join(TEST_DIR, "query_docs")
    INDEX_FILE = os.path.join(TEST_DIR, "test_index.json")

    # Limpiar de ejecuciones anteriores si existen
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

    # Crear directorios
    os.makedirs(KB_DIR, exist_ok=True)
    os.makedirs(QUERY_DOC_DIR, exist_ok=True)

    print(f"Directorio de prueba creado en: {os.path.abspath(TEST_DIR)}")

    print("\n--- Creando archivos de la Base de Conocimiento ---")
    # Simplificamos: creamos todos como .txt para la prueba de reference_search_tool.
    # La capacidad del extractor para manejar .docx/.pdf ya fue probada en su propio módulo.
    # Aquí nos centramos en el flujo de indexación y búsqueda.
    kb_files_content = {
        "kb_doc1.txt": "Este es el primer documento de la base de conocimiento. Habla sobre leyes de software y propiedad intelectual.",
        "kb_doc2.txt": "El segundo documento trata sobre la ley de protección de datos y la privacidad del usuario. El software debe ser seguro.",
        "kb_doc3.txt": "Un tercer documento que menciona normativas sobre desarrollo de software y buenas prácticas.", # Anteriormente simulaba docx
        "kb_doc4.txt": "Un cuarto documento que habla sobre licencias de software. Código abierto y software privativo." # Anteriormente simulaba pdf
    }

    for filename, content in kb_files_content.items():
        path = os.path.join(KB_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creado: {path}")

    # Crear archivo de consulta de ejemplo
    print("\n--- Creando archivo de consulta ---")
    query_file_path = os.path.join(QUERY_DOC_DIR, "query1.txt")
    # Consulta ajustada para Prueba 1 y 2 para que coincida con kb_doc2.txt
    with open(query_file_path, 'w', encoding='utf-8') as f:
        f.write("software y privacidad")
    print(f"Creado: {query_file_path}")

    # query_image_path = os.path.join(QUERY_DOC_DIR, "query_image.png") # Descomentar para prueba de imagen
    # try:
    #     from PIL import Image, ImageDraw
    #     img = Image.new('RGB', (600, 100), color = 'white')
    #     draw = ImageDraw.Draw(img)
    #     draw.text((10,10), "Consulta sobre licencias de software", fill='black')
    #     img.save(query_image_path)
    #     print(f"Creado archivo de consulta tipo imagen: {query_image_path}")
    # except ImportError:
    #     print("PIL no está disponible, no se creará archivo de consulta de imagen.")
    #     query_image_path = None


    # --- Ejecutar find_references ---
    # Prueba 1: Índice no existe, se debe construir
    print("\n\n--- Prueba 1: Índice no existente ---")
    if os.path.exists(INDEX_FILE): # Asegurar que el índice no exista para esta prueba
        os.remove(INDEX_FILE)
        
    results = find_references(query_file_path, INDEX_FILE, KB_DIR)
    print(f"\nDocumentos relevantes encontrados para '{query_file_path}':")
    if results:
        for doc_path in results: # Esperado: [temp_reference_search_test/knowledge_base/kb_doc2.txt]
            print(f"- {doc_path}")
    else:
        print("Ninguno.")
    # Esperado: kb_doc2.txt (software, privacidad)

    # Prueba 2: Índice ya existe, se debe cargar
    print("\n\n--- Prueba 2: Índice existente ---")
    # El índice ya fue creado y guardado en la prueba anterior.
    results_loaded = find_references(query_file_path, INDEX_FILE, KB_DIR)
    print(f"\nDocumentos relevantes encontrados (índice cargado) para '{query_file_path}':")
    if results_loaded:
        for doc_path in results_loaded: # Esperado: [temp_reference_search_test/knowledge_base/kb_doc2.txt]
            print(f"- {doc_path}")
    else:
        print("Ninguno.")
    # Esperado: Mismos resultados que la Prueba 1.

    # Prueba 3: Documento de consulta que podría coincidir con el simulado PDF (ahora kb_doc4.txt).
    print("\n\n--- Prueba 3: Consulta para contenido de kb_doc4.txt ---")
    query_kb4_path = os.path.join(QUERY_DOC_DIR, "query_for_kb4.txt")
    # Consulta ajustada para Prueba 3
    with open(query_kb4_path, 'w', encoding='utf-8') as f:
        f.write("código abierto y licencias de software") # Eliminado "Información sobre" y añadido "de software"
    print(f"Creado: {query_kb4_path}")
    
    results_kb4_query = find_references(query_kb4_path, INDEX_FILE, KB_DIR)
    print(f"\nDocumentos relevantes encontrados para '{query_kb4_path}':")
    if results_kb4_query:
        for doc_path in results_kb4_query: # Esperado: [temp_reference_search_test/knowledge_base/kb_doc4.txt]
            print(f"- {doc_path}") 
    else:
        print("Ninguno.")


    # Prueba 4: Documento de consulta no existente
    print("\n\n--- Prueba 4: Documento de consulta no existente ---")
    non_existent_query = os.path.join(QUERY_DOC_DIR, "non_existent.txt")
    results_non_existent = find_references(non_existent_query, INDEX_FILE, KB_DIR)
    print(f"\nDocumentos relevantes encontrados para '{non_existent_query}': {results_non_existent}")
    # Esperado: [] y un mensaje de error.

    # Prueba 5: Base de conocimiento no existente
    print("\n\n--- Prueba 5: Base de conocimiento no existente ---")
    if os.path.exists(INDEX_FILE): # Eliminar índice para forzar intento de construcción
        os.remove(INDEX_FILE)
    results_kb_non_existent = find_references(query_file_path, INDEX_FILE, "non_existent_kb_dir")
    print(f"\nDocumentos relevantes encontrados (KB no existente): {results_kb_non_existent}")
     # Esperado: [] y un mensaje de error.

    # Limpieza
    print("\n--- Limpiando archivos y directorios de prueba ---")
    if os.path.exists(TEST_DIR):
        try:
            shutil.rmtree(TEST_DIR)
            print(f"Directorio de prueba '{TEST_DIR}' eliminado.")
        except Exception as e:
            print(f"Error al eliminar el directorio de prueba '{TEST_DIR}': {e}")
    
    print("\n--- Fin de la Prueba de Búsqueda de Referencias ---")
