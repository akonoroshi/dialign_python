import re
import spacy

nlp = spacy.load("en_core_web_sm")

def tokenize(text):
    """
    Tokenize the text using spacy.

    Args:
        text (str): The text to tokenize.
    
    Returns:
        list: The list of tokens.
    """
    doc = nlp(re.sub(r'\[.*\]', '', text).replace('_', ''))
    return [token.text for token in doc]