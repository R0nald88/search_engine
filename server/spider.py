import requests
from bs4 import BeautifulSoup as bs
from utils import *
from collections import deque
from db.database import *
from typing import Iterable

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
    ) -> tuple[list[TitleIndex] | list[BodyIndex], set[str]]:

    keywords_dict = extract_keywords(text)
    max_tf = max(keywords_dict.values())
    cls = TitleIndex if is_title else BodyIndex
    # return index list, keywords
    return [
        cls(
            webpage=Webpage(url=url), keyword=Keyword(word=word.strip()), 
            frequency=freq, normalized_tf = freq / max_tf 
        ) for word, freq in keywords_dict.items() if len(word.strip()) > 0
    ], set(keywords_dict.keys())
    
def extract_infos(parent_url: str, url_visited: set[str] = set(), 
    remove_cyclic_relationship: bool = remove_cyclic_relationship,) -> \
    tuple[Webpage, list[TitleIndex], list[BodyIndex], set[str], set[str]] | None: 
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

    return Webpage(
        url=parent_url, title=title, size=size, is_active=True, is_crawled=True,
        last_modified_date=str_to_date(last_modified_date), 
    ), title_indexes, body_indexes, keywords, child_links

def save_to_db(
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

def bfs_crawl(
    seed_url: str = seed_url, 
    backup_url: str = backup_url,
    max_page: int = max_page,
    remove_cyclic_relationship: bool = remove_cyclic_relationship,
    delete_unfounded_item: bool = delete_unfounded_item,
):

    url_visited: set[str] = set()
    url_queue = deque([seed_url])
    inactive_url = set()
    page_count = 0
    page_ids: set[int] = set()
    word_ids: set[int] = set()

    while url_queue and page_count < max_page:
        url = url_queue.popleft()
        if url in url_visited: continue

        page_info = extract_infos(url, url_visited, remove_cyclic_relationship=remove_cyclic_relationship)
        if page_info is None: 
            if url == seed_url: url_queue.append(backup_url)
            inactive_url.add(url)
            url_visited.add(url)
            continue

        webpage, title_indexes, body_indexes, keywords, child_links = page_info
        with Session() as sess:
            p, w = save_to_db(
                webpage=webpage,
                title_indexes=title_indexes,
                body_indexes=body_indexes,
                keywords=keywords,
                children=child_links,
                sess=sess,
                delete_unfound_item=delete_unfounded_item
            )
            page_ids.update(p)
            word_ids.update(w)
        
        url_visited.add(url)
        if len(url_queue) + page_count < max_page: url_queue.extend(child_links)
        page_count += 1

    with Session() as sess:
        compute_pagerank(page_ids=page_ids, db=sess)
        compute_pmi(word_ids=word_ids, db=sess)

if __name__ == '__main__':
    # create_database(restore=True)
    # bfs_crawl()
    with Session() as sess:
        # cls = BodyIndex

        # ti1 = aliased(BodyIndex)
        # ti2 = aliased(BodyIndex)

        # cooccurence = sess.query(
        #     ti1.word_id.label('word1'), 
        #     ti2.word_id.label('word2'), 
        #     cast(func.min(ti1.frequency, ti2.frequency), Float).label('co_count')
        # ).join(
        #     ti2, and_(
        #         ti1.webpage_id == ti2.webpage_id,
        #         ti1.word_id != ti2.word_id,
        #         ti1.frequency >= 1,
        #         ti2.frequency >= 1,
        #         ti1.word_id.in_([1, 2, 3, 4, 5, 6]),
        #     )
        # ).join(Webpage, and_(
        #     Webpage.webpage_id == ti1.webpage_id,
        #     Webpage.is_crawled == True,
        #     Webpage.is_active == True,
        # )).subquery()

        # word_freq = sess.query(
        #     cls.word_id.label('word'),
        #     cast(func.sum(cls.frequency), Float).label('freq')
        # ).join(Webpage, and_(
        #     Webpage.webpage_id == cls.webpage_id,
        #     Webpage.is_crawled == True,
        #     Webpage.is_active == True,
        #     cls.frequency >= 1,
        # )).group_by(cls.word_id).subquery()

        # word1_freq = aliased(word_freq)
        # word2_freq = aliased(word_freq)

        # pmi_query = select(
        #     cooccurence.c.word1.label('word1'), 
        #     cooccurence.c.word2.label('word2'),
        #     cast((cooccurence.c.co_count / (word1_freq.c.freq * word2_freq.c.freq)), Float).label('co_count')
        # ).join_from(
        #     cooccurence, word1_freq, 
        #     cooccurence.c.word1 == word1_freq.c.word
        # ).join(
        #     word2_freq, cooccurence.c.word2 == word2_freq.c.word
        # ).order_by(
        #     cast((cooccurence.c.co_count / (word1_freq.c.freq * word2_freq.c.freq)), Float).desc()
        # ).limit(max_query_co_occurence_terms)

        # result = sess.execute(pmi_query).fetchall()

        # print(result)
        word_ids = sess.query(Keyword.word_id).all()
        word_ids = set([word_id[0] for word_id in word_ids])
        compute_pmi(word_ids=word_ids, db=sess)
        result = sess.query(func.count(PMI.pmi)).scalar()
        print(f'Total {result} PMIs computed.')
        # write_webpage_infos(
        #     db=sess, write_parent=False, 
        #     limit=-1, relationship_limit=10,
        #     keyword_limit=10,
        # )
        # i = sess.query(func.count(Webpage.is_active)).filter(Webpage.is_crawled == True).scalar()
        # print(f'Total {i} webpages crawled.')