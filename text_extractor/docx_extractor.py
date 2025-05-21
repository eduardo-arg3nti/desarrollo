import docx

def extract_text_from_docx(filepath):
    """
    Extracts text from a DOCX file.

    Args:
        filepath (str): The path to the DOCX file.

    Returns:
        str: The extracted text, or None if an error occurs.
    """
    try:
        doc = docx.Document(filepath)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text from DOCX file: {e}")
        return None
