from urllib.parse import urlparse
import os
from datetime import datetime

def is_url_valid(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

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
            stopword = set([line.strip() for line in f.readlines()])

    return stopword