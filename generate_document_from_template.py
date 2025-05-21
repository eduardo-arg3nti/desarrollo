import os
import argparse
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from template_manager import load_template # Suponiendo que template_manager.py está en el mismo dir o PYTHONPATH

# --- Configuración ---
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
FAISS_INDEX_FILE = "legal_corpus.index"
MAPPING_FILE = "legal_corpus_mapping.json"
DEFAULT_NUM_RELEVANT_FRAGMENTS = 3
PLACEHOLDER_NOTICE = "[[COMPLETAR ESTE DATO]]"

def get_case_embedding(text_content: str, model):
    """Genera embedding para el texto del caso."""
    if not text_content:
        return None
    try:
        return model.encode([text_content])[0]
    except Exception as e:
        print(f"Error generando embedding para el texto del caso: {e}")
        return None

def find_relevant_fragments(query_embedding, index, fragment_mapping, num_fragments: int):
    """Busca fragmentos relevantes en el índice FAISS."""
    if query_embedding is None or index is None or fragment_mapping is None:
        return []
    
    try:
        query_embedding_matrix = np.array(query_embedding, dtype='float32').reshape(1, -1)
        distances, indices = index.search(query_embedding_matrix, num_fragments)
        
        relevant_fragment_contents = []
        if indices[0].size > 0:
            for idx in indices[0]:
                if idx != -1: # FAISS puede devolver -1 si no hay suficientes vecinos
                    try:
                        fragment_path = fragment_mapping[idx]
                        with open(fragment_path, 'r', encoding='utf-8') as f:
                            relevant_fragment_contents.append(f.read())
                    except IndexError:
                        print(f"Advertencia: Índice de fragmento {idx} fuera de rango en el mapeo.")
                    except FileNotFoundError:
                        print(f"Advertencia: No se encontró el archivo de fragmento: {fragment_path}")
        return relevant_fragment_contents
    except Exception as e:
        print(f"Error durante la búsqueda FAISS de fragmentos: {e}")
        return []

def fill_template(template_content: str, context_data: dict) -> str:
    """
    Rellena la plantilla con los datos del contexto.
    Los placeholders no encontrados en context_data se dejan como están o se marcan.
    """
    filled_content = template_content
    for placeholder, value in context_data.items():
        filled_content = filled_content.replace(placeholder, str(value))
    
    # Opcional: Marcar placeholders restantes que no fueron llenados
    # Esto es una simplificación; una solución más robusta usaría regex para encontrar todos los "[...]"
    # y verificar si están en context_data o fueron llenados.
    # Por ahora, confiaremos en que los placeholders clave son manejados.
    # Si un placeholder de la plantilla no está en context_data, simplemente no se reemplaza.
    # Para ser más explícitos, podríamos añadir un paso que reemplace los no encontrados:
    # import re
    # for ph in re.findall(r"\[([A-Z0-9_]+)\]", filled_content):
    #     placeholder_full = f"[{ph}]"
    #     if placeholder_full not in context_data: # O si context_data[placeholder_full] es el valor por defecto
    #         filled_content = filled_content.replace(placeholder_full, PLACEHOLDER_NOTICE)

    return filled_content

def main():
    parser = argparse.ArgumentParser(description="Genera un documento legal a partir de una plantilla, un caso práctico y fragmentos relevantes.")
    parser.add_argument("--template_name", required=True, help="Nombre de la plantilla a usar (ej., 'amparo_simple').")
    parser.add_argument("--case_text_file", required=True, help="Ruta al archivo de texto del caso práctico.")
    parser.add_argument("--output_file", required=True, help="Ruta donde se guardará el documento generado.")
    parser.add_argument("--num_relevant_fragments", type=int, default=DEFAULT_NUM_RELEVANT_FRAGMENTS, help=f"Número de fragmentos legales relevantes a usar (default: {DEFAULT_NUM_RELEVANT_FRAGMENTS}).")

    args = parser.parse_args()

    print(f"Iniciando generación de documento para '{args.output_file}' usando plantilla '{args.template_name}'.")

    # 1. Cargar Plantilla
    print(f"Cargando plantilla '{args.template_name}'...")
    template_content = load_template(args.template_name)
    if not template_content:
        print(f"Error fatal: La plantilla '{args.template_name}' no pudo ser cargada. Abortando.")
        return
    print("Plantilla cargada exitosamente.")

    # 2. Procesar Caso Práctico
    print(f"Leyendo caso práctico desde '{args.case_text_file}'...")
    if not os.path.exists(args.case_text_file):
        print(f"Error fatal: El archivo del caso práctico '{args.case_text_file}' no fue encontrado. Abortando.")
        return
    try:
        with open(args.case_text_file, 'r', encoding='utf-8') as f:
            case_text = f.read()
    except Exception as e:
        print(f"Error fatal: No se pudo leer el archivo del caso práctico '{args.case_text_file}': {e}. Abortando.")
        return
    
    if not case_text.strip():
        print("Error fatal: El archivo del caso práctico está vacío. Abortando.")
        return
    print("Caso práctico leído exitosamente.")

    # 3. Cargar modelo y generar embedding para el caso
    print(f"Cargando el modelo de embeddings '{MODEL_NAME}'...")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error crítico al cargar el modelo de embeddings: {e}. Abortando.")
        return
    print("Modelo de embeddings cargado.")

    case_embedding = get_case_embedding(case_text, model)
    if case_embedding is None:
        print("Error fatal: No se pudo generar el embedding para el caso práctico. Abortando.")
        return
    print("Embedding del caso práctico generado.")

    # 4. Obtener Fragmentos Relevantes
    if not os.path.exists(FAISS_INDEX_FILE) or not os.path.exists(MAPPING_FILE):
        print(f"Error: Archivos de índice ('{FAISS_INDEX_FILE}') o mapeo ('{MAPPING_FILE}') no encontrados.")
        print("Asegúrate de haber ejecutado 'build_index.py' primero. Abortando.")
        return

    print(f"Cargando índice FAISS desde '{FAISS_INDEX_FILE}'...")
    try:
        index = faiss.read_index(FAISS_INDEX_FILE)
    except Exception as e:
        print(f"Error cargando el índice FAISS: {e}. Abortando.")
        return
    
    print(f"Cargando mapeo de fragmentos desde '{MAPPING_FILE}'...")
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            fragment_mapping = json.load(f)
    except Exception as e:
        print(f"Error cargando el archivo de mapeo: {e}. Abortando.")
        return

    if index.ntotal == 0:
        print("Advertencia: El índice FAISS está vacío. No se buscarán fragmentos relevantes.")
        relevant_fragments_content = []
    elif not fragment_mapping:
        print("Advertencia: El archivo de mapeo está vacío. No se podrán recuperar fragmentos.")
        relevant_fragments_content = []
    else:
        print("Buscando fragmentos relevantes...")
        relevant_fragments_content = find_relevant_fragments(case_embedding, index, fragment_mapping, args.num_relevant_fragments)
        if relevant_fragments_content:
            print(f"Se encontraron {len(relevant_fragments_content)} fragmentos relevantes.")
        else:
            print("No se encontraron fragmentos relevantes.")

    # 5. Preparar context_data para rellenar la plantilla
    context_data = {}
    context_data["[HECHOS_PRINCIPALES]"] = case_text.strip()
    
    # Para [DERECHO] o similares, concatenamos los fragmentos
    # (Esto es una simplificación, el placeholder exacto puede variar)
    derecho_placeholder_options = ["[DERECHO]", "[ARTICULOS_FUNDAMENTALES_ADICIONALES]", "[FUNDAMENTOS_DERECHO]", "[ARTICULOS_FUNDAMENTALES]"]
    concatenated_fragments = "\n\n--- Fragmento Legal Relevante ---\n".join(relevant_fragments_content) if relevant_fragments_content else "No se encontraron fragmentos legales relevantes."
    
    # Intentar llenar el placeholder de derecho más común o el primero que encuentre
    filled_derecho = False
    for ph_option in derecho_placeholder_options:
        if ph_option in template_content:
            context_data[ph_option] = concatenated_fragments
            filled_derecho = True
            print(f"Placeholder '{ph_option}' será llenado con fragmentos relevantes.")
            break
    if not filled_derecho and relevant_fragments_content : # Si hay fragmentos pero no se encontró placeholder de derecho
         print(f"Advertencia: No se encontró un placeholder de derecho estándar en la plantilla para los fragmentos. Los fragmentos son:\n{concatenated_fragments}")
    
    # Llenar todos los demás placeholders con el aviso por defecto
    # Esto es una simplificación. Idealmente, se identificarían todos los placeholders
    # y solo se pondría el aviso si no están en context_data.
    # Aquí, simplemente nos aseguramos de que los placeholders que SÍ tenemos (hechos, derecho) se usen.
    # Los demás definidos en la plantilla, si no están en context_data, no se tocarán por fill_template.
    # Si queremos que explícitamente se marquen, la lógica en fill_template necesitaría ser más robusta.

    print("Preparando datos de contexto para la plantilla...")
    # Llenar todos los placeholders definidos en la plantilla con PLACEHOLDER_NOTICE
    # excepto los que ya hemos llenado ([HECHOS_PRINCIPALES], y el de derecho)
    import re
    all_placeholders_in_template = re.findall(r"(\[[A-Z0-9_]+\])", template_content)
    for ph in all_placeholders_in_template:
        if ph not in context_data: # Si no lo hemos llenado ya explícitamente
            context_data[ph] = PLACEHOLDER_NOTICE
    print("Placeholders restantes marcados con aviso.")


    # 6. Rellenar Plantilla
    print("Rellenando la plantilla...")
    filled_document = fill_template(template_content, context_data)

    # 7. Guardar Documento
    print(f"Guardando documento generado en '{args.output_file}'...")
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(filled_document)
        print("Documento generado y guardado exitosamente.")
    except Exception as e:
        print(f"Error al guardar el documento: {e}")

if __name__ == '__main__':
    main()
