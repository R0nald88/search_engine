'use client'

import React, { useEffect, useState } from "react"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "../ui/command"
import Link from "next/link"
import { Button } from "../ui/button"
import { QuerySuggestion } from "@/types"
import { debounce, objToUrl } from "@/utils"
import { suggestQuery } from "@/utils/api"

type SearchBoxProps = {
    query?: string
    setQuery?: (query: string) => void
    open?: boolean,
    setOpen?: (open: boolean) => void
    alignment?: 'vertical' | 'horizontal'
    needSearchBtn?: boolean
    needHistoryBtn?: boolean
}

const replaceQuery = (query: string, suggestion: string): string => {
    const queryTerms = query.trim().split(' ')
    queryTerms.pop()
    return queryTerms.join(' ') + ' ' + suggestion.trim()
}

const addQuery = (query: string, suggestion: string): string => {
    return query.trim() + ' ' + suggestion.trim()
}

const SearchBox: React.FC<SearchBoxProps> = ({
    query = '',
    setQuery = () => {},
    open = true, 
    setOpen = () => {},
    alignment = 'horizontal',
    needSearchBtn = true,
    needHistoryBtn = false
}) => {
    const [suggestions, setSuggestions] = useState<QuerySuggestion>({})
    const [innerQuery, setInnerQuery] = useState<string>(query)

    const handleQueryChange = (newQuery: [string, number]): void => {
        setQuery(newQuery[0])
        setInnerQuery(newQuery[0])
    }

    useEffect(() => {
        setInnerQuery(query)
    }, [query])

    useEffect(() => {
        if (innerQuery.trim() === '') {
            setSuggestions({})
            return
        }
        const id = setTimeout(() => suggestQuery(innerQuery).then(v => setSuggestions(v)), 500)
        return () => clearTimeout(id)
    }, [innerQuery])

    return (
        <div 
            className={
                `flex flex-col ${alignment === 'horizontal' ? 'sm:flex-row' : ''} gap-5 w-full`
            }>
            <Command 
                className={
                    `rounded-lg border shadow-md w-full sm:h-50 
                    ${alignment === 'horizontal' ? 'flex-7' : ''}` 
                }
                shouldFilter={false}
                onFocus={() => setOpen(true)}
            >
                <CommandInput 
                    placeholder="Input Query to Search" 
                    value={innerQuery}
                    onValueChange={(s) => handleQueryChange([s, 0])} />
                
                {   open &&
                    <CommandList>
                        <CommandEmpty>No Query Suggested.</CommandEmpty>

                        <SuggestionItem
                            heading="Similar Queries"
                            suggestions={suggestions.simialar_queries}
                            mapping={(suggestion) => suggestion}
                            handleQueryChange={handleQueryChange} />

                        <SuggestionItem
                            heading="Fuzzy-Matched Terms"
                            suggestions={suggestions.fuzzy_matched_words}
                            mapping={(suggestion) => replaceQuery(innerQuery, suggestion)}
                            handleQueryChange={handleQueryChange} />

                        <SuggestionItem
                            heading="Relevant Terms"
                            suggestions={suggestions.relevant_words}
                            mapping={(suggestion) => addQuery(innerQuery, suggestion)}
                            handleQueryChange={handleQueryChange} />

                        <SuggestionItem
                            heading="Co-occuring Terms"
                            suggestions={suggestions.co_occuring_words}
                            mapping={(suggestion) => addQuery(innerQuery, suggestion)}
                            handleQueryChange={handleQueryChange} />
                    </CommandList>
                }
            </Command>

            {
                needSearchBtn && 
                <div className={
                    `flex flex-col gap-3 w-full 
                    ${alignment === 'horizontal' ? 'flex-3' : 'sm:flex-row'}`
                }>
                    <Button 
                        className={`w-full ${alignment === 'horizontal' ? '' : 'flex-1'}`} 
                        disabled={innerQuery.trim().length == 0}>
                        <Link
                            target="_blank"
                            rel='noreferrer noopener'
                            href={'/search?query=' + objToUrl({ type: 'simple', query: innerQuery.trim() })} className="w-full text-center">
                            Search
                        </Link>
                    </Button>
                    <Button 
                        className={`w-full ${alignment === 'horizontal' ? '' : 'flex-1'}`} 
                        variant={'outline'}
                    ><Link href={'/advanced_search_form'} className="w-full text-center">
                        Advanced Search
                    </Link></Button>
                    {
                        needHistoryBtn && 
                        <Button 
                            className={`w-full ${alignment === 'horizontal' ? '' : 'flex-1'}`} 
                            variant={'outline'}
                        ><Link href={'/history'} className="w-full text-center">
                            Search History
                        </Link></Button>
                    }
                </div>
            }
        </div>
        
    )
}

export const SuggestionItem: React.FC<{
    heading: string
    suggestions?: [string, number, number][] | [string, number][]
    mapping: (suggestion: string) => string
    handleQueryChange: (query: [string, number]) => void
}> = ({
    heading,
    suggestions,
    mapping,
    handleQueryChange
}) => {
    if (suggestions == null || suggestions?.length === 0) return <></>
    return (
        <CommandGroup heading={heading}>
            {
                suggestions.map((val) => (
                    <CommandItem 
                        key={val[0]} 
                        onSelect={() => handleQueryChange([mapping(val[0]), val[1]])}
                    >
                        {mapping(val[0])}
                    </CommandItem>
                ))
            }
            <CommandSeparator />
        </CommandGroup>
    )
}

export default SearchBox