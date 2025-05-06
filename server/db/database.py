from concurrent.futures import ThreadPoolExecutor
from math import log2
from sqlalchemy import String, Float, create_engine, and_, not_, update, or_, func, delete, select, cast, insert
from sqlalchemy.orm import sessionmaker, aliased
from constant import *

try: from schemas import *
except: from .schemas import *

from typing import Any
import sqlalchemy.dialects.sqlite as sqlite
import threading

lock = threading.Lock()
engine = create_engine(db_uri, echo=True, pool_size=16, max_overflow=16, connect_args={"check_same_thread": False}) # Create a SQLAlchemy engine , echo=True
Session = sessionmaker(bind=engine) # Create a session to interact with the database

def create_database(restore: bool = False):
    global engine
    if restore: Base().metadata.drop_all(bind=engine)
    Base().metadata.create_all(bind=engine)

def set_title_index(
    title_indexes: list[TitleIndex], 
    ignore: bool = False,
    delete_unindexed_words: bool = False, 
    db = Session()) -> None:
    
    for i in title_indexes: i.index_id = f'{i.webpage_id}-{i.word_id}'

    upsert(
        sess=db, cls=TitleIndex, inputs=title_indexes,
        ignore=ignore,
        conflict_items=[TitleIndex.index_id],
    )

    # if webpage id found but corresponding keyword is not found, set the frequency to 0
    where_clause = None
    if delete_unindexed_words:
        where_clause = not_(TitleIndex.index_id.in_([index.index_id for index in title_indexes]))
    else:
        founded_page = set([i.webpage_id for i in title_indexes])
        where_clause = and_(
            (TitleIndex.webpage_id.in_(founded_page)),
            not_(TitleIndex.index_id.in_([index.index_id for index in title_indexes]))
        )

    query = update(TitleIndex).where(where_clause).values(frequency=0)
    db.execute(query)
    db.commit()

def set_body_index(
    body_indexes: list[BodyIndex], 
    ignore: bool = False,
    delete_unindexed_words: bool = False, 
    db = Session()) -> None:
    
    for i in body_indexes: i.index_id = f'{i.webpage_id}-{i.word_id}'

    upsert(
        sess=db, cls=BodyIndex, inputs=body_indexes,
        ignore=ignore,
        conflict_items=[BodyIndex.index_id],
    )

    # if webpage id found but corresponding keyword is not found, set the frequency to 0
    where_clause = None
    if delete_unindexed_words:
        where_clause = not_(BodyIndex.index_id.in_([index.index_id for index in body_indexes]))
    else:
        founded_page = set([i.webpage_id for i in body_indexes])
        where_clause = and_(
            (BodyIndex.webpage_id.in_(founded_page)),
            not_(BodyIndex.index_id.in_([index.index_id for index in body_indexes]))
        )

    query = update(BodyIndex).where(where_clause).values(frequency=0)
    db.execute(query)
    db.commit()

def set_keyword(keywords: list[str | Keyword], db = Session()) -> dict[str, int]:
    mapping: list[tuple[int, str]] = upsert(
        sess=db, cls=Keyword, inputs=keywords,
        conflict_items=[Keyword.word],
        returning=(Keyword.word_id, Keyword.word)
    )
    return {t[1]: t[0] for t in mapping}

def set_relationship(
    relationship: list[Relationship],
    ignore: bool = False,
    delete_unfounded_relationship: bool = False,
    db = Session()) -> None:

    for r in relationship: r.relate_id = f'{r.parent_id}-{r.child_id}'

    upsert(
        sess=db, cls=Relationship, inputs=relationship,
        conflict_items=[Relationship.relate_id],
        ignore=ignore,
    )

    where_clause = None
    if delete_unfounded_relationship:
        where_clause = not_(Relationship.relate_id.in_([r.relate_id for r in relationship]))
    else:
        founded_pages = set([r.parent_id for r in relationship])
        where_clause = and_(
            (Relationship.parent_id.in_(founded_pages)),
            not_(Relationship.relate_id.in_([r.relate_id for r in relationship]))
        )

    query = update(Relationship).where(where_clause).values(is_active=False)
    db.execute(query)
    db.commit()

def set_webpage(
    webpages: list[Webpage],
    ignore: bool = False,
    delete_unfounded_page: bool = False, 
    db = Session()) -> dict[str, int]:

    mapping: list[tuple[int, str]] = upsert(
        sess=db, cls=Webpage, inputs=webpages,
        ignore=ignore,
        conflict_items=[Webpage.url],
        returning=(Webpage.webpage_id, Webpage.url)
    )

    if delete_unfounded_page:
        query = update(Webpage).where(
            not_(Webpage.url.in_([page.url for page in webpages]))
        ).values(is_active=False)
        db.execute(query)
        db.commit()

    return {t[1]: t[0] for t in mapping}

# update if exists, insert if not
def upsert(
    cls, inputs: list[Any], 
    conflict_items: list[str],
    ignore: bool = False,
    returning: tuple | None = None, sess = Session()) -> list[tuple] | None:

    new_inputs: list[dict[str, Any]] = [cls.to_basic_dict(a) for a in inputs]
    query = sqlite.insert(cls).values(new_inputs)
    if ignore:
        query = query.on_conflict_do_nothing(index_elements=conflict_items)
    else:
        query = query.on_conflict_do_update(
            index_elements=conflict_items,
            set_=cls.to_update_dict(query.excluded)
        )
    
    if returning is not None: 
        query = query.returning(*returning)
        result = sess.execute(query).fetchall()
        sess.commit()
        return result

    sess.execute(query)
    sess.commit()

def compute_pagerank(page_ids: list[int] | None = None):
    pagerank: dict[int, float] = dict()
    parent_dict: dict[int, dict[int, int]] = dict() # child id: parent id: child count

    with Session() as db:
        if page_ids is None:
            active_webpage = db.query(Webpage).filter(
                and_(Webpage.is_active == True, Webpage.is_crawled == True)
            ).all()
        else:
            active_webpage = db.query(Webpage).filter(
                and_(Webpage.is_active == True, Webpage.is_crawled == True, Webpage.webpage_id.in_(page_ids))
            ).all()

        # asyncronous computation of pagerank
        for webpage in active_webpage:
            for parent in webpage.child_relation:
                if parent.is_active and parent.parent.is_crawled and parent.parent.is_active:
                    # counting parents' children
                    count = 0
                    for child in parent.parent.parent_relation:
                        if child.is_active and child.child.is_crawled and child.child.is_active:
                            count += 1
                    if count > 0:
                        if webpage.webpage_id not in parent_dict.keys():
                            parent_dict[webpage.webpage_id] = dict()
                        parent_dict[webpage.webpage_id][parent.parent.webpage_id] = count  
                        pagerank[parent.parent.webpage_id] = parent.parent.pagerank   

        pagerank.update({w.webpage_id: 1 for w in active_webpage})

    def calc_pagerank(webpage: Webpage):
        if webpage.webpage_id not in pagerank.keys(): return
        if webpage.webpage_id not in parent_dict.keys(): return
        for parent_id, count in parent_dict[webpage.webpage_id].items():
            print(type(count), type(pagerank[parent_id]))
            pagerank[webpage.webpage_id] += (pagerank[parent_id] / count) * pagerank_damping_factor
        pagerank[webpage.webpage_id] = (1 - pagerank_damping_factor) + pagerank[webpage.webpage_id]

    def write_pagerank(webpages: list[Webpage]):
        lock.acquire()
        db = Session()
        db.execute(update(Webpage), [
            {'webpage_id': i.webpage_id, 'pagerank': pagerank[i.webpage_id]}
            for i in webpages if i.webpage_id in pagerank.keys()
        ])
        db.commit()
        db.close()
        lock.release()

    with ThreadPoolExecutor(max_workers=max_thread_worker) as executor:
        for _ in range(pagerank_iteration):
            [executor.submit(calc_pagerank, w) for w in active_webpage]
        
    with ThreadPoolExecutor(max_workers=max_thread_worker) as executor:
        [executor.submit(write_pagerank, active_webpage[i: i + bulk_write_limit]) for i in range(0, len(active_webpage), bulk_write_limit)]

def compute_pmi(word_ids: set[int]) -> list[tuple[int, int, float]]:
    def query_coocurrence(word_ids: list[int], is_title: bool, db=Session()):
        cls = TitleIndex if is_title else BodyIndex
        ti1 = aliased(cls)
        ti2 = aliased(cls)
        freq_threshold = (
            co_occurence_title_frequency_threshold if is_title else 
            co_occurence_body_frequency_threshold
        )

        cooccurence = db.query(
            ti1.word_id.label('word1'), 
            ti2.word_id.label('word2'), 
            cast(func.min(ti1.frequency, ti2.frequency), Float).label('co_count')
        ).join(
            ti2, and_(
                ti1.webpage_id == ti2.webpage_id,
                ti1.word_id != ti2.word_id,
                ti1.frequency > freq_threshold,
                ti2.frequency > freq_threshold,
                ti1.word_id.in_(word_ids),
            )
        ).join(Webpage, and_(
            Webpage.webpage_id == ti1.webpage_id,
            Webpage.is_crawled == True,
            Webpage.is_active == True,
        )).subquery()

        word_freq = db.query(
            cls.word_id.label('word'),
            cast(func.sum(cls.frequency), Float).label('freq')
        ).join(Webpage, and_(
            Webpage.webpage_id == cls.webpage_id,
            Webpage.is_crawled == True,
            Webpage.is_active == True,
            cls.frequency > freq_threshold,
        )).group_by(cls.word_id).subquery()

        word1_freq = aliased(word_freq)
        word2_freq = aliased(word_freq)

        pmi_n = db.query(func.sum(cls.frequency)).join(
            Webpage, and_(
                Webpage.webpage_id == cls.webpage_id,
                Webpage.is_crawled == True,
                Webpage.is_active == True,
            )
        ).scalar_subquery()

        pmi_query = select(
            cooccurence.c.word1.label('word1'), 
            cooccurence.c.word2.label('word2'),
            func.log(cooccurence.c.co_count * pmi_n / (word1_freq.c.freq * word2_freq.c.freq)).label('co_count')
        ).join_from(
            cooccurence, word1_freq, 
            cooccurence.c.word1 == word1_freq.c.word
        ).join(
            word2_freq, cooccurence.c.word2 == word2_freq.c.word
        ).subquery()

        top_pmi_score = select(
            pmi_query.c.co_count.distinct()
        ).filter(
            pmi_query.c.co_count > pmi_threshold
        ).order_by(
            pmi_query.c.co_count.desc()
        ).limit(
            max_query_co_occurence_terms
        )

        top_pmi = select(
            (
                cast(func.min(pmi_query.c.word1, pmi_query.c.word2), String) + '-' + 
                cast(func.max(pmi_query.c.word1, pmi_query.c.word2), String)
            ).label('pmi_id'),
            func.min(pmi_query.c.word1, pmi_query.c.word2).label('word1_id'),
            func.max(pmi_query.c.word1, pmi_query.c.word2).label('word2_id'),
            pmi_query.c.co_count.label('pmi')
        ).filter(
            pmi_query.c.co_count.in_(top_pmi_score)
        ).order_by(
            pmi_query.c.co_count.desc()
        )

        return top_pmi

    def delete_words(word_ids: list[int]) -> set[int]: 
        db = Session()
        if db.query(func.count(PMI.pmi)).scalar() <= 0: 
            db.close()
            return set()

        result = db.execute(delete(PMI).where(or_(
            PMI.word1_id.in_(word_ids),
            PMI.word2_id.in_(word_ids)
        )).returning(PMI.word1_id, PMI.word2_id)).fetchall()
        db.commit()
        db.close()
        return {i[0] for i in result}.union({i[1] for i in result})

    def write_pmi(affected_words: list[int]):
        lock.acquire()
        db = Session()
        title_pmi = query_coocurrence(affected_words, True, db=db).subquery()
        body_pmi = query_coocurrence(affected_words, False, db=db).subquery()

        pmi = select(
            func.coalesce(title_pmi.c.pmi_id, body_pmi.c.pmi_id).label('pmi_id'),
            func.coalesce(title_pmi.c.word1_id, body_pmi.c.word1_id).label('word1_id'),
            func.coalesce(title_pmi.c.word2_id, body_pmi.c.word2_id).label('word2_id'),
            (
                func.coalesce(title_pmi.c.pmi, 0) * pmi_title_weight + 
                func.coalesce(body_pmi.c.pmi, 0) * (1 - pmi_title_weight)
            ).label('pmi')
        ).join_from(
            title_pmi, body_pmi, and_(
                title_pmi.c.word1_id == body_pmi.c.word1_id,
                title_pmi.c.word2_id == body_pmi.c.word2_id,
            ),
            full=True
        )

        insert_query = sqlite.insert(PMI).from_select(
            ['pmi_id', 'word1_id', 'word2_id', 'pmi'], pmi
        ).on_conflict_do_nothing()
        db.execute(insert_query)
        db.commit()
        db.close()
        lock.release()

    with ThreadPoolExecutor(max_workers=max_thread_worker) as executor: 
        affected_words = word_ids
        word_ids = list(word_ids)

        futures = [executor.submit(delete_words, word_ids[i: i + bulk_write_limit]) for i in range(0, len(word_ids), bulk_write_limit)]
        for f in futures: affected_words.update(f.result())
    
        affected_words = list(affected_words)
        futures = [executor.submit(write_pmi, affected_words[i: i + bulk_write_limit]) for i in range(0, len(word_ids), bulk_write_limit)]
        for f in futures: f.result()
    

def write_webpage_infos(
    limit: int = -1, db = Session(), write_parent: bool = True,
    keyword_limit: int = 10,
    relationship_limit: int = relationship_limit,
    filename: str = 'spider_result.txt'):

    webpages = db.query(Webpage).filter(and_(
        Webpage.is_active == True,
        Webpage.is_crawled == True
    ))
    if limit > 0: webpages = webpages.limit(limit)
    webpages = webpages.all()
    seperator = '-----------------------------------'

    result = ''

    for i, page in enumerate(webpages):
        output = f'Page {i + 1}\nTitle: {page.title}\nURL: {page.url}\nLast Modified Date: {page.last_modified_date}\nPage Size: {page.size}\n'
        output += 'Title Keywords:\n'

        limit = 0
        for index in page.title_indexes:
            if limit >= keyword_limit: break
            output += f'\t- \"{index.keyword.word}\" with frequency: {index.frequency}\n'
            limit += 1

        output += 'Body Keywords:\n'
        limit = 0
        for index in page.body_indexes:
            if limit >= keyword_limit: break
            output += f'\t- \"{index.keyword.word}\" with frequency: {index.frequency}\n'
            limit += 1

        output += 'Children:\n'
        limit = 0
        for child in page.parent_relation:
            if limit >= relationship_limit: break
            if child.is_active and child.child.is_active:
                output += f'\t- {child.child.url}\n'
                limit += 1
        if limit <= 0: output += '\tNo Children Found\n'
        
        if write_parent:
            output += 'Parent:\n'
            limit = 0
            for parent in page.child_relation:
                if limit >= relationship_limit: break
                if parent.is_active and parent.parent.is_active:
                    output += f'\t- {parent.parent.url}\n'
                    limit += 1
            if limit <= 0: output += '\tNo Parent Found\n'
        
        output += seperator + '\n'
        result += output
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(result)