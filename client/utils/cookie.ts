'use server'

import { SearchHistory } from "@/types"
import { cookies } from "next/headers"

let history: SearchHistory[] | undefined = undefined

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