import spacy
import math
import re
import argparse
import sys
from pathlib import Path


# tokenizador
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Error: Model not found.", file=sys.stderr)
    print("Please run: python -m spacy download en_core_web_sm", file=sys.stderr)
    sys.exit(1)

def clean_markdown(md_text):
    """
    limpiar formato Markdown .
    """
    text = re.sub(r'^#+\s+', '', md_text, flags=re.MULTILINE) # Headers
    text = re.sub(r'\*\*|__|\*|_|`', '', text) # Bold/Italic/Code
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text) # Links
    text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text) # Images
    text = re.sub(r'\s+', ' ', text).strip() # Whitespace
    return text

def get_spacy_tokens(text):
    """
    Obtiene tokens.
    """

    nlp.max_length = 5000000
    doc = nlp(text)
    
    tokens = [token.text.lower() for token in doc if token.is_alpha]
    
    return tokens


def calculate_distinct_l_n(text, n=2):
    # limpiar md
    cleaned_text = clean_markdown(text)
    
    # tokenización
    tokens = get_spacy_tokens(cleaned_text)
    word_count = len(tokens)
    
    if word_count == 0:
        return 0.0, 0

    # ngramas
    ngrams_list = list(zip(*[tokens[i:] for i in range(n)]))
    
    total_ngrams = len(ngrams_list)
    if total_ngrams == 0:
        return 0.0, word_count
    
    unique_ngrams = len(set(ngrams_list))
    distinct_l_n = (unique_ngrams / total_ngrams) * (1 + math.log(word_count))
    
    return distinct_l_n, word_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcula la métrica DistinctL-n para un archivo Markdown.")
    parser.add_argument("filepath", type=str, help="Ruta al archivo .md")
    
    args = parser.parse_args()

    file_path = Path(args.filepath)

    if not file_path.exists():
        print(f"Error: El archivo '{file_path}' no existe.", file=sys.stderr)
        sys.exit(1)
        
    if not file_path.is_file():
        print(f"Error: '{file_path}' no es un archivo válido.", file=sys.stderr)
        sys.exit(1)

    try:
        content = file_path.read_text(encoding="utf-8")
        
        metric_val_1, token_count_1 = calculate_distinct_l_n(content, n=1)
        metric_val_3, token_count_3 = calculate_distinct_l_n(content, n=3)
        metric_val_4, token_count_4 = calculate_distinct_l_n(content, n=4)
        
        print(f"DistinctL-1: {metric_val_1:.4f}")
        print(f"Total Tokens: {token_count_1}")

        print(f"DistinctL-3: {metric_val_3:.4f}")
        print(f"Total Tokens: {token_count_3}")

        print(f"DistinctL-4: {metric_val_4:.4f}")
        print(f"Total Tokens: {token_count_4}")

    except Exception as e:
        print(f"Error inesperado al procesar el archivo: {e}", file=sys.stderr)
        sys.exit(1)
