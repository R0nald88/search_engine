import requests
from bs4 import BeautifulSoup as bs
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import nltk
from utils import *
from db.schemas import *
from collections import deque, Counter
from db.database import *

seed_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
backup_url = 'https://comp4321-hkust.github.io/testpages/testpage.htm'
max_page = 30
timeout = 15
stemmer = PorterStemmer()
tokenize_keyword: bool = True
if tokenize_keyword: nltk.download('punkt')

def fetch_page(url: str, timeout: int = timeout) -> tuple[str, str] | None:
    try:
        print(f'Fetching {url}...')
        response = requests.get(url, allow_redirects=True, timeout=timeout)
        response.raise_for_status()
        print(f'Finish fetching {url}...')
        return response.headers, response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        print(f'Unknown error: {e}')
        return None

def extract_keywords(
    text: str, url: str, is_title: bool = True, 
    tokenize_keyword: bool = tokenize_keyword
    ) -> tuple[list[Index], list[str]]:
    # return index list, keywords

    global stemmer

    # Convert to lower case
    words: str = text.lower().strip()
    # Tokenize words
    try:
        if not tokenize_keyword: raise Exception()
        words: list[str] = word_tokenize(words)
    except:
        words: list[str] = str(words).split()
    # Remove stop words and stem words
    stopwords = get_stopwords()
    words: list[str] = [stemmer.stem(word.strip()) for word in words if word not in stopwords]
    # Count word frequencies
    word_counts = Counter(words)
    # TODO: Support phrases

    return [
        Index(webpage=Webpage(url=url), keyword=Keyword(word=word), 
                      frequency=freq, is_title=is_title) 
        for word, freq in word_counts.items()
    ], list(word_counts.keys())
    
def extract_infos(parent_url: str) -> tuple[
    Webpage, list[tuple[str, str]], list[Index],
    list[str], list[str]] | None: 
    # retrun webpage, parent-child relationship, index list, keywords, children links

    info = fetch_page(parent_url)
    if info is None: return None

    headers, page = info
    soup = bs(page, 'html.parser')

    # Extract basic infos
    last_modified_date = headers.get('Last-Modified', headers.get('Date', ''))
    size = headers.get('Content-Length', len(page))
    title = soup.title.string if soup.title else ''

    # Extract child links
    child_links: list[str] = []
    relationship: list[tuple[str, str]] = []
    body = soup.get_text()
    links = soup.find_all('a', href=True)

    for link in links:
        link = link['href']
        link = normalize_url(link, parent_url)
        if link is not None: 
            child_links.append(link)
            relationship.append((parent_url, link))

    title_indexes, title_keywords = extract_keywords(title, url=parent_url, is_title=True)
    body_indexes, body_keywords = extract_keywords(body, url=parent_url, is_title=False)

    keywords: list[str] = title_keywords + body_keywords
    indexes: list[Index] = title_indexes + body_indexes

    return Webpage(
        url=parent_url, title=title, size=size, is_active=True,
        last_modified_date=str_to_date(last_modified_date), 
    ), relationship, indexes, keywords, child_links

def save_to_db(
    webpages: list[Webpage],
    inactive_links: list[str],
    relationships: list[tuple[str, str]],
    indexes: list[Index],
    keywords: list[str],
    sess=Session(),
    delete_unfound_item: bool = False,
    ):
    
    page_id_dict = set_webpage(
        webpages, db=sess, delete_unfounded_page=delete_unfound_item, 
        inactive_links=inactive_links)
    word_id_dict = set_keyword(keywords, db=sess)

    if not delete_unfound_item:
        result: list[tuple[int, str]] = sess.query(Webpage.webpage_id, Webpage.url).all()
        page_id_dict = {r[1]: r[0] for r in result}

    relation_list: list[Relationship] = []
    index_list: list[Index] = []
    available_page = list(page_id_dict.keys())
    available_word = list(word_id_dict.keys())

    for parent, child in relationships:
        if parent in available_page and child in available_page:
            parent_id = page_id_dict[parent]
            child_id = page_id_dict[child]
            relation_list.append(Relationship(
                parent_id=parent_id,
                child_id=child_id,
                is_active=True
            ))
    set_relationship(relation_list, db=sess, delete_unfounded_relationship=delete_unfound_item)

    for index in indexes:
        page = index.webpage.url
        word = index.keyword.word
        if page in available_page and word in available_word:
            page_id = page_id_dict[page]
            word_id = word_id_dict[word]
            index_list.append(Index(
                webpage_id=page_id,
                word_id=word_id,
                frequency=index.frequency,
                is_title=index.is_title,
            ))
    set_inverted_index(index_list, db=sess, delete_unindexed_words=delete_unfound_item)

def bfs_crawl(
    seed_url: str = seed_url, 
    backup_url: str = backup_url,
    max_page: int = max_page) -> tuple[
    list[Webpage], list[str], list[tuple[str, str]], list[Index], list[str]]:
    # return list of webpages, inactive_links, relationships, indexes, keywords

    url_visited = set()
    url_queue = deque([seed_url])
    webpages_list: list[Webpage] = []
    relationships_list: list[tuple[str, str]] = []
    indexes_list: list[Index] = []
    keywords_list: list[str] = []
    inactive_url = set()
    page_count = 0

    while url_queue and page_count < max_page:
        url = url_queue.popleft()
        if url in url_visited: continue

        page_info = extract_infos(url)
        if page_info is None: 
            if url == seed_url: url_queue.append(backup_url)
            inactive_url.add(url)
            url_visited.add(url)
            continue

        webpage, relationship, indexes, keywords, child_links = page_info
        webpages_list.append(webpage)
        relationships_list += relationship
        keywords_list += keywords
        indexes_list += indexes
        url_visited.add(url)
        print(url)
        if len(url_queue) + page_count < max_page: url_queue.extend(child_links)
        page_count += 1

    return webpages_list, list(inactive_url), relationships_list, indexes_list, keywords_list

def crawl_to_db(
    seed_url: str = seed_url, 
    backup_url: str = backup_url,
    max_page: int = max_page,
    restore: bool = False,
    delete_unfound_item: bool = False) -> None: 

    webpages, inactive_links, relationships, indexes, keywords = bfs_crawl(
        seed_url, max_page=max_page, backup_url=backup_url
    )

    with Session() as sess:
        create_database(restore=restore)
        save_to_db(
            sess=sess, delete_unfound_item=delete_unfound_item,
            webpages=webpages, inactive_links=inactive_links,
            relationships=relationships, indexes=indexes,
            keywords=keywords
        )

if __name__ == '__main__':
    crawl_to_db(restore=True)
    with Session() as sess:
        write_webpage_infos(10, db=sess)