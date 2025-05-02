from urllib.parse import urlparse
import os
from datetime import datetime
from typing import Any, Callable
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from rake_nltk import Rake
import nltk, string

def is_url_valid(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
# pip install sqlalchemy requests nltk rake-nltk beautifulsoup4 --user
def str_to_date(date: str): return datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
    
def normalize_url(url: str, parent_url: str) -> str | None:
    url = url.strip()
    parsed_url = urlparse(url)

    # absolute path
    if parsed_url.netloc != '' and parsed_url.scheme != '': 
        return url if is_url_valid(url) else None
    
    parent_url = parent_url.strip()
    if not is_url_valid(parent_url): return None
    parsed_parent_url = urlparse(parent_url)

    norm_link = None
    relative_path = parsed_url.path
    # relative path with leading double slash
    if parsed_url.netloc != '' and parsed_url.scheme == '':
        norm_link = f'{parsed_parent_url.scheme}:{parsed_url.netloc}{relative_path}'
    # relative path with leading single slash
    elif relative_path.startswith('/'):
        norm_link = f'{parsed_parent_url.scheme}://{parsed_parent_url.netloc}{relative_path}'
    else:
        path = None
        if parent_url.endswith('/'): path = f'{parsed_parent_url.path}{relative_path}'
        else: path = f'{os.path.dirname(parsed_parent_url.path)}/{relative_path}'
        path = os.path.normpath(path).replace('\\', '/')
        norm_link = f'{parsed_parent_url.scheme}://{parsed_parent_url.netloc}{path}'

    return norm_link if is_url_valid(norm_link) else None

stopword = None
def get_stopwords() -> set[str]:
    global stopword
    if stopword is None:
        with open('server/stopwords.txt', 'r') as f:
            stopword = {line.strip() for line in f.readlines()}

    return stopword

nltk.download('punkt')
stemmer = PorterStemmer()
rake = Rake()
def extract_keywords(text: str) -> dict[str, int]:
    global stemmer, rake
    # remove punctuation
    text = ''.join([c for c in text if c not in string.punctuation])
    # Convert to lower case
    words: str = text.lower().strip()
    # Tokenize words
    words: list[str] = word_tokenize(words)
    # Remove stop words and stem words
    stopwords = get_stopwords()
    words: list[str] = [stemmer.stem(word.strip()) for word in words if word not in stopwords and len(word) > 0]
    # Count word frequencies
    word_counts = Counter(words)
    # Extract phrasal words
    rake.extract_keywords_from_text(text)
    phrases = rake.get_ranked_phrases()
    output: dict[str, int] = dict()

    for phrase in phrases:
        if len(phrase) <= 0: continue
        w = [stemmer.stem(word.strip()) for word in str(phrase).split(' ') if word not in stopwords and len(word) > 0]
        
        # only select phrase with 2-3 words
        if len(w) <= 1 or len(w) > 3: continue
        freq = min([word_counts.get(a, 0) for a in w])
        if freq <= 0: continue
        output[' '.join(w)] = freq

    frequencies = {**output, **word_counts}

    return frequencies

def merge_dict(a: dict, b: dict, func: Callable[[Any, Any], Any]) -> dict:
    n = dict()
    for k, v in a.items():
        if k in b:
            t = func(v, b[k])
            if t == None: continue
            n[k] = t
        else:
            t = func(v, None)
            if t == None: continue
            n[k] = t
    for k, v in b.items():
        if k not in n:
            t = func(None, v)
            if t == None: continue
            n[k] = t
    return n

def find_str_index(s: str, sub: str) -> set[int]:
    """Find all occurrences of a substring in a string and return their starting indices."""
    indices = set()
    start = 0
    while True:
        start = s.find(sub, start)
        if start == -1:
            break
        indices.add(start)
        start += len(sub)  # Move past the last found index
    return indices

def substring_probability(substring: str, string: str) -> tuple:
    """
    Finds the occurrence of substring A in string S and computes the probability of finding A in S.
    
    :param A: Substring to find
    :param S: String in which to search
    :return: Tuple containing (count of A in S, probability of finding A in S)
    """
    if not substring or not string or len(substring) > len(string):
        return (0, 0.0)
    
    count = string.count(substring)
    total_possible_substrings = len(string) - len(substring) + 1
    probability = count / total_possible_substrings if total_possible_substrings > 0 else 0.0
    
    return probability