export type WebpageDetail = {
    webpage_id: number,
    url: string,
    title: string,
    last_modified_date: string,
    size: number,
    top_tfs: [string, number, number][],
    top_tfidfs: [string, number, number][],
    parents: string[],
    children: string[],
    modified_score: number,
    original_score: number
}

export type QueryVector = Record<string, [number, number]>

export type SearchResult = {
    webpages: [WebpageDetail, number][]
    original_query_vector: QueryVector
    modified_query_vector: QueryVector
}

export type QuerySuggestion = {
    similar_queries?: [string, number][]
    co_occuring_words?: [string, number, number][]
    relevant_words?: [string, number, number][]
    fuzzy_matched_words?: [string, number, number][]
}

export type WebpageHistory = WebpageDetail & {
    relevance: number
    clicked: boolean
    likeState: 'liked' | 'disliked' | 'none'
}

export type BasicSearchHistory = {
    date: string
    original_query_vector: QueryVector
    modified_query_vector: QueryVector
    webpages: WebpageHistory[]
}

export type SimpleSearchHistory = BasicSearchHistory & SimpleSearchQuery
export type AdvancedSearchHistory = BasicSearchHistory & SingleSearchQuery
export type JoinedSearchHistory = BasicSearchHistory & JoinedSearchQuery
export type SearchHistory = SimpleSearchHistory | AdvancedSearchHistory | JoinedSearchHistory

export type SimpleSearchQuery = {
    query: string
    type: 'simple'
}

export type SingleSearchQuery = {
    query?: string
    title_any?: [string, number][]
    title_all?: [string, number][]
    title_not?: [string, number][]
    body_any?: [string, number][]
    body_all?: [string, number][]
    body_not?: [string, number][]
    page_any?: [string, number][]
    page_all?: [string, number][]
    page_not?: [string, number][]
    from_date?: string
    to_date?: string
    type: 'single'
}

export type JoinedSearchQuery = {
    queries: SingleSearchQuery[]
    type: 'merged' | 'subquery'
}

export type SearchQuery = SingleSearchQuery | JoinedSearchQuery | SimpleSearchQuery