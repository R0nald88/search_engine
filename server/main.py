from pydantic import BaseModel, Field
from typing import Any
from fastapi import FastAPI
from search import search, joined_search, suggest_query, Session

app = FastAPI()

class SearchParams(BaseModel):
    query: dict[str, Any] = dict()
    cookies: list[dict[str, Any]] = list()
@app.post("/search")
def search_query(parmas: SearchParams):
    with Session() as db:
        webpages, original_query_vector, modified_query_vector = search(
            query=parmas.query.get('query', ''),
            cookies=parmas.cookies,
            title_any=parmas.query.get('title_any', list()),
            title_all=parmas.query.get('title_all', list()),
            title_not=parmas.query.get('title_not', list()),
            body_any=parmas.query.get('body_any', list()),
            body_all=parmas.query.get('body_all', list()),
            body_not=parmas.query.get('body_not', list()),
            page_any=parmas.query.get('page_any', list()),
            page_all=parmas.query.get('page_all', list()),
            page_not=parmas.query.get('page_not', list()),
            from_date=parmas.query.get('from_date', None),
            to_date=parmas.query.get('to_date', None)
        )

        return {
            'webpages': webpages,
            'original_query_vector': original_query_vector,
            'modified_query_vector': modified_query_vector,
        }

class JoinedSearchParams(BaseModel):
    queries: dict[str, Any]
    cookies: list[dict[str, Any]] = list()
@app.post("/joined_search")
def joined_search_query(params: JoinedSearchParams):
    with Session() as db:
        webpages, original_query_vector, modified_query_vector = joined_search(
            queries=params.queries,
            cookies=params.cookies,
        )

        return {
            'webpages': webpages,
            'original_query_vector': original_query_vector,
            'modified_query_vector': modified_query_vector,
        }

class SuggestQueryParams(BaseModel):
    query: str
    cookies: list[dict[str, Any]] = list()
@app.post("/suggest_query")
def suggest_query_api(params: SuggestQueryParams):
    with Session() as db:
        fuzzy_matched_keywords, pmi_words, relevant_words, sim_queries = suggest_query(
            query=params.query,
            cookies=params.cookies,
            db=db
        )

        return {
            'fuzzy_matched_words': fuzzy_matched_keywords,
            'co_occuring_words': pmi_words,
            'relevant_words': relevant_words,
            'similar_queries': sim_queries,
        }

