import requests
from bs4 import BeautifulSoup as bs
from utils import *
from db.schemas import *
from collections import deque
from db.database import *
from typing import Iterable

seed_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
backup_url = 'https://comp4321-hkust.github.io/testpages/testpage.htm'
max_page = 30
remove_cyclic_relationship: bool = True

def fetch_page(url: str) -> tuple[Any, str] | None:
    try:
        print(f'Fetching {url}...')
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()
        print(f'Finish fetching {url}...')
        return response.headers, response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        print(f'Unknown error: {e}')
        return None

def extract_page_keywords(
    text: str, url: str, is_title: bool = True
    ) -> tuple[list[Index], set[str]]:

    keywords_dict = extract_keywords(text)
    # return index list, keywords
    return [
        Index(webpage=Webpage(url=url), keyword=Keyword(word=word), 
                      frequency=freq, is_title=is_title) 
        for word, freq in keywords_dict.items()
    ], set(keywords_dict.keys())
    
def extract_infos(parent_url: str, url_visited: set[str] = set()) -> \
    tuple[Webpage, list[Index], set[str], set[str]] | None: 
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
    child_links: set[str] = set()
    body = soup.get_text()
    links = soup.find_all('a', href=True)

    for link in links:
        link = link['href']
        link = normalize_url(link, parent_url)
        if link is not None and (not remove_cyclic_relationship or link not in url_visited): 
            child_links.add(link)

    title_indexes, title_keywords = extract_page_keywords(title, url=parent_url, is_title=True)
    body_indexes, body_keywords = extract_page_keywords(body, url=parent_url, is_title=False)

    keywords: set[str] = title_keywords.union(body_keywords)
    indexes: list[Index] = title_indexes + body_indexes

    return Webpage(
        url=parent_url, title=title, size=size, is_active=True, is_crawled=True,
        last_modified_date=str_to_date(last_modified_date), 
    ), indexes, keywords, child_links

def save_to_db(
    webpage: Webpage,
    children: Iterable[str],
    indexes: Iterable[Index],
    keywords: Iterable[str],
    sess=Session(),
    delete_unfound_item: bool = False,
):
    parent_id = set_webpage(
        [webpage], db=sess, delete_unfounded_page=delete_unfound_item
    )[webpage.url]

    if len(children) > 0:
        child_pages = [Webpage(
            url=url, is_crawled=False, is_active=False
        ) for url in children]

        child_ids = set_webpage(child_pages, ignore=True, db=sess, 
            delete_unfounded_page=delete_unfound_item).values()
        relation_list: set[Relationship] = set()

        for child_id in child_ids:
            relation_list.add(Relationship(
                parent_id=parent_id,
                child_id=child_id,
                is_active=True
            ))
        set_relationship(
            relation_list, db=sess,
            delete_unfounded_relationship=delete_unfound_item
        )
    
    if len(keywords) > 0 and len(indexes) > 0:
        word_id_dict = set_keyword(keywords, db=sess)    
        index_list: set[Index] = set()

        for index in indexes:
            index_list.add(Index(
                webpage_id=parent_id,
                word_id=word_id_dict[index.keyword.word],
                frequency=index.frequency,
                is_title=index.is_title,
            ))
        set_index(
            index_list, db=sess, 
            delete_unindexed_words=delete_unfound_item
        )

def bfs_crawl(
    seed_url: str = seed_url, 
    backup_url: str = backup_url,
    max_page: int = max_page,
    delete_unfounded_item: bool = False,
):

    url_visited: set[str] = set()
    url_queue = deque([seed_url])
    inactive_url = set()
    page_count = 0

    while url_queue and page_count < max_page:
        url = url_queue.popleft()
        if url in url_visited: continue

        page_info = extract_infos(url, url_visited)
        if page_info is None: 
            if url == seed_url: url_queue.append(backup_url)
            inactive_url.add(url)
            url_visited.add(url)
            continue

        webpage, indexes, keywords, child_links = page_info
        with Session() as sess:
            save_to_db(
                webpage=webpage,
                indexes=indexes,
                keywords=keywords,
                children=child_links,
                sess=sess,
                delete_unfound_item=delete_unfounded_item
            )
        
        url_visited.add(url)
        if len(url_queue) + page_count < max_page: url_queue.extend(child_links)
        page_count += 1

if __name__ == '__main__':
    create_database(restore=True)
    bfs_crawl()
    with Session() as sess:
        write_webpage_infos(db=sess, write_parent=False, limit=10)