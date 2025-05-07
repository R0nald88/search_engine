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
            webpages: [] 
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
        return {}
    }
}