def extract_text_from_txt(filepath):
    """
    Extracts text from a TXT file.

    Args:
        filepath (str): The path to the TXT file.

    Returns:
        str: The extracted text, or None if an error occurs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error extracting text from TXT file: {e}")
        return None
