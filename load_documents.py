import os
import argparse
import shutil
from text_extractor import extract_text # Asumiendo que text_extractor está accesible
from text_processor.chunking import chunk_text_by_paragraph

# Directorio base para almacenar los fragmentos procesados
OUTPUT_CORPUS_DIR = "legal_corpus"

def process_single_file(filepath: str):
    """
    Procesa un solo archivo: extrae texto, lo fragmenta y guarda los fragmentos.
    """
    print(f"Procesando archivo: {filepath}...")
    
    # 1. Extraer texto del archivo
    text_content = extract_text(filepath)
    
    if not text_content:
        print(f"No se pudo extraer texto de {filepath}. Omitiendo.")
        return

    # 2. Aplicar fragmentación por párrafos
    chunks = chunk_text_by_paragraph(text_content)
    
    if not chunks:
        print(f"No se generaron fragmentos para {filepath} (posiblemente vacío o solo espacios).")
        return

    # 3. Crear directorio de salida para los fragmentos
    base_filename = os.path.basename(filepath)
    filename_no_ext, _ = os.path.splitext(base_filename)
    
    # Crear un nombre de directorio seguro (reemplazar espacios o caracteres no deseados si es necesario)
    # Por ahora, usaremos el nombre de archivo sin extensión directamente.
    # Podríamos añadir un slugify más robusto si los nombres de archivo son complejos.
    sanitized_dirname = filename_no_ext.replace(" ", "_") 
    
    output_dir_for_file = os.path.join(OUTPUT_CORPUS_DIR, sanitized_dirname)
    
    if os.path.exists(output_dir_for_file):
        # Opción: limpiar directorio si ya existe para evitar fragmentos antiguos.
        # Por ahora, lo borraremos y recrearemos.
        # Alternativamente, se podría añadir un timestamp o un contador para evitar colisiones.
        print(f"Directorio de salida {output_dir_for_file} ya existe. Limpiando...")
        shutil.rmtree(output_dir_for_file)
    
    os.makedirs(output_dir_for_file, exist_ok=True)

    # 4. Guardar cada fragmento en un archivo .txt
    num_fragments = len(chunks)
    for i, chunk in enumerate(chunks):
        fragment_filename = f"fragment_{i+1:03}.txt" # Ej: fragment_001.txt
        fragment_filepath = os.path.join(output_dir_for_file, fragment_filename)
        try:
            with open(fragment_filepath, 'w', encoding='utf-8') as f:
                f.write(chunk)
        except Exception as e:
            print(f"Error al guardar el fragmento {fragment_filepath}: {e}")
            # Considerar si continuar o detenerse en caso de error de escritura.

    print(f"Archivo {filepath} procesado. Se generaron {num_fragments} fragmentos en {output_dir_for_file}.")


def main():
    parser = argparse.ArgumentParser(description="Procesa documentos legales (PDF, DOCX, TXT), los fragmenta por párrafos y guarda los fragmentos.")
    parser.add_argument("input_path", help="Ruta a un archivo de documento o a un directorio que contenga documentos.")
    
    args = parser.parse_args()
    
    input_path = args.input_path

    if not os.path.exists(input_path):
        print(f"Error: La ruta de entrada '{input_path}' no existe.")
        return

    # Crear el directorio base del corpus si no existe
    if not os.path.exists(OUTPUT_CORPUS_DIR):
        os.makedirs(OUTPUT_CORPUS_DIR)
        print(f"Directorio del corpus creado en: {OUTPUT_CORPUS_DIR}")

    if os.path.isfile(input_path):
        # Procesar un solo archivo
        # Verificar si es un tipo de archivo soportado por extract_text
        _, extension = os.path.splitext(input_path)
        if extension.lower() in ['.pdf', '.docx', '.txt']:
            process_single_file(input_path)
        else:
            print(f"Archivo {input_path} no es de un tipo soportado (PDF, DOCX, TXT). Omitiendo.")
            
    elif os.path.isdir(input_path):
        # Procesar todos los archivos en un directorio
        print(f"Procesando directorio: {input_path}")
        for item in os.listdir(input_path):
            item_path = os.path.join(input_path, item)
            if os.path.isfile(item_path):
                _, extension = os.path.splitext(item_path)
                if extension.lower() in ['.pdf', '.docx', '.txt']:
                    process_single_file(item_path)
                else:
                    print(f"Archivo {item_path} no es de un tipo soportado. Omitiendo.")
            else:
                print(f"Elemento {item_path} no es un archivo. Omitiendo.")
    else:
        print(f"Error: La ruta de entrada '{input_path}' no es un archivo ni un directorio válido.")

if __name__ == '__main__':
    # Para que esto funcione, text_extractor y text_processor deben estar en PYTHONPATH
    # o en el mismo directorio raíz.
    # Suponiendo que la estructura es:
    # ./load_documents.py
    # ./text_extractor/
    # ./text_processor/
    # Se puede ejecutar desde el directorio raíz.
    main()
