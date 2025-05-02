from pydantic import BaseModel, Field
from typing import Any
from fastapi import FastAPI
from search import search, joined_search, suggest_query, Session

app = FastAPI()

class SearchParams(BaseModel):
    query: str
    cookies: list[dict[str, Any]] = list()
    title_any: set[int] = set()
    title_all: set[int] = set()
    title_not: set[int] = set()
    body_any: set[int] = set()
    body_all: set[int] = set()
    body_not: set[int] = set()
    page_any: set[int] = set()
    page_all: set[int] = set()
    page_not: set[int] = set()
    from_date: str | None = None
    to_date: str | None = None
@app.get("/search")
def search_query(parmas: SearchParams):
    with Session() as db:
        webpages, original_query_vector, modified_query_vector = search(
            query=parmas.query,
            cookies=parmas.cookies,
            title_any=parmas.title_any,
            title_all=parmas.title_all,
            title_not=parmas.title_not,
            body_any=parmas.body_any,
            body_all=parmas.body_all,
            body_not=parmas.body_not,
            page_any=parmas.page_any,
            page_all=parmas.page_all,
            page_not=parmas.page_not,
            from_date=parmas.from_date,
            to_date=parmas.to_date,
            db=db
        )

        return {
            'webpages': webpages,
            'original_query_vector': original_query_vector,
            'modified_query_vector': modified_query_vector,
        }

class JoinedSearchParams(BaseModel):
    queries: dict[str, Any]
    cookies: list[dict[str, Any]] = list()
@app.get("/joined_search")
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
@app.get("/suggest_query")
def suggest_query_api(params: SuggestQueryParams):
    with Session() as db:
        fuzzy_matched_keywords, pmi_words, relevant_words, sim_queries = suggest_query(
            query=params.query,
            cookies=params.cookies,
        )

        return {
            'fuzzy_matched_words': fuzzy_matched_keywords,
            'co_occuring_words': pmi_words,
            'relevant_words': relevant_words,
            'similar_queries': sorted(sim_queries.items(), key=lambda x: x[1], reverse=True),
        }

