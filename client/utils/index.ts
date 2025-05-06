import { QuerySuggestion, SearchHistory, SearchQuery, SearchResult } from "@/types"
import { getCookies } from "./cookie"

const debounceDelay = 500

export const debounce = <T extends unknown[]>(
    callback: (...args: T) => void,
    delay: number = debounceDelay,
) => {
    let timeoutTimer: ReturnType<typeof setTimeout>;

    return (...args: T) => {
        clearTimeout(timeoutTimer);

        timeoutTimer = setTimeout(() => {
            callback(...args);
        }, delay);
    };
};

export const castHistoryToQuery = (history: any): SearchQuery => {
    let s = {
        ...history,
        webpages: undefined,
        original_query_vector: undefined,
        modified_query_vector: undefined,
        date: undefined,
    }
    return s
}

export const objToUrl = (json: any) => {
    return JSON.stringify(json)
}

export const urlToObj = (url?: string) => {
    if (url === undefined) return undefined
    return JSON.parse(url.replaceAll('%20', ' '))
}