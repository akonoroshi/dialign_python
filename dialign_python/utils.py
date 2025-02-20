import re
import spacy

nlp = spacy.load("en_core_web_sm")

def tokenize(text):
    doc = nlp(re.sub(r'\[.*\]', '', text).replace('_', ''))
    return [token.text for token in doc]