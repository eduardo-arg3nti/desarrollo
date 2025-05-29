import os
import docx
import PyPDF2
from pdf2image import convert_from_path
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract

# Moved Tesseract/Poppler info to main block or a setup function if needed globally.

def _inform_tesseract_installation():
    """Prints information about Tesseract installation requirements."""
    print("INFO: For PDF and image text extraction, Tesseract OCR needs to be installed on your system.")
    print("If not installed, please install it using: sudo apt-get install tesseract-ocr")
    print("You might also need to install poppler-utils for pdf2image: sudo apt-get install poppler-utils")

def extract_text_from_txt(file_path):
    """Extracts text from a .txt file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error processing .txt file: {e}"

def extract_text(file_path):
    """
    Loads a file and extracts text from it based on its extension.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension == '.txt':
        return extract_text_from_txt(file_path)
    # Add other file types later
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    elif file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file_path)
    else:
        return "Error: Unsupported file type."

def extract_text_from_docx(file_path):
    """Extracts text from a .docx file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error processing .docx file: {e}"

def extract_text_from_pdf(file_path):
    """Extracts text from a .pdf file. Tries direct extraction first, then OCR if needed."""
    try:
        text = ""
        # Try direct text extraction
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if reader.is_encrypted:
                try:
                    reader.decrypt('') # Try with empty password
                except Exception as e:
                    return f"Error: Could not decrypt PDF file. {e}"

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # If direct extraction yields little or no text, try OCR
        # Define "little text" as less than, say, 20 characters for a multi-page doc or if pages exist but no text
        # This threshold might need adjustment.
        if len(text.strip()) < 20 and len(reader.pages) > 0:
            print(f"INFO: Direct text extraction from {file_path} yielded little text. Attempting OCR.")
            try:
                images = convert_from_path(file_path)
                ocr_text = ""
                for i, image in enumerate(images):
                    # Save pages as images and then perform OCR
                    # page_image_path = f"temp_page_{i}.png"
                    # image.save(page_image_path, "PNG")
                    ocr_text += pytesseract.image_to_string(image) + "\n"
                    # os.remove(page_image_path) # Clean up temp image
                text = ocr_text
            except Exception as ocr_error:
                return f"Error during PDF OCR: {ocr_error}. (Make sure Tesseract and poppler-utils are installed and in PATH)"
        
        if not text.strip() and not len(reader.pages): # if no pages and no text
             return "Error: PDF file seems empty or unreadable."
        elif not text.strip() and len(reader.pages) > 0: # if pages but no text extracted
            return "Warning: PDF contains pages but no text could be extracted directly or via OCR."


        return text.strip() if text else "No text found in PDF."

    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error processing .pdf file: {e}"

def extract_text_from_image(file_path):
    """Extracts text from an image file (.png, .jpg, .jpeg) using Tesseract OCR."""
    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        return text.strip() if text else "No text found in image."
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        # Catching pytesseract.TesseractNotFoundError explicitly would be good if we were sure of the exception type
        if "Tesseract is not installed or not in your PATH" in str(e):
             return f"Error processing image file: {e}. Make sure Tesseract OCR is installed and in your PATH."
        return f"Error processing image file: {e}"

if __name__ == '__main__':
    _inform_tesseract_installation() # Inform when script is run directly
    # Create dummy files for testing
    if not os.path.exists('test_files'):
        os.makedirs('test_files')
    with open('test_files/sample.txt', 'w') as f:
        f.write("This is a sample text file.")
    # Create a dummy docx for testing
    doc = docx.Document()
    doc.add_paragraph("This is a sample DOCX file.")
    doc.save('test_files/sample.docx')
    # Create a dummy PDF for testing (text-based)
    from reportlab.pdfgen import canvas
    c = canvas.Canvas("test_files/sample.pdf")
    c.drawString(100, 750, "This is a sample PDF document for testing text extraction.")
    c.save()
    # Create a dummy PDF (image-based) - for now, we'll just copy the text one
    # A true image PDF would require a different creation process (e.g. scanning)
    # For testing OCR, we will rely on the image extraction part later.
    # For now, pdf_ocr_test.pdf will be the same as sample.pdf
    # We can manually create an image-only PDF later if needed for more robust testing.
    c_img = canvas.Canvas("test_files/sample_image.pdf")
    # Simulate an image pdf by just adding an image - pdf2image will convert this
    # For simplicity, we won't actually embed an image that pytesseract can read without OCR for this test
    # We'll test OCR with actual image files.
    try:
        # Create a dummy png for testing image embedding in PDF
        img_temp = Image.new('RGB', (60, 30), color = 'red')
        img_temp.save('test_files/dummy_for_pdf.png')
        c_img.drawImage('test_files/dummy_for_pdf.png', 100, 600)
    except Exception as e:
        print(f"Could not create dummy image for PDF: {e}")
    c_img.drawString(100, 750, "This PDF is intended for OCR test if direct extraction fails.")
    c_img.save()


    # Test .txt
    print(f"\n--- Testing TXT ---")
    print(f"Text from TXT: {extract_text('test_files/sample.txt')}")
    # Test .docx
    print(f"\n--- Testing DOCX ---")
    print(f"Text from DOCX: {extract_text('test_files/sample.docx')}")
    # Test .pdf
    print(f"\n--- Testing PDF ---")
    print(f"Text from PDF (text-based): {extract_text('test_files/sample.pdf')}")
    # The sample_image.pdf currently doesn't have actual image text for OCR,
    # it was more a test of the pdf2image pipeline.
    # print(f"Text from PDF (image-based - should trigger OCR or text): {extract_text('test_files/sample_image.pdf')}")

    # Create a dummy PNG for testing image OCR
    try:
        img = Image.new('RGB', (400, 100), color = 'white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # Simple text that Tesseract should recognize
        draw.text((10,10), "Hello from PNG image", fill='black')
        img.save('test_files/sample.png')
        print(f"\n--- Testing Image (PNG) ---")
        print(f"Text from PNG: {extract_text('test_files/sample.png')}")
    except Exception as e:
        print(f"Error creating or testing sample PNG: {e}")

    # Create a dummy zip for testing unsupported file type
    with open('test_files/unsupported.zip', 'w') as f:
        f.write("dummy zip content")

    print(f"\n--- Testing Error Cases ---")
    print(f"Text from non_existent.txt: {extract_text('test_files/non_existent.txt')}")
    print(f"Text from unsupported.zip: {extract_text('test_files/unsupported.zip')}")
