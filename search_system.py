import os
import json
import re
from text_extractor.extractor import extract_text # Asumiendo que está en la misma raíz o PYTHONPATH

# Lista básica de stopwords en español
STOPWORDS_ES = set([
    "a", "actualmente", "acuerdo", "adelante", "ademas", "además", "afirmó", "agregó", "ahora", "ahí", "al", "algo", "alguna", "algunas", "alguno", "algunos", "alrededor", "ambos", "ante", "anterior", "antes", "apenas", "aproximadamente", "aquel", "aquella", "aquellas", "aquello", "aquellos", "aqui", "aquí", "arriba", "aseguró", "así", "atras", "aun", "aunque", "bajo", "bastante", "bien", "breve", "buen", "buena", "buenas", "bueno", "buenos", "cada", "casi", "cerca", "cierta", "ciertas", "cierto", "ciertos", "cinco", "comentó", "como", "cómo", "con", "conocer", "conseguimos", "conseguir", "considera", "consideró", "consigo", "consigue", "consiguen", "consigues", "contra", "cosas", "creo", "cual", "cuales", "cualquier", "cuando", "cuanto", "cuatro", "cuenta", "da", "dado", "dan", "dar", "de", "debe", "deben", "debido", "decir", "dejó", "del", "demás", "dentro", "desde", "después", "dice", "dicen", "dicho", "dieron", "diferente", "diferentes", "dijeron", "dijo", "dio", "donde", "dos", "durante", "e", "ejemplo", "el", "él", "ella", "ellas", "ello", "ellos", "embargo", "empleais", "emplean", "emplear", "empleas", "empleo", "en", "encima", "encuentra", "entonces", "entre", "era", "erais", "eramos", "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "estaba", "estabais", "estaban", "estabas", "estad", "estada", "estadas", "estado", "estados", "estais", "estamos", "estan", "estando", "estar", "estará", "estarán", "estarás", "estaré", "estaréis", "estaremos", "estaría", "estaríais", "estaríamos", "estarían", "estarías", "estas", "este", "esto", "estos", "estoy", "estuve", "estuviera", "estuvierais", "estuvieran", "estuvieras", "estuvieron", "estuviese", "estuvieseis", "estuviesen", "estuvieses", "estuvimos", "estuviste", "estuvisteis", "estuviéramos", "estuviésemos", "estuvo", "ex", "existe", "existen", "explicó", "expresó", "fin", "fue", "fuera", "fuerais", "fueran", "fueras", "fueron", "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos", "fuiste", "fuisteis", "general", "gran", "grandes", "gueno", "ha", "haber", "habrá", "habrán", "habrás", "habré", "habréis", "habremos", "habría", "habríais", "habríamos", "habrían", "habrías", "habéis", "había", "habíais", "habíamos", "habían", "habías", "hace", "haceis", "hacemos", "hacen", "hacer", "hacerlo", "haces", "hacia", "haciendo", "hago", "han", "has", "hasta", "hay", "haya", "hayamos", "hayan", "hayas", "hayáis", "he", "hecho", "hemos", "hicieron", "hizo", "hoy", "hube", "hubiera", "hubierais", "hubieran", "hubieras", "hubieron", "hubiese", "hubieseis", "hubiesen", "hubieses", "hubimos", "hubiste", "hubisteis", "hubiéramos", "hubiésemos", "hubo", "i", "igual", "incluso", "indicó", "informó", "intenta", "intentais", "intentamos", "intentan", "intentar", "intentas", "intento", "ir", "junto", "la", "lado", "largo", "las", "le", "lejos", "les", "llegó", "lleva", "llevar", "lo", "los", "luego", "lugar", "manera", "manifestó", "mas", "más", "mayor", "me", "mediante", "medio", "mejor", "mencionó", "menos", "menudo", "mi", "mia", "mias", "mientras", "mio", "mios", "mis", "misma", "mismas", "mismo", "mismos", "modo", "momento", "mucha", "muchas", "mucho", "muchos", "muy", "nada", "nadie", "ni", "ninguna", "ningunas", "ninguno", "ningunos", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "nueva", "nuevas", "nuevo", "nuevos", "nunca", "o", "ocho", "os", "otra", "otras", "otro", "otros", "para", "parece", "parte", "partir", "pasada", "pasado", "pero", "pesar", "poca", "pocas", "poco", "pocos", "podeis", "podemos", "poder", "podrá", "podrán", "podría", "podrían", "podríamos", "podríais", "podrías", "poner", "por", "porque", "posible", "pronto", "propia", "propias", "propio", "propios", "proximo", "próximo", "próximos", "pudo", "pueda", "puede", "pueden", "puedo", "pues", "q", "q.", "que", "qué", "quedó", "queremos", "quien", "quienes", "quiere", "quiza", "quizas", "quizá", "quizás", "realizado", "realizar", "realizó", "respecto", "sabe", "sabeis", "sabemos", "saben", "saber", "sabes", "se", "sea", "seamos", "sean", "seas", "segunda", "segundo", "según", "seis", "ser", "será", "serán", "serás", "seré", "seréis", "seremos", "sería", "seríais", "seríamos", "serían", "serías", "señaló", "si", "sí", "siempre", "siendo", "siete", "sigue", "siguiente", "sin", "sino", "sobre", "sois", "sola", "solamente", "solas", "solo", "sólo", "solos", "somos", "son", "soy", "sr", "sra", "sres", "su", "supuesto", "sus", "suya", "suyas", "suyo", "suyos", "tal", "también", "tampoco", "tan", "tanta", "tantas", "tanto", "tantos", "te", "tenDRá", "tendrá", "tendrán", "tendrás", "tendré", "tendréis", "tendremos", "tendría", "tendríais", "tendríamos", "tendrían", "tendrías", "tened", "teneis", "tenemos", "tener", "tenga", "tengamos", "tengan", "tengas", "tengo", "tengáis", "tenia", "tenida", "tenidas", "tenido", "tenidos", "teniendo", "tenéis", "tenía", "teníais", "teníamos", "tenían", "tenías", "tercera", "ti", "tiene", "tienen", "tienes", "toda", "todas", "todavía", "todo", "todos", "total", "trabaja", "trabajais", "trabajamos", "trabajan", "trabajar", "trabajas", "trabajo", "tras", "trata", "través", "tres", "tu", "tus", "tuve", "tuviera", "tuvierais", "tuvieran", "tuvieras", "tuvieron", "tuviese", "tuvieseis", "tuviesen", "tuvieses", "tuvimos", "tuviste", "tuvisteis", "tuviéramos", "tuviésemos", "tuvo", "tuya", "tuyas", "tuyo", "tuyos", "tú", "u", "ultimo", "un", "una", "unas", "uno", "unos", "usa", "usais", "usamos", "usan", "usar", "usas", "uso", "usted", "ustedes", "va", "vais", "valor", "vamos", "van", "varias", "varios", "vaya", "veces", "ver", "verdad", "verdadera", "verdadero", "vez", "vosotras", "vosotros", "voy", "vuestra", "vuestras", "vuestro", "vuestros", "y", "ya", "yo", "él", "éramos", "ésa", "ésas", "ése", "ésos", "ésta", "éstas", "éste", "éstos", "última", "últimas", "último", "últimos"
])


class SearchIndex:
    def __init__(self, index_file_path=None):
        self.inverted_index = {}  # {term: [doc_id1, doc_id2]}
        self.documents = {}       # {doc_id: file_path}
        self.next_doc_id = 0
        if index_file_path and os.path.exists(index_file_path):
            self.load_index(index_file_path)

    def _get_next_doc_id(self):
        self.next_doc_id += 1
        return self.next_doc_id

    def preprocess_text(self, text):
        if text is None:
            return []
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Eliminar puntuación
        tokens = text.split()
        # Eliminar stopwords
        tokens = [token for token in tokens if token not in STOPWORDS_ES and token.strip()]
        return tokens

    def add_document(self, file_path):
        # Primero, verificar si el extractor está disponible y funciona
        try:
            text = extract_text(file_path)
        except NameError:
            print("Error: text_extractor.extractor.extract_text no está disponible.")
            return None
        except Exception as e:
            print(f"Error extrayendo texto de {file_path}: {e}")
            return None

        if text is None or "Error:" in text : # Manejar errores de extracción
            print(f"No se pudo extraer texto de {file_path}. Mensaje: {text}")
            return None

        doc_id = self._get_next_doc_id()
        self.documents[doc_id] = file_path
        
        processed_tokens = self.preprocess_text(text)
        
        for token in processed_tokens:
            if token not in self.inverted_index:
                self.inverted_index[token] = []
            if doc_id not in self.inverted_index[token]: # Evitar duplicados si una palabra aparece muchas veces
                self.inverted_index[token].append(doc_id)
        return doc_id

    def search(self, query_string):
        processed_query = self.preprocess_text(query_string)
        if not processed_query:
            return []

        # Implementación de búsqueda AND: Documentos que contienen todos los términos
        # Obtener las listas de documentos para cada término de la consulta
        result_sets = []
        for term in processed_query:
            if term in self.inverted_index:
                result_sets.append(set(self.inverted_index[term]))
            else:
                # Si un término no está en el índice, ningún documento contendrá todos los términos
                return []
        
        if not result_sets:
            return []

        # Intersección de todos los conjuntos de documentos
        intersected_docs_ids = result_sets[0]
        for i in range(1, len(result_sets)):
            intersected_docs_ids.intersection_update(result_sets[i])
            if not intersected_docs_ids: # Si la intersección se vuelve vacía, parar
                return []
        
        return [self.documents[doc_id] for doc_id in list(intersected_docs_ids)]

    def save_index(self, index_file_path):
        data_to_save = {
            'inverted_index': self.inverted_index,
            'documents': self.documents,
            'next_doc_id': self.next_doc_id
        }
        try:
            with open(index_file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            print(f"Índice guardado en {index_file_path}")
        except Exception as e:
            print(f"Error al guardar el índice: {e}")

    def load_index(self, index_file_path):
        try:
            with open(index_file_path, 'r', encoding='utf-8') as f:
                data_loaded = json.load(f)
                self.inverted_index = data_loaded['inverted_index']
                # JSON guarda las claves de documents como strings, convertir a int
                self.documents = {int(k): v for k,v in data_loaded['documents'].items()}
                self.next_doc_id = data_loaded['next_doc_id']
            print(f"Índice cargado desde {index_file_path}")
        except FileNotFoundError:
            print(f"Archivo de índice no encontrado: {index_file_path}. Se iniciará con un índice vacío.")
            self.inverted_index = {}
            self.documents = {}
            self.next_doc_id = 0
        except Exception as e:
            print(f"Error al cargar el índice: {e}. Se iniciará con un índice vacío.")
            self.inverted_index = {}
            self.documents = {}
            self.next_doc_id = 0

if __name__ == '__main__':
    # --- Bloque de Prueba ---

    # Crear directorio para archivos de prueba y el índice
    if not os.path.exists('test_search_files'):
        os.makedirs('test_search_files')
    
    INDEX_FILE = 'test_search_files/my_index.json'

    # 0. Limpiar índice anterior si existe para pruebas limpias
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)

    # 1. Crear instancia de SearchIndex
    search_engine = SearchIndex() # Carga el índice si existe, o crea uno nuevo

    # 2. Crear archivos de prueba
    doc1_path = 'test_search_files/doc1.txt'
    with open(doc1_path, 'w', encoding='utf-8') as f:
        f.write("Este es el primer documento. Habla sobre Python y desarrollo web.")
    
    doc2_path = 'test_search_files/doc2.txt'
    with open(doc2_path, 'w', encoding='utf-8') as f:
        f.write("El segundo documento trata sobre inteligencia artificial y Python.")

    doc3_path = 'test_search_files/doc3.txt' # PDF sería más complejo de crear aquí sin reportlab
    with open(doc3_path, 'w', encoding='utf-8') as f:
        f.write("Un tercer texto que menciona la web y algún otro tema.") # Modificado para no tener 'Python'

    # 3. Añadir documentos
    print("\n--- Añadiendo documentos ---")
    id1 = search_engine.add_document(doc1_path)
    id2 = search_engine.add_document(doc2_path)
    id3 = search_engine.add_document(doc3_path)
    
    if id1: print(f"Documento '{doc1_path}' añadido con ID: {id1}")
    if id2: print(f"Documento '{doc2_path}' añadido con ID: {id2}")
    if id3: print(f"Documento '{doc3_path}' añadido con ID: {id3}")

    print("\nÍndice interno después de añadir:")
    # print("Inverted Index:", json.dumps(search_engine.inverted_index, indent=2, ensure_ascii=False))
    # print("Documents:", search_engine.documents)


    # 4. Realizar búsquedas
    print("\n--- Realizando búsquedas ---")
    query1 = "Python"
    results1 = search_engine.search(query1)
    print(f"Resultados para '{query1}': {results1}") # Esperado: [doc1.txt, doc2.txt]

    query2 = "desarrollo web"
    results2 = search_engine.search(query2)
    print(f"Resultados para '{query2}': {results2}") # Esperado: [doc1.txt, doc3.txt]

    query3 = "Python y web" # Búsqueda AND
    results3 = search_engine.search(query3)
    print(f"Resultados para '{query3}': {results3}") # Esperado: [doc1.txt]
    
    query4 = "inteligencia artificial"
    results4 = search_engine.search(query4)
    print(f"Resultados para '{query4}': {results4}") # Esperado: [doc2.txt]

    query5 = "documento inexistente en el índice"
    results5 = search_engine.search(query5)
    print(f"Resultados para '{query5}': {results5}") # Esperado: []

    # 5. Guardar el índice
    print("\n--- Guardando índice ---")
    search_engine.save_index(INDEX_FILE)

    # 6. Crear una nueva instancia y cargar el índice
    print("\n--- Cargando índice en una nueva instancia ---")
    search_engine_loaded = SearchIndex(index_file_path=INDEX_FILE)
    # print("Loaded Inverted Index:", json.dumps(search_engine_loaded.inverted_index, indent=2, ensure_ascii=False))
    # print("Loaded Documents:", search_engine_loaded.documents)


    # 7. Verificar que la búsqueda funciona después de cargar
    print("\n--- Realizando búsquedas con el índice cargado ---")
    results_loaded1 = search_engine_loaded.search("Python")
    print(f"Resultados para 'Python' (cargado): {results_loaded1}") # Esperado: [doc1.txt, doc2.txt]

    results_loaded2 = search_engine_loaded.search("Python y web")
    print(f"Resultados para 'Python y web' (cargado): {results_loaded2}") # Esperado: [doc1.txt]
    
    # Prueba adicional: añadir un documento después de cargar
    print("\n--- Añadiendo documento después de cargar ---")
    doc4_path = 'test_search_files/doc4.txt'
    with open(doc4_path, 'w', encoding='utf-8') as f:
        f.write("Cuarto documento sobre análisis de datos con Python.")
    id4 = search_engine_loaded.add_document(doc4_path)
    if id4: print(f"Documento '{doc4_path}' añadido con ID: {id4}")
    
    results_loaded3 = search_engine_loaded.search("análisis datos")
    print(f"Resultados para 'análisis datos' (después de añadir doc4): {results_loaded3}") # Esperado: [doc4.txt]
    
    results_loaded4 = search_engine_loaded.search("Python")
    print(f"Resultados para 'Python' (después de añadir doc4): {results_loaded4}") # Esperado: [doc1.txt, doc2.txt, doc4.txt] (el orden puede variar)


    # Limpieza opcional de archivos de prueba
    # print("\n--- Limpiando archivos de prueba ---")
    # for f_path in [doc1_path, doc2_path, doc3_path, doc4_path, INDEX_FILE]:
    #     if os.path.exists(f_path):
    #         os.remove(f_path)
    # if os.path.exists('test_search_files'):
    #     os.rmdir('test_search_files') # Solo si está vacío
    print("\n--- Fin de las pruebas ---")

print("INFO: Para que este script funcione, el módulo 'text_extractor' debe estar accesible.")
print("Asegúrate de que 'text_extractor/extractor.py' está en el mismo directorio o en el PYTHONPATH.")
print("También, recuerda que 'text_extractor' depende de varias bibliotecas (docx, PyPDF2, etc.) y Tesseract OCR.")

# Consideraciones adicionales:
# - Para PDFs, se necesitaría una biblioteca como reportlab para crearlos en las pruebas, o tener PDFs de muestra.
# - La normalización de texto (lematización/stemming) podría mejorar la búsqueda pero añade complejidad.
# - El ranking de resultados no está implementado (ej. TF-IDF).
# - El manejo de errores en `extract_text` es básico; podría ser más robusto.
# - Si `extract_text` devuelve un error (ej. "Error: File not found."), `add_document` actualmente lo trata como texto y lo indexaría.
#   Esto se ha mejorado con: `if text is None or "Error:" in text:`

# Mensajes informativos movidos al bloque __main__ o eliminados si son específicos del módulo importado
