'use client'

import {
    Command,
    CommandDialog,
    CommandEmpty,
    CommandInput,
    CommandList,
} from "@/components/ui/command"

import AdvancedSearchCard from "@/components/shared/AdvancedSearchCard"
import { Label } from "@/components/ui/label"
import { JoinedSearchQuery, QuerySuggestion, SearchQuery, SingleSearchQuery } from "@/types"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { SuggestionItem } from "@/components/shared/SearchBox"
import { Button } from "@/components/ui/button"
import { castHistoryToQuery, debounce, objToUrl, urlToObj } from "@/utils"
import { suggestQuery } from "@/utils/api"
import SelectQueryHistoryDialog from "@/components/shared/SelectQueryHistoryDialog"
import { toast } from "sonner"

const validateQuery = (searchQuery: JoinedSearchQuery): SearchQuery | string => {
    if (searchQuery.queries.length <= 0) return 'Make sure at least 1 query is inputted.'

    for (let q of searchQuery.queries) {
        if ((q.query === undefined || q.query.trim().length <= 0) && 
            (q.body_all === undefined || q.body_all.length <= 0) && 
            (q.body_any === undefined || q.body_any.length <= 0) &&
            (q.body_not === undefined || q.body_not.length <= 0) &&
            (q.title_all === undefined || q.title_all.length <= 0) &&
            (q.title_any === undefined || q.title_any.length <= 0) &&
            (q.title_not === undefined || q.title_not.length <= 0) &&
            (q.page_all === undefined || q.page_all.length <= 0) &&
            (q.page_any === undefined || q.page_any.length <= 0) &&
            (q.page_not === undefined || q.page_not.length <= 0)
        )
            return 'Make sure all queries has \"Query\" field inputted or at least 1 keyword selected.'
    }

    if (searchQuery.queries.length === 1) {
        let q = searchQuery.queries[0]
        if (!(q.query === undefined || q.query.trim().length <= 0) && 
            (q.body_all === undefined || q.body_all.length <= 0) && 
            (q.body_any === undefined || q.body_any.length <= 0) &&
            (q.body_not === undefined || q.body_not.length <= 0) &&
            (q.title_all === undefined || q.title_all.length <= 0) &&
            (q.title_any === undefined || q.title_any.length <= 0) &&
            (q.title_not === undefined || q.title_not.length <= 0) &&
            (q.page_all === undefined || q.page_all.length <= 0) &&
            (q.page_any === undefined || q.page_any.length <= 0) &&
            (q.page_not === undefined || q.page_not.length <= 0)
        )
            return { type: 'simple', query: q.query }
        return { ...q, type: 'single' }
    }

    if (searchQuery.type === 'merged' && searchQuery.queries.length > 5) {
        return 'Too much queries to merge. Only at most 5 queries can be merged.'
    }

    if (searchQuery.type === 'subquery' && searchQuery.queries.length > 2) {
        return 'Only 1 subquery is allowed.'
    }
    return searchQuery
}

const KeywordSearchDialog: React.FC<{
    open: boolean
    setOpen: (o: boolean) => void
    onCommandDialogKeywordClick: (word: [string, number]) => void
    eliminateWords: [string, number][]
}> = ({ open, setOpen, onCommandDialogKeywordClick, eliminateWords }) => {
    const [input, setInput] = useState<string>('')
    const [suggestion, setSuggestions] = useState<QuerySuggestion>({})
    const e = eliminateWords.map(v => v[1])
    const handleQueryChange = (s: [string, number]) => {
        onCommandDialogKeywordClick(s)
        setInput('')
        setOpen(false)
    }
    
    useEffect(() => {
        if (input.trim() === '') {
            setSuggestions({})
            return
        }
        const id = setTimeout(() => suggestQuery(input).then(v => setSuggestions(v)))
        return () => clearTimeout(id)
    }, [input])

    return (
        <CommandDialog open={open} onOpenChange={setOpen}>
            <Command shouldFilter={false}>
                <CommandInput 
                    placeholder="Type something to search..." 
                    value={input}
                    onValueChange={(s) => {
                        setInput(s)
                    }}
                    
                />
                <CommandList>
                    <CommandEmpty>No results found.</CommandEmpty>
                    <SuggestionItem 
                        heading='Fuzzy-matched Words'
                        suggestions={suggestion.fuzzy_matched_words?.filter(a => !e.includes(a[1]))}
                        mapping={s => s}
                        handleQueryChange={handleQueryChange}
                    />
                    <SuggestionItem 
                        heading='Relevant Words'
                        suggestions={suggestion.relevant_words?.filter(a => !e.includes(a[1]))}
                        mapping={s => s}
                        handleQueryChange={handleQueryChange}
                    />
                    <SuggestionItem 
                        heading='Co-occuring Words'
                        suggestions={suggestion.co_occuring_words?.filter(a => !e.includes(a[1]))}
                        mapping={s => s}
                        handleQueryChange={handleQueryChange}
                    />
                </CommandList>
            </Command>
        </CommandDialog>
    )
}

const toJoinedSearchQuery = (query: SearchQuery | undefined): JoinedSearchQuery => {
    return query === undefined ? { queries: [{ type: 'single' }], type: 'merged' } :
        query.type === 'simple' ? { queries: [{ type: "single", query: query.query }], type: 'merged' } :
            query.type === 'single' ? { queries: [query], type: 'merged' } : query
}

const AdvancedSearchFormPage: React.FC<{}> = () => {
    const router = useRouter()
    const [open, setOpen] = useState<boolean>(false)
    const [onCommandDialogKeywordClick, setOnCommandDialogKeywordClick] = 
        useState<(word: [string, number]) => void>(() => () => {})
    const [eliminateWords, setEliminateWords] = useState<[string, number][]>([])
    const searchParams = useSearchParams()
    const query: SearchQuery | undefined = urlToObj(searchParams.get('query') ?? undefined)
    const [searchQuery, setSearchQuery] = useState<JoinedSearchQuery>(toJoinedSearchQuery(query))

    return (
        <div
            className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-7 sm:p-17 sm:pr-45 sm:pl-45 font-[family-name:var(--font-geist-sans)]">
            <KeywordSearchDialog 
                open={open} setOpen={setOpen} 
                eliminateWords={eliminateWords} 
                onCommandDialogKeywordClick={onCommandDialogKeywordClick}/>
            <Label className="text-2xl font-bold text-start w-full">Advanced Search Query</Label>
            {
                searchQuery.queries.map((v, i) => {
                    return <AdvancedSearchCard
                        searchQuery={v}
                        key={i}
                        setSearchQuery={(p) => {
                            if (typeof p === 'function') {
                                setSearchQuery(prev => {
                                    prev.queries[i] = p(prev.queries[i])
                                    return { ...prev }
                                })
                            } else {
                                searchQuery.queries[i] = { ...p }
                                setSearchQuery({ ...searchQuery })
                            }
                        }}
                        onDelete={() => {
                            setSearchQuery(prev => {
                                prev.queries = prev.queries.filter((a, j) => i !== j)
                                return { ...prev }
                            })
                        }}
                        index={i} type={i === 0 ? 'none' : searchQuery.type} 
                        setOpen={setOpen}
                        setEliminateWords={setEliminateWords}
                        setOnCommandDialogKeywordClick={setOnCommandDialogKeywordClick}
                    />
                })
            }
            <div className="flex flex-row gap-3 w-full">
                <Button 
                    variant={'outline'} 
                    className="flex-1"
                    onClick={() => {
                        searchQuery.queries = [ ...searchQuery.queries, { type: 'single' } ]
                        searchQuery.type = 'merged'
                        setSearchQuery({ ...searchQuery })
                    }}
                    disabled={ 
                        (searchQuery.type === 'subquery' && searchQuery.queries.length > 1) || 
                        (searchQuery.type === 'merged' && searchQuery.queries.length >= 5) 
                    }
                >Add Merging Query</Button>
                <Button 
                    variant={'outline'}
                    className="flex-1"
                    onClick={() => {
                        searchQuery.queries = [ ...searchQuery.queries, { type: 'single' } ]
                        searchQuery.type = 'subquery'
                        setSearchQuery({ ...searchQuery })
                    }}
                    disabled={ 
                        (searchQuery.type === 'merged' && searchQuery.queries.length > 1) ||
                        (searchQuery.type === 'subquery' && searchQuery.queries.length >= 2)
                    }
                >Add Subquery</Button>
                <SelectQueryHistoryDialog
                    isMultiple={false}
                    includeJoinedQuery
                    onSelected={(v, setOpen) => {
                        setSearchQuery(toJoinedSearchQuery(v[0]))
                        setOpen(false)
                    }}
                >
                    <Button variant={'outline'} className="flex-1">Import Single Query</Button>
                </SelectQueryHistoryDialog>
                <SelectQueryHistoryDialog
                    isMultiple={true}
                    includeJoinedQuery={false}
                    onSelected={(v, setOpen) => {
                        if (v.length > 5) toast('Excess Query Selected', {
                            description: 'More than 5 queries selected. Please unselect some for merged searching.'
                        })
                        else {
                            let q: JoinedSearchQuery = {
                                type: 'merged',
                                queries: v.map(a => {
                                    console.log(a)
                                    if (a.type === 'single') return a
                                    else if (a.type === 'simple') return {
                                        query: a.query,
                                        type: 'single'
                                    } as SingleSearchQuery
                                    else return { type: 'single' } as SingleSearchQuery
                                }).filter(a => a !== undefined)
                            }
                            console.log(q)
                            setSearchQuery({ ...q })
                            setOpen(false)
                        }
                    }}
                >
                    <Button variant={'outline'} className="flex-1">Merge Multiple Query</Button>
                </SelectQueryHistoryDialog>
            </div>
            <Button 
                onClick={() => {
                    const query = validateQuery(searchQuery)
                    if (typeof(query) === 'string') toast('Query Error', {description: query})
                    else {
                        router.push('/search?query=' + objToUrl(castHistoryToQuery(query)))
                    }
                }}
                className="w-full"
            >Search</Button>
        </div>
    )
}

export default AdvancedSearchFormPage
