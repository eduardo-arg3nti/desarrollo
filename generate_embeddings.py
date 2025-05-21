import os
import numpy as np
from sentence_transformers import SentenceTransformer
import argparse

# --- Configuración ---
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2' # Modelo recomendado
LEGAL_CORPUS_DIR = "legal_corpus" # Directorio base de los fragmentos

def generate_and_save_embedding(model, text_content: str, output_npy_filepath: str):
    """
    Genera un embedding para el texto dado y lo guarda como un archivo .npy.
    """
    try:
        embedding = model.encode([text_content])[0] # model.encode devuelve una lista de embeddings
        np.save(output_npy_filepath, embedding)
        # print(f"      Embedding guardado en: {output_npy_filepath}")
    except Exception as e:
        print(f"      Error generando o guardando embedding para {output_npy_filepath}: {e}")

def process_document_directory(model, doc_dir_path: str):
    """
    Procesa todos los fragmentos .txt en un directorio de documento específico.
    """
    print(f"  Procesando directorio de documento: {doc_dir_path}")
    
    fragment_files = [f for f in os.listdir(doc_dir_path) if f.endswith(".txt")]
    
    if not fragment_files:
        print(f"    No se encontraron archivos .txt en {doc_dir_path}.")
        return
    
    num_fragments_processed = 0
    for fragment_file in fragment_files:
        fragment_txt_filepath = os.path.join(doc_dir_path, fragment_file)
        base_filename, _ = os.path.splitext(fragment_file)
        output_npy_filepath = os.path.join(doc_dir_path, base_filename + ".npy")

        # print(f"    Procesando fragmento: {fragment_txt_filepath}")
        try:
            with open(fragment_txt_filepath, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            if not text_content.strip():
                # print(f"      Fragmento {fragment_txt_filepath} está vacío o solo contiene espacios. Omitiendo.")
                continue

            generate_and_save_embedding(model, text_content, output_npy_filepath)
            num_fragments_processed += 1
        except Exception as e:
            print(f"      Error leyendo el fragmento {fragment_txt_filepath}: {e}")
            
    print(f"    Se procesaron y guardaron embeddings para {num_fragments_processed} fragmentos en {doc_dir_path}.")


def main():
    print("Iniciando la generación de embeddings...")

    # 1. Cargar el modelo de SentenceTransformer
    print(f"Cargando el modelo '{MODEL_NAME}'... Esto puede tardar la primera vez.")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error crítico al cargar el modelo '{MODEL_NAME}': {e}")
        print("Asegúrate de tener conexión a internet si es la primera vez que usas este modelo.")
        return
    print("Modelo cargado exitosamente.")

    # 2. Verificar si el directorio legal_corpus existe
    if not os.path.exists(LEGAL_CORPUS_DIR):
        print(f"Error: El directorio '{LEGAL_CORPUS_DIR}' no fue encontrado.")
        print("Por favor, ejecuta primero el script 'load_documents.py' para generar los fragmentos.")
        return
    
    if not os.listdir(LEGAL_CORPUS_DIR):
        print(f"El directorio '{LEGAL_CORPUS_DIR}' está vacío.")
        return

    print(f"Recorriendo el corpus en: {LEGAL_CORPUS_DIR}")
    
    # 3. Recorrer los subdirectorios de documentos en legal_corpus
    for doc_dirname in os.listdir(LEGAL_CORPUS_DIR):
        doc_dir_path = os.path.join(LEGAL_CORPUS_DIR, doc_dirname)
        if os.path.isdir(doc_dir_path):
            process_document_directory(model, doc_dir_path)
        else:
            print(f"  Elemento '{doc_dirname}' no es un directorio. Omitiendo.")
            
    print("\nGeneración de embeddings completada.")

if __name__ == '__main__':
    # Configurar argparse si se desea flexibilidad, pero para este caso
    # los directorios están predefinidos según la tarea.
    # parser = argparse.ArgumentParser(description="Genera embeddings para fragmentos de texto en legal_corpus.")
    # args = parser.parse_args() # No se usan argumentos por ahora
    main()
