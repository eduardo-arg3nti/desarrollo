import os

# Esta constante será usada por la función load_template
TEMPLATES_BASE_DIR = "templates"

def load_template(template_name: str) -> str | None:
    """
    Carga una plantilla de texto desde el directorio de plantillas.

    Args:
        template_name (str): El nombre de la plantilla (sin la extensión .txt).
                               Ej: "amparo_simple"
        base_dir (str): El directorio base donde se encuentra la carpeta de plantillas.
                        Por defecto es TEMPLATES_BASE_DIR.

    Returns:
        str | None: El contenido de la plantilla como una cadena, 
                    o None si la plantilla no se encuentra.
    """
    # Usar TEMPLATES_BASE_DIR definido globalmente para la ruta de las plantillas
    template_filename = f"{template_name}.txt"
    template_filepath = os.path.join(TEMPLATES_BASE_DIR, template_filename)

    if not os.path.isdir(TEMPLATES_BASE_DIR): # Verificar si el directorio base de plantillas existe
        print(f"Error: El directorio de plantillas '{TEMPLATES_BASE_DIR}' no existe o no es un directorio.")
        return None
        
    if not os.path.isfile(template_filepath):
        print(f"Error: La plantilla '{template_filepath}' no fue encontrada.")
        return None
    
    try:
        with open(template_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error leyendo la plantilla '{template_filepath}': {e}")
        return None

if __name__ == '__main__':
    print("Probando la carga de plantillas...")

    # Prueba 1: Cargar plantilla existente 'amparo_simple.txt'
    print("\n--- Cargando 'amparo_simple' ---")
    amparo_content = load_template("amparo_simple")
    if amparo_content:
        print("Plantilla 'amparo_simple' cargada exitosamente (primeros 100 caracteres):")
        print(amparo_content[:100] + "...")
    else:
        print("Fallo al cargar 'amparo_simple'.")

    # Prueba 2: Cargar plantilla existente 'carta_documento_simple.txt'
    print("\n--- Cargando 'carta_documento_simple' ---")
    carta_content = load_template("carta_documento_simple")
    if carta_content:
        print("Plantilla 'carta_documento_simple' cargada exitosamente (primeros 100 caracteres):")
        print(carta_content[:100] + "...")
    else:
        print("Fallo al cargar 'carta_documento_simple'.")

    # Prueba 3: Intentar cargar plantilla no existente
    print("\n--- Intentando cargar 'plantilla_inexistente' ---")
    inexistente_content = load_template("plantilla_inexistente")
    if inexistente_content:
        print("Plantilla 'plantilla_inexistente' cargada (esto no debería ocurrir).")
    else:
        print("Fallo al cargar 'plantilla_inexistente' (comportamiento esperado).")

    # Prueba 4: Intentar cargar si el directorio de plantillas no existe
    print("\n--- Intentando cargar con directorio de plantillas inválido temporalmente ---")
    
    # Guardar el nombre original del directorio de plantillas
    original_templates_dir_name = TEMPLATES_BASE_DIR 
    
    # Cambiar temporalmente el nombre del directorio base de plantillas a uno que no exista
    # Esto se hace modificando la variable global que usa la función.
    # No es la forma más elegante, pero para una prueba simple dentro de if __name__ == '__main__' es aceptable.
    # Una mejor forma sería pasar TEMPLATES_BASE_DIR como argumento a load_template.
    globals()['TEMPLATES_BASE_DIR'] = "directorio_inexistente_para_prueba"
    
    test_content_no_dir = load_template("amparo_simple")
    if test_content_no_dir:
        print("Plantilla cargada cuando el directorio no existe (esto no debería ocurrir).")
    else:
        print("Fallo al cargar plantilla cuando el directorio de plantillas no existe (comportamiento esperado).")
    
    # Restaurar el nombre original del directorio de plantillas
    globals()['TEMPLATES_BASE_DIR'] = original_templates_dir_name
    print(f"Nombre del directorio de plantillas restaurado a: {TEMPLATES_BASE_DIR}")
