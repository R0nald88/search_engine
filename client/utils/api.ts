'use server'

import { QuerySuggestion, SearchQuery, SearchResult } from "@/types"
import { getCookies } from "./cookie"

const api_url = 'http://127.0.0.1:8000'

export const search = async (query: SearchQuery): Promise<SearchResult> => {
    const cookie = await getCookies()
    let url = ''
    let body = {}

    if (['single', 'simple'].includes(query.type)) {
        url = `${api_url}/search`
        body = {
            query: { ...query },
            cookies: cookie
        }
    } else {
        url = `${api_url}/joined_search`
        body = {
            queries: { ...query },
            cookies: cookie
        }
    }

    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST',
            body: JSON.stringify(body)
        })

        if (!response.ok) {
            throw new Error('Fetch failed')
        }
        
        const data: SearchResult = await response.json()
        return data
    } catch(e) {
        return {
            original_query_vector: {},
            modified_query_vector: {},
            webpages: [
                [{
                    webpage_id: 0,
                    url: 'www.google.com',
                    title: 'Google',
                    last_modified_date: 'fgdsd',
                    size: 213,
                    top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
                    top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
                    parents: ['gdg', 'trb', 'fdss'],
                    children: ['gdg', 'trb', 'fdss'],
                    modified_score: 40,
                    original_score: 40
                }, 40]
            ] 
        }
    }
}

export const suggestQuery = async (query: string): Promise<QuerySuggestion> => {
    if (query.trim().length === 0) {
        return {}
    }

    const cookie = await getCookies()

    try {
        const response = await fetch(`${api_url}/suggest_query`, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST',
            body: JSON.stringify({
                query: query,
                cookies: cookie
            })
        })
    
        if (!response.ok) throw new Error('Failed Fetching')
        const json = await response.json()
        return json
    } catch (e) {
        return {
            simialar_queries: [
                ["example query", 0.9],
                ["another example", 0.8],
            ],
            co_occuring_words: [
                ["co-occuring term", 0.7, 0.6],
                ["another co-occuring", 0.5, 0.4],
            ],
            relevant_words: [
                ["relevant term", 0.3, 0.2],
                ["another relevant", 0.1, 0.05],
            ],
            fuzzy_matched_words: [
                ["fuzzy term", 0.9, 0.8],
                ["another fuzzy", 0.7, 0.6],
            ]
        }
    }
}