from db.schemas import *
from db.database import *
from utils import extract_keywords
from math import log2, sqrt

def search(
    query: str, title_weight: float = 0.7, 
    db = Session()) -> list[tuple[Webpage, float]]:
    # get word ids
    query_tf_dict = extract_keywords(query)
    max_query_tf = max(query_tf_dict.values())
    wids = db.query(Keyword.word, Keyword.word_id).filter(Keyword.word.in_(query_tf_dict.keys())).all()
    word_id_dict = {str(w[0]).strip(): int(w[1]) for w in wids}

    # get tfidfs
    title_webpage_dict, title_tfidfs, title_idfs = get_tfidfs(
        word_ids=word_id_dict.values(), 
        weight=title_weight, is_title=True, db=db)
    body_webpage_dict, body_tfidfs, body_idfs = get_tfidfs(
        word_ids=word_id_dict.values(), 
        weight=(1 - title_weight), is_title=False, db=db)
    
    # compute query tfidf
    query_tfidfs: dict[int, float] = dict()
    for word, tf in query_tf_dict.items():
        word_id = word_id_dict.get(word, -1)
        if word_id < 0: continue
        title_idf = title_idfs.get(word_id, 0)
        body_idf = body_idfs.get(word_id, 0)
        query_tfidfs[word_id] = (tf / max_query_tf) * (title_idf + body_idf)

    # get involved webpage keyword count
    webpage_dict = {**title_webpage_dict, **body_webpage_dict}
    title_count = db.query(Index.webpage_id, func.count(Index.frequency)).filter(and_(
        Index.frequency >= 1,
        Index.webpage_id.in_(webpage_dict.keys()),
        Index.is_title == True
    )).group_by(Index.webpage_id).all()
    title_word_count = {t[0]: t[1] for t in title_count}
    body_count = db.query(Index.webpage_id, func.count(Index.frequency)).filter(and_(
        Index.frequency >= 1,
        Index.webpage_id.in_(webpage_dict.keys()),
        Index.is_title == False
    )).group_by(Index.webpage_id).all()
    body_word_count = {b[0]: b[1] for b in body_count}

    # compute weighted cosine similarity
    scores: dict[Webpage, float] = dict()
    for page_id, page in webpage_dict.items():
        sim = get_cos_similarity(
            title_tfidfs=title_tfidfs.get(page_id, dict()),
            body_tfidfs=body_tfidfs.get(page_id, dict()),
            query_tfidfs=query_tfidfs,
            title_word_count=title_word_count[page_id],
            body_word_count=body_word_count[page_id],
            title_weight=title_weight
        )
        scores[page] = sim

    # sort by similarity
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

def get_cos_similarity(
    title_tfidfs: dict[int, float],
    body_tfidfs: dict[int, float],
    query_tfidfs: dict[int, float],
    title_word_count: int,
    body_word_count: int,
    title_weight: float,
) -> float:
    doc_sum = 0
    query_sum = 0
    nominator = 0
    query_word_count = len(query_tfidfs)
    title_intersect = len(title_tfidfs)
    body_intersect = len(body_tfidfs)
    title_union = title_word_count + query_word_count - title_intersect
    body_union = body_word_count + query_word_count - body_intersect
    cos_weight = title_intersect / title_union * title_weight + body_intersect / body_union * (1 - title_weight)

    for word_id in query_tfidfs.keys():
        title_tfidf = title_tfidfs.get(word_id, 0)
        body_tfidf = body_tfidfs.get(word_id, 0)
        query_tfidf = query_tfidfs[word_id]

        doc_sum += (title_tfidf + body_tfidf) ** 2
        query_sum += query_tfidf ** 2
        nominator += (title_tfidf + body_tfidf) * query_tfidf

    return nominator / (sqrt(query_sum) * sqrt(doc_sum)) * cos_weight

def get_tfidfs(
    word_ids: set[int], is_title: bool = True, 
    weight: float = 1, db=Session()
) -> tuple[
    dict[int, Webpage], # webpage id: webpage
    dict[int, dict[int, float]],
    dict[int, float],
]:
    indexes = db.query(Index).join(Webpage, Index.webpage_id == Webpage.webpage_id).filter(and_(
        Index.word_id.in_(word_ids),
        Index.frequency >= 1,
        Index.is_title == is_title,
        Webpage.is_crawled == True,
        Webpage.is_active == True,
    )).all()

    n = int(db.query(func.count(Webpage.webpage_id)).filter(and_(
        Webpage.is_active == True,
        Webpage.is_crawled == True
    )).first()[0])

    forward_index_dict: dict[int, dict[int, Index]] = dict() # webpage id: word_id: index
    inverted_index_dict: dict[int, dict[int, Index]] = dict() # word id: webpage id: index
    webpage_dict = {i.webpage_id: i.webpage for i in indexes}

    for index in indexes:
        try: forward_index_dict[index.webpage_id][index.word_id] = index
        except: forward_index_dict[index.webpage_id] = {index.word_id: index}

        try: inverted_index_dict[index.word_id][index.webpage_id] = index
        except: inverted_index_dict[index.word_id] = {index.webpage_id: index}

    tfidf_dict: dict[int, dict[int, float]] = dict() # webpage id: word id: tfidf
    idf_dict: dict[int, float] = dict() # word id: idf

    for word, w_dict in inverted_index_dict.items():
        idf = log2(n / len(w_dict)) * weight
        idf_dict[word] = idf

    for webpage, w_dict in forward_index_dict.items():
        tfidf_dict[webpage] = {word: index.normalized_tf * idf_dict[word] for word, index in w_dict.items()}

    return webpage_dict, tfidf_dict, idf_dict

if __name__ == '__main__':
    result = None
    with Session() as sess:
        result = search('hkust cse department', db=sess)
        
    for a, s in result:
        print(a.url, s)