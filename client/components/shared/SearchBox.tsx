'use client'

import React, { useState } from "react"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "../ui/command"
import Link from "next/link"
import { Button } from "../ui/button"
import { QuerySuggestion } from "@/types"

type SearchBoxProps = {
    query?: string
    setQuery?: (query: string) => void
    open?: boolean,
    setOpen?: (open: boolean) => void
    alignment?: 'vertical' | 'horizontal'
    needSearchBtn?: boolean
    needHistoryBtn?: boolean
}

const eSuggestion: QuerySuggestion = {
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

const replaceQuery = (query: string, suggestion: string): string => {
    const queryTerms = query.trim().split(' ')
    queryTerms.pop()
    return queryTerms.join(' ') + ' ' + suggestion.trim()
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
    const [suggestions, setSuggestions] = useState<QuerySuggestion>(eSuggestion)
    const [innerQuery, setInnerQuery] = useState<string>(query)

    const handleQueryChange = (newQuery: string): void => {
        setQuery(newQuery)
        setInnerQuery(newQuery)
    }

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
                    onValueChange={handleQueryChange} />
                
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
                            mapping={(suggestion) => replaceQuery(innerQuery, suggestion)}
                            handleQueryChange={handleQueryChange} />

                        <SuggestionItem
                            heading="Co-occuring Terms"
                            suggestions={suggestions.co_occuring_words}
                            mapping={(suggestion) => replaceQuery(innerQuery, suggestion)}
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
                        <Link href={{
                            pathname: '/search',
                            query: {
                                query: innerQuery.replaceAll(' ', '_')
                            }
                        }} className="w-full text-center">
                            Search
                        </Link>
                    </Button>
                    <Button 
                        className={`w-full ${alignment === 'horizontal' ? '' : 'flex-1'}`} 
                        variant={'outline'}
                    >Advanced Search</Button>
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

const SuggestionItem: React.FC<{
    heading: string
    suggestions?: [string, number, number][] | [string, number][]
    mapping: (suggestion: string) => string
    handleQueryChange: (query: string) => void
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
                        onSelect={() => handleQueryChange(mapping(val[0]))}
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