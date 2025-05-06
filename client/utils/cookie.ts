'use server'

import { SearchHistory } from "@/types"
import { cookies } from "next/headers"

let history: SearchHistory[] | undefined = [
    {
        type: 'simple',
        query: 'query',
        date: '543',
        original_query_vector: {},
        modified_query_vector: {},
        webpages: [{
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            relevance: 0,
            clicked: true,
            likeState: 'liked',
            modified_score: 40,
            original_score: 40
        },
        {
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            relevance: 0,
            clicked: true,
            likeState: 'liked',
            modified_score: 40,
            original_score: 40
        },
        {
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            relevance: 0,
            clicked: true,
            likeState: 'liked',
            modified_score: 40,
            original_score: 40
        }
    ]
        
    },
    {
        type: 'simple',
        query: 'query',
        date: '54433',
        original_query_vector: {},
        modified_query_vector: {},
        webpages: [{
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            relevance: 0,
            clicked: true,
            likeState: 'liked',
            modified_score: 40,
            original_score: 40
        }]
        
    },
    {
        type: 'simple',
        query: 'query',
        date: '54r3d',
        original_query_vector: {},
        modified_query_vector: {},
        webpages: [{
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            relevance: 0,
            clicked: true,
            likeState: 'liked',
            modified_score: 40,
            original_score: 40
        }]
        
    },
]

export const getCookies = async (): Promise<SearchHistory[]> => {
    if (history === undefined) {
        const cookieStore = await cookies()
        if (cookieStore.has('history')) {
            let h = cookieStore.get('history')
            if (h === undefined) {
                history = []
            } else {
                history = JSON.parse(h.value) as SearchHistory[]
            }
        } else {
            history = []
        }
    }
    return history
}

export const setCookies = async (h: SearchHistory[]) => {
    history = h
    const cookieStore = await cookies()
    cookieStore.set('history', JSON.stringify(history), {secure: true, httpOnly: true, path: '/'})
}

export const addCookies = async (h: SearchHistory | SearchHistory[]): Promise<number> => {
    let history = await getCookies()
    if (Array.isArray(h)) {
        if (history === undefined) history = h
        else history = history.concat(h)
    } else {
        if (history === undefined) history = [h]
        else history.push(h)
    }
    await setCookies(history)
    return history.length - 1
}

export const queryCookies = async (types: ('simple' | 'single' | 'merged' | 'subquery')[]): Promise<SearchHistory[]> => {
    let h = await getCookies()
    return h.filter(a => types.includes(a.type))
}

export const setSingleCookie = async (history: SearchHistory, index: number) => {
    let h = await getCookies()
    h[index] = history
    await setCookies(h)
}