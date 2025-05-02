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
}

export type QueryVector = Record<string, [number, number]>

export type SearchResult = {
    webpages: [WebpageDetail, number][]
    original_query_vector: QueryVector
    modified_query_vector: QueryVector
}

export type QuerySuggestion = {
    simialar_queries?: [string, number][]
    co_occuring_words?: [string, number, number][]
    relevant_words?: [string, number, number][]
    fuzzy_matched_words?: [string, number, number][]
}

export type WebpageHistory = WebpageDetail & {
    relevance: number
    clicked: boolean
    likeState: 'liked' | 'disliked' | 'none'
}

export type SearchHistory = {
    query: string
    date: string
    original_query_vector: QueryVector
    modified_query_vector: QueryVector
    webpages: WebpageHistory[]
}