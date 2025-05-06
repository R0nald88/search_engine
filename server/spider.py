from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Iterable
import requests
from bs4 import BeautifulSoup as bs
from sqlalchemy import text
from utils import *
import time
from db.database import *
from queue import Queue

url_visited: set[str] = set()
inactive_url = set()
page_count = 0
url_queue = Queue()
page_ids: set[int] = set()
word_ids: set[int] = set()

def fetch_page(url: str) -> tuple[Any, str, str, set[str]] | None:
    global url_visited, inactive_url, page_count, url_queue
    if url in url_visited: return None

    try:
        print(f'Fetching {url}...')
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()
        print(f'Finish fetching {url}...')

        page = response.text
        soup = bs(page, 'html.parser')
        child_links: set[str] = set()
        links = soup.find_all('a', href=True)
        url_visited.add(url)

        for link in links:
            link = link['href']
            link = normalize_url(link, url)
            if link is not None and (not remove_cyclic_relationship or link not in url_visited): 
                child_links.add(link)
                if url_queue.qsize() + page_count < max_page: url_queue.put(link)

        page_count += 1

        return response.headers, response.text, url, child_links
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        inactive_url.add(url)
        return None
    except Exception as e:
        print(f'Unknown error: {e}')
        inactive_url.add(url)
        return None

def extract_page_keywords(
    text: str, url: str, is_title: bool = True
    ) -> tuple[list[TitleIndex] | list[BodyIndex], set[str]]:

    keywords_dict, _ = extract_keywords(text, is_query=False)
    max_tf = max(keywords_dict.values())
    cls = TitleIndex if is_title else BodyIndex
    # return index list, keywords
    return [
        cls(
            webpage=Webpage(url=url), keyword=Keyword(word=word.strip()), 
            frequency=freq, normalized_tf = freq / max_tf 
        ) for word, freq in keywords_dict.items() if len(word.strip()) > 0
    ], set(keywords_dict.keys())
    
def extract_infos(
    parent_url: str, 
    info: tuple[Any, str] | None,
) -> tuple[Webpage, list[TitleIndex], list[BodyIndex], set[str]] | None: 
    # retrun webpage, parent-child relationship, index list, keywords, children links
    if info is None: return None

    headers, page = info
    soup = bs(page, 'html.parser')

    # Extract basic infos
    last_modified_date = headers.get('Last-Modified', headers.get('Date', ''))
    size = headers.get('Content-Length', len(page))
    title = soup.title.string if soup.title else ''

    # Extract child links
    body = soup.get_text()

    title_indexes, title_keywords = extract_page_keywords(title, url=parent_url, is_title=True)
    body_indexes, body_keywords = extract_page_keywords(body, url=parent_url, is_title=False)

    keywords: set[str] = title_keywords.union(body_keywords)

    return Webpage(
        url=parent_url, title=title, size=size, is_active=True, is_crawled=True,
        last_modified_date=str_to_date(last_modified_date), 
    ), title_indexes, body_indexes, keywords

def save_to_db_immediately(
    webpage: Webpage,
    children: Iterable[str],
    title_indexes: Iterable[TitleIndex],
    body_indexes: Iterable[BodyIndex],
    keywords: Iterable[str],
    sess=Session(),
    delete_unfound_item: bool = False,
) -> tuple[set[int], set[int]]:
    parent_id = set_webpage(
        [webpage], db=sess, delete_unfounded_page=delete_unfound_item
    )[webpage.url]
    page_ids = {parent_id}
    word_ids = set()

    if len(children) > 0:
        child_pages = [Webpage(
            url=url, is_crawled=False, is_active=False
        ) for url in children]

        set_webpage(child_pages, ignore=True, db=sess, 
            delete_unfounded_page=delete_unfound_item)
        child_ids = sess.query(Webpage.webpage_id).filter(Webpage.url.in_(children)).all()
        relation_list: set[Relationship] = set()

        for child_id in child_ids:
            relation_list.add(Relationship(
                parent_id=parent_id,
                child_id=child_id[0],
                is_active=True
            ))
            page_ids.add(child_id[0])

        set_relationship(
            relation_list, db=sess,
            delete_unfounded_relationship=delete_unfound_item
        )
    
    if len(keywords) > 0 and (len(title_indexes) > 0 or len(body_indexes) > 0):
        word_id_dict = set_keyword(keywords, db=sess)
        word_ids = set(word_id_dict.values())

        if len(title_indexes) > 0:
            index_list: set[TitleIndex] = set()

            for index in title_indexes:
                index_list.add(TitleIndex(
                    webpage_id=parent_id,
                    word_id=word_id_dict[index.keyword.word],
                    frequency=index.frequency,
                    normalized_tf=index.normalized_tf,
                ))
            set_title_index(
                index_list, db=sess, 
                delete_unindexed_words=delete_unfound_item
            )

        if len(body_indexes) > 0:
            index_list: set[BodyIndex] = set()

            for index in body_indexes:
                index_list.add(BodyIndex(
                    webpage_id=parent_id,
                    word_id=word_id_dict[index.keyword.word],
                    frequency=index.frequency,
                    normalized_tf=index.normalized_tf,
                ))
            set_body_index(
                index_list, db=sess, 
                delete_unindexed_words=delete_unfound_item
            )

    return page_ids, word_ids

def crawl_webpage(url: str, info: tuple[Any, str] | None, child_links: set[str]):
    global url_visited, inactive_url, page_ids, word_ids, url_queue, lock

    page_info = extract_infos(url, info)
    if page_info == None: 
        if url == seed_url: url_queue.put(backup_url)
        inactive_url.add(url)
        url_visited.add(url)
        return

    webpage, title_indexes, body_indexes, keywords = page_info
    
    lock.acquire()
    db = Session()
    p, w = save_to_db_immediately(
        webpage=webpage,
        title_indexes=title_indexes,
        body_indexes=body_indexes,
        keywords=keywords,
        children=child_links,
        sess=db,
        delete_unfound_item=delete_unfounded_item
    )
    db.commit()
    db.close()
    page_ids.update(p)
    word_ids.update(w)
    lock.release()

def bfs_crawl(max_page: int = max_page):
    global url_visited, inactive_url, page_count, page_ids, word_ids, url_queue
    url_queue.put(seed_url)

    def future_callback(future: Future[tuple[Any, str, str, set[str]] | None]):
        result = future.result()
        if result == None: return
        else: crawl_webpage(info=(result[0], result[1]), url=result[2], child_links=result[3])
            
    
    with ThreadPoolExecutor(max_workers=max_thread_worker*2) as executor:
        while page_count < max_page:
            try:
                url = url_queue.get(timeout=15)
                future = executor.submit(fetch_page, url)
                future.add_done_callback(fn=future_callback)
            except: break

    with Session() as sess:
        i = sess.query(func.count(Webpage.is_active)).filter(Webpage.is_crawled == True).scalar()
        print(f'Total {i} webpages crawled.')
    compute_pmi(word_ids=word_ids)
    compute_pagerank(page_ids=page_ids)

if __name__ == '__main__':
    time_start = time.time()
    create_database(restore=True)
    bfs_crawl()
    print('Time taken:', time.time() - time_start)