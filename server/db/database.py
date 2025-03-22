from sqlalchemy import create_engine, and_, not_, update, or_, func
from sqlalchemy.orm import sessionmaker

try: from schemas import *
except: from .schemas import *

from typing import Callable, Any
import sqlalchemy.dialects.sqlite as sqlite

db_uri = "sqlite:///./server/db/project.db"
engine = create_engine(db_uri, echo=True) # Create a SQLAlchemy engine , echo=True
Session = sessionmaker(bind=engine) # Create a session to interact with the database

def create_database(restore: bool = False):
    global engine
    if restore: Base().metadata.drop_all(bind=engine)
    Base().metadata.create_all(bind=engine)

def set_index(
    indexes: list[Index], 
    ignore: bool = False,
    delete_unindexed_words: bool = False, 
    db = Session()) -> None:
    
    for i in indexes: i.index_id = f'{i.webpage_id}-{i.word_id}-{1 if i.is_title else 0}'

    upsert(
        sess=db, cls=Index, inputs=indexes,
        func=Index.to_basic_dict,
        ignore=ignore,
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
    ignore: bool = False,
    delete_unfounded_relationship: bool = False,
    db = Session()) -> None:

    for r in relationship: r.relate_id = f'{r.parent_id}-{r.child_id}'

    upsert(
        sess=db, cls=Relationship, inputs=relationship,
        func=Relationship.to_basic_dict,
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
        func=Webpage.to_basic_dict,
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
    func: Callable[[Any], dict[str, Any]],
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

def write_webpage_infos(
    limit: int = -1, db = Session(), write_parent: bool = True,
    keyword_limit: int = 10,
    relationship_limit: int = 10,
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
        for index in page.indexes:
            if limit >= keyword_limit: break
            if not index.is_title: continue
            output += f'\t- \"{index.keyword.word}\" with frequency: {index.frequency}\n'
            limit += 1

        output += 'Body Keywords:\n'
        limit = 0
        for index in page.indexes:
            if limit >= keyword_limit: break
            if index.is_title: continue
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