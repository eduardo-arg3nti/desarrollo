import os
import argparse
import numpy as np
import faiss
import json
from sentence_transformers import SentenceTransformer
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# --- Configuración ---
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
FAISS_INDEX_FILE = "legal_corpus.index"
MAPPING_FILE = "legal_corpus_mapping.json"
NUM_RELEVANT_FRAGMENTS = 5 # k

def extract_text_from_image_path(image_path: str) -> str | None:
    """
    Extrae texto de un archivo de imagen (JPG, PNG) o de un PDF (que podría ser escaneado).
    """
    print(f"Extrayendo texto de: {image_path}...")
    try:
        _, extension = os.path.splitext(image_path)
        extension = extension.lower()

        if extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            return pytesseract.image_to_string(Image.open(image_path))
        elif extension == '.pdf':
            # Para PDF, convertir a imágenes y luego aplicar OCR a cada imagen.
            # Esto es similar a la lógica de OCR en pdf_extractor.py
            images = convert_from_path(image_path)
            full_text = ""
            for i, image in enumerate(images):
                print(f"  Procesando página {i+1} del PDF...")
                full_text += pytesseract.image_to_string(image) + "\n"
            return full_text
        else:
            print(f"  Tipo de archivo no soportado para OCR directa: {extension}")
            return None
    except Exception as e:
        print(f"  Error durante la extracción de texto (OCR) de '{image_path}': {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Busca fragmentos legales relevantes a partir del texto de una imagen.")
    parser.add_argument("image_path", help="Ruta al archivo de imagen (ej. .png, .jpg, .pdf).")
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: El archivo de imagen '{args.image_path}' no fue encontrado.")
        return

    # 1. Extraer texto de la imagen
    query_text = extract_text_from_image_path(args.image_path)
    if not query_text or not query_text.strip():
        print("No se pudo extraer texto discernible de la imagen o el texto está vacío.")
        return
    print(f"Texto extraído de la imagen:\n---\n{query_text[:500]}...\n---")

    # 2. Cargar modelo y generar embedding para el texto extraído
    print(f"Cargando el modelo '{MODEL_NAME}'...")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error crítico al cargar el modelo '{MODEL_NAME}': {e}")
        return
    print("Modelo cargado.")

    print("Generando embedding para el texto de la imagen...")
    try:
        query_embedding = model.encode([query_text])
    except Exception as e:
        print(f"Error generando embedding para el texto de la imagen: {e}")
        return
    print("Embedding de la consulta generado.")

    # 3. Cargar índice FAISS y mapeo
    if not os.path.exists(FAISS_INDEX_FILE) or not os.path.exists(MAPPING_FILE):
        print(f"Error: Archivos de índice ('{FAISS_INDEX_FILE}') o mapeo ('{MAPPING_FILE}') no encontrados.")
        print("Asegúrate de haber ejecutado 'build_index.py' primero.")
        return

    print(f"Cargando índice FAISS desde '{FAISS_INDEX_FILE}'...")
    try:
        index = faiss.read_index(FAISS_INDEX_FILE)
    except Exception as e:
        print(f"Error cargando el índice FAISS: {e}")
        return
    
    print(f"Cargando mapeo de fragmentos desde '{MAPPING_FILE}'...")
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            fragment_mapping = json.load(f)
    except Exception as e:
        print(f"Error cargando el archivo de mapeo: {e}")
        return
    
    if index.ntotal == 0:
        print("El índice FAISS está vacío. No hay fragmentos contra los cuales buscar.")
        return
    if not fragment_mapping:
        print("El archivo de mapeo está vacío.")
        return
    if index.ntotal != len(fragment_mapping):
        print("Advertencia: El número de vectores en el índice FAISS no coincide con el número de entradas en el mapeo.")
        # Podría ser un error crítico dependiendo de la implementación, pero por ahora solo advertimos.

    print("Índice y mapeo cargados.")

    # 4. Búsqueda de Similitud
    print(f"Buscando los {NUM_RELEVANT_FRAGMENTS} fragmentos más similares...")
    try:
        # FAISS espera una matriz 2D para las búsquedas
        query_embedding_matrix = np.array(query_embedding, dtype='float32').reshape(1, -1)
        distances, indices = index.search(query_embedding_matrix, NUM_RELEVANT_FRAGMENTS)
    except Exception as e:
        print(f"Error durante la búsqueda FAISS: {e}")
        return

    if indices[0].size == 0 or (indices[0][0] == -1 and NUM_RELEVANT_FRAGMENTS > 0) : # FAISS puede devolver -1 si no hay vecinos
        print("No se encontraron fragmentos relevantes.")
        return

    # 5. Recuperación y Presentación de Resultados
    print(f"\n--- {NUM_RELEVANT_FRAGMENTS} Fragmentos Más Relevantes Encontrados ---")
    num_found = 0
    for i in range(len(indices[0])):
        idx = indices[0][i]
        dist = distances[0][i]

        if idx == -1: # En caso de que k sea mayor que el número de elementos en el índice
            continue
        num_found +=1

        try:
            fragment_path = fragment_mapping[idx]
            with open(fragment_path, 'r', encoding='utf-8') as f:
                fragment_content = f.read()
            
            print(f"\nFragmento #{num_found} (Índice: {idx}, Distancia: {dist:.4f})")
            print(f"Fuente: {fragment_path}")
            print("Contenido:")
            print("--------------------------------------------------")
            print(fragment_content.strip())
            print("--------------------------------------------------")

        except IndexError:
            print(f"\nError: Índice {idx} fuera de rango para el mapeo de fragmentos.")
        except FileNotFoundError:
            print(f"\nError: No se encontró el archivo de fragmento: {fragment_path}")
        except Exception as e:
            print(f"\nError recuperando o mostrando el fragmento {idx}: {e}")
            
    if num_found == 0:
         print("No se encontraron fragmentos relevantes válidos después de procesar los resultados.")


if __name__ == '__main__':
    main()
