import os
import numpy as np
import faiss
import json
import argparse

# --- Configuración ---
LEGAL_CORPUS_DIR = "legal_corpus"
OUTPUT_INDEX_FILE = "legal_corpus.index"
OUTPUT_MAPPING_FILE = "legal_corpus_mapping.json"

def load_embeddings_and_create_mapping(corpus_dir: str):
    """
    Carga todos los embeddings .npy del corpus y crea un mapeo a sus archivos .txt originales.
    """
    all_embeddings = []
    fragment_paths_mapping = []

    print(f"Cargando embeddings desde: {corpus_dir}")

    if not os.path.exists(corpus_dir):
        print(f"  Error: El directorio del corpus '{corpus_dir}' no fue encontrado.")
        return None, None

    doc_subdirs = [d for d in os.listdir(corpus_dir) if os.path.isdir(os.path.join(corpus_dir, d))]

    if not doc_subdirs:
        print(f"  No se encontraron subdirectorios de documentos en '{corpus_dir}'.")
        return None, None

    total_embeddings_loaded = 0
    for doc_dirname in doc_subdirs:
        doc_dir_path = os.path.join(corpus_dir, doc_dirname)
        # print(f"  Procesando subdirectorio: {doc_dir_path}")
        
        npy_files = [f for f in os.listdir(doc_dir_path) if f.endswith(".npy")]
        
        for npy_file in npy_files:
            npy_filepath = os.path.join(doc_dir_path, npy_file)
            base_filename, _ = os.path.splitext(npy_file)
            txt_filepath = os.path.join(doc_dir_path, base_filename + ".txt")

            if not os.path.exists(txt_filepath):
                print(f"    Advertencia: No se encontró el archivo .txt '{txt_filepath}' correspondiente a '{npy_filepath}'. Omitiendo embedding.")
                continue
            
            try:
                embedding = np.load(npy_filepath)
                all_embeddings.append(embedding)
                fragment_paths_mapping.append(txt_filepath)
                total_embeddings_loaded += 1
            except Exception as e:
                print(f"    Error cargando embedding '{npy_filepath}': {e}. Omitiendo.")
                
    if not all_embeddings:
        print("  No se cargaron embeddings.")
        return None, None

    print(f"  Se cargaron {total_embeddings_loaded} embeddings.")
    return np.array(all_embeddings, dtype='float32'), fragment_paths_mapping


def build_and_save_faiss_index(embeddings_matrix, output_index_path: str):
    """
    Construye un índice FAISS a partir de la matriz de embeddings y lo guarda.
    """
    if embeddings_matrix is None or embeddings_matrix.size == 0:
        print("  No hay embeddings para construir el índice.")
        return False

    dimensionality = embeddings_matrix.shape[1]
    print(f"  Dimensionalidad de los embeddings: {dimensionality}")

    try:
        index = faiss.IndexFlatL2(dimensionality)
        index.add(embeddings_matrix)
        print(f"  Índice FAISS construido. Número total de vectores en el índice: {index.ntotal}")
        
        faiss.write_index(index, output_index_path)
        print(f"  Índice FAISS guardado en: {output_index_path}")
        return True
    except Exception as e:
        print(f"  Error construyendo o guardando el índice FAISS: {e}")
        return False

def save_mapping_file(fragment_mapping: list, output_mapping_path: str):
    """
    Guarda la lista de mapeo de fragmentos en un archivo JSON.
    """
    if not fragment_mapping:
        print("  No hay mapeo de fragmentos para guardar.")
        return False
        
    try:
        with open(output_mapping_path, 'w', encoding='utf-8') as f:
            json.dump(fragment_mapping, f, indent=4)
        print(f"  Mapeo de fragmentos guardado en: {output_mapping_path}")
        return True
    except Exception as e:
        print(f"  Error guardando el archivo de mapeo JSON: {e}")
        return False

def main():
    print("Iniciando la construcción del índice FAISS y el mapeo de fragmentos...")

    # 1. Cargar embeddings y crear mapeo
    embeddings_matrix, fragment_mapping = load_embeddings_and_create_mapping(LEGAL_CORPUS_DIR)

    if embeddings_matrix is None or fragment_mapping is None:
        print("Proceso detenido debido a errores en la carga de embeddings o creación de mapeo.")
        return

    # 2. Construir y guardar índice FAISS
    if not build_and_save_faiss_index(embeddings_matrix, OUTPUT_INDEX_FILE):
        print("Proceso detenido debido a errores en la construcción o guardado del índice FAISS.")
        return
        
    # 3. Guardar archivo de mapeo
    if not save_mapping_file(fragment_mapping, OUTPUT_MAPPING_FILE):
        print("Error al guardar el archivo de mapeo.")
        return
        
    print("\nConstrucción del índice y guardado de mapeo completados exitosamente.")

if __name__ == '__main__':
    # Configurar argparse si se desea flexibilidad para las rutas de entrada/salida.
    # Por ahora, se usan las constantes definidas.
    # parser = argparse.ArgumentParser(description="Construye un índice FAISS y un mapeo para fragmentos legales.")
    # args = parser.parse_args()
    main()
