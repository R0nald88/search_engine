from sqlalchemy import create_engine, and_, not_, update, or_
from sqlalchemy.orm import sessionmaker
from .schemas import *
from typing import Callable, Any
import sqlalchemy.dialects.sqlite as sqlite

db_uri = "sqlite:///./server/db/project.db"
engine = create_engine(db_uri, echo=True) # Create a SQLAlchemy engine , echo=True
Session = sessionmaker(bind=engine) # Create a session to interact with the database

def create_database(restore: bool = False):
    global engine
    if restore: Base().metadata.drop_all(bind=engine)
    Base().metadata.create_all(bind=engine)

def set_inverted_index(
    indexes: list[Index], 
    delete_unindexed_words: bool = False, 
    db = Session()) -> None:
    
    for i in indexes: i.index_id = f'{i.webpage_id}-{i.word_id}'

    upsert(
        sess=db, cls=Index, inputs=indexes,
        func=Index.to_basic_dict,
        conflict_items=[Index.index_id],
    )

        # if webpage id found but corresponding keyword is not found, set the frequency to 0
    where_clause = None
    if delete_unindexed_words:
        where_clause = not_(Index.index_id.in_([index.index_id for index in indexes]))
    else:
        founded_page = set([i.webpage_id for i in indexes])
        where_clause = and_(
            (Index.webpage_id.in_(founded_page)),
            not_(Index.index_id.in_([index.index_id for index in indexes]))
        )

    query = update(Index).where(where_clause).values(frequency=0)
    db.execute(query)
    db.commit()

def set_keyword(keywords: list[str | Keyword], db = Session()) -> dict[str, int]:
    mapping: list[tuple[int, str]] = upsert(
        sess=db, cls=Keyword, inputs=keywords,
        func=Keyword.to_basic_dict,
        conflict_items=[Keyword.word],
        returning=(Keyword.word_id, Keyword.word)
    )
    return {t[1]: t[0] for t in mapping}

def set_relationship(
    relationship: list[Relationship],
    delete_unfounded_relationship: bool = False,
    db = Session()) -> None:

    for r in relationship: r.relate_id = f'{r.parent_id}-{r.child_id}'

    upsert(
        sess=db, cls=Relationship, inputs=relationship,
        func=Relationship.to_basic_dict,
        conflict_items=[Relationship.relate_id]
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
    inactive_links: list[str] = [],
    delete_unfounded_page: bool = False, 
    db = Session()) -> dict[str, int]:

    mapping: list[tuple[int, str]] = upsert(
        sess=db, cls=Webpage, inputs=webpages,
        func=Webpage.to_basic_dict,
        conflict_items=[Webpage.url],
        returning=(Webpage.webpage_id, Webpage.url)
    )

    where_clause = None
    if delete_unfounded_page:
        where_clause = or_(
            not_(Webpage.url.in_([page.url for page in webpages])),
            Webpage.url.in_(inactive_links)
        )
    else: where_clause = Webpage.url.in_(inactive_links)

    query = update(Webpage).where(where_clause).values(is_active=False)
    db.execute(query)
    db.commit()

    return {t[1]: t[0] for t in mapping}

# update if exists, insert if not
def upsert(
    cls, inputs: list[Any], 
    func: Callable[[Any], dict[str, Any]],
    conflict_items: list[str],
    returning: tuple | None = None, sess = Session()) -> list[tuple] | None:

    new_inputs: list[dict[str, Any]] = [func(a) for a in inputs]
    query = sqlite.insert(cls).values(new_inputs)
    query = query.on_conflict_do_update(
        index_elements=conflict_items,
        set_=func(query.excluded)
    )
    
    if returning is not None: 
        query = query.returning(*returning)
        result = sess.execute(query).fetchall()
        sess.commit()
        return result

    sess.execute(query)
    sess.commit()

def search_webpage_by_keyword(words: list[str], limit: int = -1, db = Session()) -> list[Webpage]:
    keywords = db.query(Keyword).filter(Keyword.word.in_(words))
    if limit > 0: keywords = keywords.limit(limit)
    keywords = keywords.all()

    webpages = set()
    for k in keywords:
        if len(webpages) + len(k.webpages) < limit:
            webpages = webpages.union(k.webpages)
        elif len(webpages) < limit:
            webpages = webpages.union(k.webpages[:(limit - len(webpages))])
            break
        else: break

    return webpages

def write_webpage_infos(limit: int = -1, db = Session(), filename: str = 'spider_result.txt'):
    webpages = db.query(Webpage).filter(Webpage.is_active == True)
    if limit > 0: webpages = webpages.limit(limit)
    webpages = webpages.all()
    seperator = '-----------------------------------'

    result = ''

    for i, page in enumerate(webpages):
        output = f'Page {i + 1}\nTitle: {page.title}\nURL: {page.url}\nLast Modified Date: {page.last_modified_date}\nPage Size: {page.size}\nKeywords:\n'
        for index in page.indexes:
            output += f'\t- \"{index.keyword.word}\" with frequency: {index.frequency}\n'
        output += 'Children:\n'
        for child in page.children_relation:
            if child.is_active and child.child.is_active:
                output += f'\t- {child.child.url}\n'
        output += 'Parent:\n'
        for parent in page.parent_relation:
            if parent.is_active and parent.parent.is_active:
                output += f'\t- {parent.parent.url}\n'
        output += seperator + '\n'
        result += output
    
    with open(filename, 'w') as f:
        f.write(result)