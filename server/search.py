from db.schemas import *
from db.database import *
from sqlalchemy.orm import aliased
from utils import extract_keywords
from math import log2, sqrt
from utils import *
import time

'''
[
    {
        'query': str
        'original_query_vector': dict[str, (int, float)] # word, word_id, tfidf
        'modified_query_vector': dict[str, (int, float)] # word, word_id, tfidf
        'webpages': [
            {
                top_tfs: list[tuple[str, int, int]], # word, word_id, tf
                relevance: int[-1, 1],
                ...
            }
        ]
    }
]
'''

terms_ids: dict[int ,str] = dict()

def search(
    query: str,
    title_any: set[int] = set(),
    title_all: set[int] = set(),
    title_not: set[int] = set(),
    body_any: set[int] = set(),
    body_all: set[int] = set(),
    body_not: set[int] = set(),
    page_any: set[int] = set(),
    page_all: set[int] = set(),
    page_not: set[int] = set(),
    from_date: str | None = None,
    to_date: str | None = None,
    cookies: list[dict[str, Any]] = list(),
    db = Session()
) -> tuple[
    list[tuple[dict[str, Any], float]], # webpage: score
    dict[str, tuple[int, float]], # word: (word_id, tfidf) (original query)
    dict[str, tuple[int, float]], # word: (word_id, tfidf) (modified query)
]:
    global terms_ids
    # get word ids
    query_tfidfs, query_tfs, _ = compute_query_tfidf(
        query, db=db, fuzzy_matched=False,
        title_all=title_all, title_any=title_any, title_not=title_not,
        body_all=body_all, body_any=body_any, body_not=body_not,
        page_all=page_all, page_any=page_any, page_not=page_not
    )
    word_ids: set[int] = {k for k, v in query_tfidfs.items() if v >= 0}
    pmi_tfidfs = compute_co_occurence_tfidf(query_tfs, require_idf=True, db=db)

    # get tfidfs
    title_webpage_dict, title_tfidfs, title_tfs = get_webpage_tfidfs(
        word_ids=word_ids, 
        any_word_ids=title_any.union(page_any), 
        all_word_ids=title_all.union(page_all), 
        not_word_ids=title_not.union(page_not),
        from_date=from_date, to_date=to_date,
        is_title=True, db=db
    )
    body_webpage_dict, body_tfidfs, body_tfs = get_webpage_tfidfs(
        word_ids=word_ids, 
        any_word_ids=body_any.union(page_any), 
        all_word_ids=body_all.union(page_all), 
        not_word_ids=body_not.union(page_not),
        from_date=from_date, to_date=to_date,
        is_title=False, db=db
    )

    # query weight modification
    modified_query_tfidfs: dict[int, float] = dict()
    # relevance feedback consideration
    modified_query_tfidfs, _ = compute_relevance_feedback(
        qtfidf=query_tfidfs, cookies=cookies
    )

    # pmi consideration
    print(pmi_tfidfs)
    for i, v in pmi_tfidfs.items():
        if i in modified_query_tfidfs.keys():
            modified_query_tfidfs[i] += v
        else:   
            modified_query_tfidfs[i] = v

    # get involved webpage keyword count
    webpage_dict = {**title_webpage_dict, **body_webpage_dict}

    # compute cosine similarity
    scores: dict[Webpage, float] = dict()
    max_pagerank = db.query(func.max(Webpage.pagerank)).first()
    for page_id, page in webpage_dict.items():
        tfidf = combine_weight(
            title_tfidfs.get(page_id, dict()), body_tfidfs.get(page_id, dict())
        )
        sim = compute_cosine_similarity(
            q1=modified_query_tfidfs,
            q2=tfidf
        )
        scores[page] = sim * (1 - pagerank_weight) + page.pagerank * pagerank_weight / max_pagerank[0]

    output: list[tuple[dict[str, Any], float]] = list()

    for page, score in scores.items():
        if score <= 0: continue
        top_tfs = combine_weight(title_tfs.get(page.webpage_id, dict()), body_tfs.get(page.webpage_id, dict()))
        top_tfidfs = combine_weight(title_tfidfs.get(page.webpage_id, dict()), body_tfidfs.get(page.webpage_id, dict()))
        
        for i in set(top_tfidfs.keys()).union(set(top_tfs.keys())):
            if i not in terms_ids.keys():
                terms_ids[i] = db.query(Keyword.word).filter(Keyword.word_id == i).first()[0]

        top_tfs = sorted(top_tfs.items(), key=lambda kv: kv[1], reverse=True)[:max_ranked_words]
        top_tfidfs = sorted(top_tfidfs.items(), key=lambda kv: kv[1], reverse=True)[:max_ranked_words]

        page_item = {
            'webpage_id': page.webpage_id,
            'url': page.url,
            'title': page.title,
            'last_modified_date': page.last_modified_date,
            'size': page.size,
            'top_tfs': [(terms_ids[i], i, j) for i, j in top_tfs],
            'top_tfidfs': [(terms_ids[i], i, j) for i, j in top_tfidfs],
            'parents': [],
            'children': [],
        }

        limit = 0
        for child in page.parent_relation:
            if limit >= relationship_limit: break
            if child.is_active and child.child.is_active and child.child.is_crawled:
                page_item['children'].append(child.child.url)
                limit += 1

        limit = 0
        for parent in page.child_relation:
            if limit >= relationship_limit: break
            if parent.is_active and parent.parent.is_active and parent.parent.is_crawled:
                page_item['parents'].append(parent.parent.url)
                limit += 1

        output.append((page_item, score))


    for i in set(modified_query_tfidfs.keys()):
        if i not in terms_ids.keys():
            terms_ids[i] = db.query(Keyword.word).filter(Keyword.word_id == i).first()[0]

    original_query_vector = {terms_ids[i]: (i, j) for i, j in query_tfidfs.items()}
    modified_query_vector = {terms_ids[i]: (i, j) for i, j in modified_query_tfidfs.items()}

    # sort by similarity
    return (
        sorted(output, key=lambda kv: kv[1], reverse=True), 
        original_query_vector, 
        modified_query_vector
    )

def joined_search(
    queries: dict[str, Any], 
    cookies: list[dict[str, Any]] = list(), 
    db=Session()
) -> tuple[
    list[tuple[dict[str, Any], float]], 
    dict[str, tuple[int, float]],
    dict[str, tuple[int, float]],
]:
    average_result: dict[int, tuple[dict[str, Any], float]] = dict()
    original_query_vector: dict[str, tuple[int, float]] = dict()
    modified_query_vector: dict[str, tuple[int, float]] = dict()

    # list of queries
    n = len(queries['queries'])
    for i in queries['queries']:
        result, q_vector = [], dict()
        if isinstance(i, dict):
            if 'queries' in i.keys():
                result, q_vector, mq_vector = joined_search(i, cookies=cookies, db=db)
            else:
                result, q_vector, mq_vector = search(
                    query=i['query'], 
                    title_any=i.get('title_any', set()),
                    title_all=i.get('title_all', set()),
                    title_not=i.get('title_not', set()),
                    body_any=i.get('body_any', set()),
                    body_all=i.get('body_all', set()),
                    body_not=i.get('body_not', set()),
                    page_any=i.get('page_any', set()),
                    page_all=i.get('page_all', set()),
                    page_not=i.get('page_not', set()),
                    from_date=i.get('from_date', None),
                    to_date=i.get('to_date', None),
                    cookies=cookies, db=db
                )

        if len(average_result) == 0:
            average_result = {j[0]['webpage_id']: (j[0], j[1] / n) for j in result}
        else:
            for j in result:
                # union
                if j[0]['webpage_id'] not in average_result.keys():
                    if queries['type'] == 'merged':
                        average_result[j[0]['webpage_id']] = (j[0], j[1] / n)
                # intersect
                else:
                    average_result[j[0]['webpage_id']] = (
                        j[0], average_result[j[0]['webpage_id']][1] + j[1] / n
                    )

        original_query_vector = merge_dict(
            a=original_query_vector, b=q_vector,
            func=lambda a, b: (
                (a[0] if a is not None else b[0]),
                (a[1] if a is not None else 0) + (b[1] if b is not None else 0) / n
            )
        )
        
        modified_query_vector = merge_dict(
            a=modified_query_vector, b=mq_vector,
            func=lambda a, b: (
            (a[0] if a is not None else b[0]),
            (a[1] if a is not None else 0) + (b[1] if b is not None else 0) / n
            )
        )

    return (
        sorted(average_result.values(), key=lambda kv: kv[1], reverse=True), 
        original_query_vector, 
        modified_query_vector
    )

def combine_weight(title: dict[int, float], body: dict[int, float]) -> dict[int, float]:
    return merge_dict(
        a=title, b=body, 
        func=lambda a, b: (a if a is not None else 0) * title_weight + (b if b is not None else 0) * (1 - title_weight)
    )

def suggest_query(
    query: str,
    cookies: list[dict[str, Any]] = list(),
    db = Session()
) -> tuple[
    list[tuple[str, int, float]], # word: (word_id, probability)
    dict[tuple[str, int, float]], # word: (word_id, pmi)
    dict[tuple[str, int, float]], # word: (word_id, tfidf)
    dict[tuple[str, float]], # queries: cosine similarity
]:
    query_tfidfs, query_tfs, fuzzy_matched_keywords = compute_query_tfidf(query, fuzzy_matched=True, db=db)
    word_ids: set[int] = set(query_tfidfs.keys())
    pmi_word_ids = compute_co_occurence_tfidf(query_tfs, require_idf=True, db=db)

    # relevance feedback consideration
    query_tfidfs, sim_queries = compute_relevance_feedback(
        qtfidf=query_tfidfs, cookies=cookies
    )
    relevant_words = sorted(
        [(k, v) for k, v in query_tfidfs.items() if k not in word_ids and v >= 0], 
        key=lambda kv: kv[1], reverse=True
    )[:max_ranked_words]

    suggest_word_ids = set(pmi_word_ids.keys()).union(query_tfidfs.keys())
    suggest_word_id_dict = db.query(Keyword.word_id, Keyword.word).filter(Keyword.word_id.in_(suggest_word_ids)).all()
    suggest_word_id_dict = {i[0]: i[1] for i in suggest_word_id_dict}
    pmi_words = sorted(
        [(suggest_word_id_dict[k], k, v) for k, v in pmi_word_ids.items() if v > 0],
        key=lambda kv: kv[2], reverse=True
    )
    relevant_words = sorted(
        [(suggest_word_id_dict[k], k, v) for k, v in relevant_words],
        key=lambda kv: kv[2], reverse=True
    )
    fuzzy_matched_keywords = sorted(
        [(suggest_word_id_dict[k], k, v) for k, v in fuzzy_matched_keywords.items() if v > 0],
        key=lambda kv: kv[2], reverse=True
    )
    sim_queries = sorted(
        [(i, j) for i, j in sim_queries.items() if j > 0],
        key=lambda kv: kv[1], reverse=True
    )

    return fuzzy_matched_keywords, pmi_words, relevant_words, sim_queries

def compute_cosine_similarity(
    q1: dict[int, float],
    q2: dict[int, float],
) -> float:
    q1_sum = 0
    q2_sum = 0
    nominator = 0

    # compute cosine similarity
    for word_id in q1.keys():
        q1_tfidf = q1[word_id]
        q2_tfidf = q2.get(word_id, 0)

        q1_sum += q1_tfidf ** 2
        nominator += q1_tfidf * q2_tfidf

    for word_id in q2.keys():
        q2_sum += q2[word_id] ** 2

    return nominator / (sqrt(q1_sum) * sqrt(q2_sum)) if (q1_sum > 0 and q2_sum > 0) else 0

def compute_relevance_feedback(
    qtfidf: dict[int, float], 
    cookies: list[dict[str, Any]] = list(),
) -> tuple[dict[int, float], dict[str, float]]:
    # compute relevance feedback
    relevant_words: list[tuple[int, float]] = list()
    query_similarities: dict[float, list[int]] = dict()
    relevant_n = 0
    non_relevant_n = 0

    for i, cookie in enumerate(cookies):
        query_similarity = round(compute_cosine_similarity(qtfidf, cookie['modified_query_vector']), 3)
        if query_similarity not in query_similarities.keys():
            query_similarities[query_similarity] = [i]
        else: query_similarities[query_similarity].append(i) 

    top_similarities = sorted(
        query_similarities.items(), key=lambda kv: kv[0], reverse=True
    )[:max_relevant_query_considered]
    top_queries = dict()
    for similarity, qid in top_similarities:
        if similarity <= 0: continue
        for i in qid:
            cookie = cookies[i]

            if 'query' in cookie and cookie['query'] not in top_queries.keys():
                top_queries[cookie['query']] = similarity

            for page in cookie['webpages']:
                relevance = page['relevance'] * similarity
                if relevance == 0: continue
                elif relevance > 0: relevant_n += relevance
                else: non_relevant_n += abs(relevance)
                relevant_words += [(i, j * relevance) for _, i, j in page['top_tfidfs']]

    # compute query tfidf
    for word_id, freq in relevant_words:
        w = freq
        if w < 0: w *= non_relevant_weight / non_relevant_n
        else: w *= relevant_weight / relevant_n

        if word_id in qtfidf.keys():
            qtfidf[word_id] += w
        else:
            qtfidf[word_id] = w

    return qtfidf, top_queries

def get_webpage_tfidfs(
    word_ids: set[int] = set(), 
    any_word_ids: set[int] = set(),
    all_word_ids: set[int] = set(),
    not_word_ids: set[int] = set(),
    from_date: str | None = None,
    to_date: str | None = None,
    is_title: bool = True, 
    db=Session()
) -> tuple[
    dict[int, Webpage], # webpage id: webpage
    dict[int, dict[int, float]], # webpage id: word id: tfidf
    dict[int, dict[int, float]], # webpage id: word id: tf
]:
    any_word_ids = word_ids.union(any_word_ids)
    any_word_ids = any_word_ids.difference(not_word_ids).difference(all_word_ids)
    all_word_ids = all_word_ids.difference(not_word_ids)
    cls = TitleIndex if is_title else BodyIndex

    any_subquery = db.query(Webpage.webpage_id).join(
        cls, cls.webpage_id == Webpage.webpage_id
    ).filter(and_(
        cls.word_id.in_(any_word_ids),
        cls.frequency >= 1,
        Webpage.is_crawled == True,
        Webpage.is_active == True,
    )).subquery()
    where_clause = [cls.webpage_id.in_(any_subquery), cls.frequency >= 1]

    if len(all_word_ids) != 0:
        all_subquery = db.query(Webpage.webpage_id).join(
            cls, cls.webpage_id == Webpage.webpage_id
        ).filter(and_(
            cls.word_id.in_(all_word_ids),
            cls.frequency >= 1,
            Webpage.is_crawled == True,
            Webpage.is_active == True,
        )).group_by(Webpage.webpage_id).having(
            func.count(cls.word_id.distinct()) == len(all_word_ids)
        ).subquery()
        where_clause.append(cls.webpage_id.in_(all_subquery))

    if len(not_word_ids) != 0:
        not_subquery = db.query(Webpage.webpage_id).join(
            cls, cls.webpage_id == Webpage.webpage_id
        ).filter(and_(
            cls.word_id.in_(not_word_ids),
            cls.frequency >= 1,
            Webpage.is_crawled == True,
            Webpage.is_active == True,
        )).subquery()
        where_clause.append(cls.webpage_id.notin_(not_subquery))

    if from_date is not None:
        where_clause.append(Webpage.last_modified_date >= from_date)
    if to_date is not None:
        where_clause.append(Webpage.last_modified_date <= to_date)

    indexes = db.query(cls).filter(and_(*where_clause)).all()

    tf_dict: dict[int, dict[int, TitleIndex | BodyIndex]] = dict() # webpage id: word_id: index
    webpage_dict = {i.webpage_id: i.webpage for i in indexes}

    for index in indexes:
        try: tf_dict[index.webpage_id][index.word_id] = index.normalized_tf
        except: tf_dict[index.webpage_id] = {index.word_id: index.normalized_tf}

    tfidf_dict: dict[int, dict[int, float]] = {
        k: compute_tfidf(v, is_title=is_title, db=db) 
        for k, v in tf_dict.items()
    }

    return webpage_dict, tfidf_dict, tf_dict

def compute_query_tfidf(
    query: str, 
    fuzzy_matched: bool = False,
    title_any: set[int] = set(),
    title_all: set[int] = set(),
    title_not: set[int] = set(),
    body_any: set[int] = set(),
    body_all: set[int] = set(),
    body_not: set[int] = set(),
    page_any: set[int] = set(),
    page_all: set[int] = set(),
    page_not: set[int] = set(),
    db=Session()) -> tuple[
    dict[int, float], 
    dict[int, float], 
    dict[int, float]
]:

    global terms_ids
    
    given_ids = title_any.union(page_any).union(body_any).union(title_all).union(body_all).union(page_all).difference(title_not).difference(page_not).difference(body_not)
    not_word_ids = title_not.union(body_not).union(page_not)
    query_tf = dict()
    exact_match_words = given_ids.union(not_word_ids)

    if query.strip() != '':
        query_tf_dict = extract_keywords(query)
        exact_match_words = exact_match_words.union(set(query_tf_dict.keys()))
        where_clause = Keyword.word.in_(query_tf_dict.keys())
        if fuzzy_matched:
            where_clause = or_(Keyword.word.like(f'%{i}%') for i in query_tf_dict.keys())

        terms = db.query(Keyword.word_id, Keyword.word).filter(where_clause).all()
        terms = {i[1]: i[0] for i in terms}
        terms_ids.update({i[0]: i[1] for i in terms})
        
        for k, v in query_tf_dict.items():
            if fuzzy_matched:
                w = [i for i in terms.keys() if k in i]
                if len(w) > 0: 
                    query_tf.update({
                        terms[a]: v * substring_probability(k, a) for a in w if a in terms.keys()
                    })
            else:
                word_id = terms.get(k, None)
                if word_id is None: continue
                if word_id < 0: continue
                query_tf[word_id] = v

    for k in given_ids:
        if k in query_tf.keys(): query_tf[k] += 1
        else: query_tf[k] = 1

    for k in not_word_ids:
        query_tf[k] = -1

    max_query_tf = max(max(query_tf.values()), 1)
    for k, v in query_tf.items():
        query_tf[k] /= max_query_tf

    tfidf = compute_tfidf(query_tf, is_title=None, db=db)

    fuzzy_matched_words = dict()
    if fuzzy_matched:
        fuzzy_matched_words = {
            k: v for k, v in tfidf.items() if k not in exact_match_words
        }
        top_fuzzy_matched = sorted(
            set(fuzzy_matched_words.values()), reverse=True
        )[:max_fuzzy_word_matching]
        fuzzy_matched_words = {
            k: v for k, v in fuzzy_matched_words.items() if v in top_fuzzy_matched
        }
    
    return tfidf, query_tf, fuzzy_matched_words

def compute_co_occurence_tfidf(
    query_tfs: dict[int, float], 
    require_idf: bool = True, 
    db=Session()) -> dict[int, float]: # word_id: pmi

    pmi_word_tfs: dict[int, float] = dict()
    max_pmi = db.query(func.max(PMI.pmi)).scalar_subquery()

    pmi = db.query(
        PMI.word1_id.label('word1'), 
        PMI.word2_id.label('word2'), 
        (PMI.pmi / max_pmi * co_occurence_weight).label('pmi'),
    ).filter(or_(
        PMI.word1_id.in_(query_tfs.keys()), 
        PMI.word2_id.in_(query_tfs.keys())
    )).all()

    if pmi is None or len(pmi) == 0:
        return dict()

    for i in pmi:
        if i[0] not in query_tfs:
            pmi_word_tfs[i[0]] = i[2] * query_tfs[i[1]]

        if i[1] not in query_tfs:
            pmi_word_tfs[i[1]] = i[2] * query_tfs[i[0]]

    if require_idf:
        tfidf = compute_tfidf(pmi_word_tfs, is_title=None, db=db)
    else:
        tfidf = pmi_word_tfs

    top_score = sorted(set(tfidf.values()), reverse=True)[:max_query_co_occurence_terms]
    return {
        k: v for k, v in tfidf.items() if v in top_score
    }

def compute_tfidf(tf: dict[int, float], is_title: bool | None, db=Session()) -> dict[int, float]:
    wid = set(tf.keys())
    if len(wid) <= 0: return dict()

    def idf_query(wid: set[int], is_title: bool):
        idf_n = db.query(func.count(Webpage.webpage_id)).filter(and_(
            Webpage.is_active == True,
            Webpage.is_crawled == True
        )).scalar_subquery()
        cls = TitleIndex if is_title else BodyIndex
    
        return db.query(
            cls.word_id.label('word_id'), 
            func.log(idf_n / func.count(cls.webpage_id)).label('idf'),
        ).join(
            Webpage, cls.webpage_id == Webpage.webpage_id
        ).filter(and_(
            cls.word_id.in_(wid),
            cls.frequency >= 1,
            Webpage.is_crawled == True,
            Webpage.is_active == True,
        )).group_by(
            cls.word_id
        ).having(
            func.count(cls.webpage_id) > 0
        )
    
    result = None
    if is_title is None:
        title = idf_query(wid, is_title=True).subquery()
        body = idf_query(wid, is_title=False).subquery()
        result = select(
            func.coalesce(title.c.word_id, body.c.word_id),
            (
                func.coalesce(title.c.idf, 0) * title_weight + 
                func.coalesce(body.c.idf, 0) * (1 - title_weight)
            )
        ).join_from(
            title, body, title.c.word_id == body.c.word_id, full=True
        ).filter(
            func.coalesce(title.c.idf, 0) + func.coalesce(body.c.idf, 0) > 0
        )
        result = db.execute(result).fetchall()
    elif is_title == True:
        result = idf_query(wid, is_title=True).all()
    else: 
        result = idf_query(wid, is_title=False).all()

    result = {i[0]: i[1] for i in result}

    return {word: index * result.get(word, 0) for word, index in tf.items()}

def get_keywords_with_freq(db=Session()) -> dict[str, tuple[int, int]]:
    title_keywords = db.query(Keyword.word, Keyword.word_id, func.sum(TitleIndex.frequency)).join(
        TitleIndex, Keyword.word_id == TitleIndex.word_id
    ).filter(
        TitleIndex.frequency >= 1
    ).order_by(
        func.sum(TitleIndex.frequency).desc()
    ).group_by(Keyword.word_id).all()
    title_keywords = {i[0]: (i[1], i[2]) for i in title_keywords}

    body_keywords = db.query(Keyword.word, Keyword.word_id, func.sum(BodyIndex.frequency)).join(
        BodyIndex, Keyword.word_id == BodyIndex.word_id
    ).filter(
        BodyIndex.frequency >= 1
    ).order_by(
        func.sum(BodyIndex.frequency).desc()
    ).group_by(Keyword.word_id).all()
    body_keywords = {i[0]: (i[1], i[2]) for i in body_keywords}

    return merge_dict(
        a=title_keywords, b=body_keywords, 
        func=lambda a, b: (
            (a[0] if a is not None else b[0]), 
            (a[1] if a is not None else 0) + 
            (b[1] if b is not None else 0)
        )
    )

if __name__ == '__main__':
    time_start = time.time()
    result = None
    # relevant_urls = [
    #     'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm',
    #     'https://www.cse.ust.hk/~kwtleung/COMP4321/books.htm',
    #     'https://www.cse.ust.hk/~kwtleung/COMP4321/ust_cse.htm',
    #     'https://www.cse.ust.hk/~kwtleung/COMP4321/Movie.htm',
    #     'https://www.cse.ust.hk/~kwtleung/COMP4321/news.htm',
    # ]
    with Session() as sess:
        result = joined_search(queries={
            'type': 'merged',
            'queries': [
                {
                    'query': 'cse'
                },
                {
                    'query': 'hkust'
                }
            ]
        }, db=sess)
        
    print(result)
    print('Time taken:', time.time() - time_start)