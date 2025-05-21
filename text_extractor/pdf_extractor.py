import PyPDF2
import pytesseract
from pdf2image import convert_from_path

def extract_text_from_pdf_direct(filepath):
    """
    Extracts text directly from a PDF file.

    Args:
        filepath (str): The path to the PDF file.

    Returns:
        str: The extracted text, or None if an error occurs.
    """
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text directly from PDF file: {e}")
        return None

def extract_text_from_pdf_ocr(filepath):
    """
    Extracts text from a PDF file using OCR.

    Args:
        filepath (str): The path to the PDF file.

    Returns:
        str: The extracted text, or None if an error occurs.
    """
    try:
        images = convert_from_path(filepath)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from PDF file using OCR: {e}")
        return None

def extract_text_from_pdf(filepath):
    """
    Extracts text from a PDF file.
    Tries direct extraction first, then OCR if direct extraction fails
    or returns too little text.

    Args:
        filepath (str): The path to the PDF file.

    Returns:
        str: The extracted text, or None if an error occurs.
    """
    direct_text = extract_text_from_pdf_direct(filepath)

    if direct_text and len(direct_text.strip()) > 100: # Threshold for 'significant text'
        return direct_text
    else:
        print("Direct text extraction insufficient, trying OCR...")
        return extract_text_from_pdf_ocr(filepath)
