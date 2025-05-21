from PIL import Image, ImageDraw, ImageFont

def create_image(filename="test_image.png", text="Texto de prueba para OCR", size=(400, 100), bg_color="white", text_color="black"):
    try:
        # Intenta cargar una fuente, si falla, usa la fuente por defecto de Pillow
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 20)
        except IOError:
            print("Fuente DejaVuSans.ttf no encontrada, usando fuente por defecto.")
            font = ImageFont.load_default()
            
        img = Image.new('RGB', size, color = bg_color)
        d = ImageDraw.Draw(img)
        
        # Calcular la posición del texto para centrarlo (aproximadamente)
        # text_width, text_height = d.textsize(text, font=font) # textsize es obsoleto
        # Usa textbbox para versiones más nuevas de Pillow
        bbox = d.textbbox((0,0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size[0] - text_width) / 2
        y = (size[1] - text_height) / 2
        
        d.text((x,y), text, fill=text_color, font=font)
        img.save(filename)
        print(f"Imagen de prueba '{filename}' creada exitosamente.")
    except Exception as e:
        print(f"Error creando imagen de prueba: {e}")

if __name__ == '__main__':
    # Crear una imagen con texto que podría estar en nuestros documentos legales de prueba
    # El único fragmento actual es "legal_corpus/sample/fragment_001.txt" que contiene:
    # "Este es un archivo de prueba TXT.\nContiene texto simple para verificar la extracción.\nTiene múltiples líneas."
    # Vamos a usar una frase de ahí.
    create_image(filename="query_test_image.png", text="archivo de prueba TXT")
