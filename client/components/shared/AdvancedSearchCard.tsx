'use client'

import { SingleSearchQuery } from "@/types"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../ui/card"
import { Label } from "@radix-ui/react-label"
import SearchBox from "./SearchBox"
import React from "react"
import { DatePicker } from "../ui/datepicker"
import KeywordBadge from "./KeywordBadge"
import Seperator from "./Seperator"
import { Button } from "../ui/button"
import SelectQueryHistoryDialog from "./SelectQueryHistoryDialog"

const addKeywords = (
    prev: SingleSearchQuery, 
    word: [string, number], 
    content: 'title' | 'body' | 'page',
    type: 'all' | 'any' | 'not'
) => {
    let a = prev[`${content}_${type}`]
    if (a === undefined) 
        prev[`${content}_${type}`] = [word]
    else 
        prev[`${content}_${type}`] = [...a, word]
    return { ...prev }
}

const formHintClassName = 'flex-2 p-2'
const fromHintTextClassName = 'text-start text-sm align-middle'
const formInputClassName = 'flex-7'

const KeywordList: React.FC<{
    searchQuery: SingleSearchQuery
    setSearchQuery: React.Dispatch<React.SetStateAction<SingleSearchQuery>>
    content: 'title' | 'body' | 'page'
    type: 'all' | 'any' | 'not'
    setOnCommandDialogKeywordClick: React.Dispatch<React.SetStateAction<(word: [string, number]) => void>>
    setEliminateWords: React.Dispatch<React.SetStateAction<[string, number][]>>
    setOpen: React.Dispatch<React.SetStateAction<boolean>>
}> = ({ searchQuery, setSearchQuery, content, type, setEliminateWords, setOnCommandDialogKeywordClick, setOpen }) => {

    return (
        <div className="w-full flex flex-row flex-wrap gap-3 p-2">
            {searchQuery[`${content}_${type}`]?.map((v, i) => (
                <KeywordBadge 
                    keyword={v[0]} 
                    key={i} 
                    onDelete={() => {
                        setSearchQuery(prev => {
                            prev[`${content}_${type}`] = prev[`${content}_${type}`]?.filter(o => o[0] != v[0])
                            return { ...prev }
                        })
                    }}/>
            ))}
            <Button onClick={() => {
                const keys = content === 'page' ? 
                    [
                        'page_any', 'page_all', 'page_not', 
                        'title_any', 'title_not', 'title_all',
                        'body_all', 'body_any', 'body_not',
                    ] as const:
                    [`${content}_any`, `${content}_all`, `${content}_not`] as const

                let eliminateWords: [string, number][] = []
                for (let t of keys) {
                    eliminateWords = eliminateWords.concat(searchQuery[t] ?? [])
                }
                console.log(eliminateWords)
                setEliminateWords(eliminateWords)
                setOnCommandDialogKeywordClick(() => (w: [string, number]) => {
                    setSearchQuery(addKeywords(searchQuery, w, content, type))
                    setOpen(false)
                })
                setOpen(true)
            }}>Add Keyword</Button>
        </div>
    )
}

const content = ['title', 'body', 'page'] as const
const combineType = ['any', 'all', 'not'] as const

const AdvancedSearchCard: React.FC<{
    searchQuery: SingleSearchQuery
    setSearchQuery: React.Dispatch<React.SetStateAction<SingleSearchQuery>>
    type: 'subquery' | 'merged' | 'none'
    index: number
    onDelete: () => void
    setOnCommandDialogKeywordClick: React.Dispatch<React.SetStateAction<(word: [string, number]) => void>>
    setEliminateWords: React.Dispatch<React.SetStateAction<[string, number][]>>
    setOpen: React.Dispatch<React.SetStateAction<boolean>>
}> = ({
    searchQuery,
    setSearchQuery,
    type, index, onDelete,
    setOpen, setOnCommandDialogKeywordClick, setEliminateWords
}) => {
    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle>
                    {
                        type === 'merged' ? 'Merge Query' :
                        type === 'subquery' ? 'Subquery' :
                        'Original Query'    
                    } {type === 'merged' ? index : ''}
                </CardTitle>
                <CardDescription>
                    {
                        type === 'merged' ? 'Query result to be merged with previous query' :
                        type === 'subquery' ? 'Search within the result of previous query' :
                        'Query for searching'
                    }
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="w-full flex flex-col gap-7">
                    <div className="flex flex-row">
                        <div className={formHintClassName}>
                            <Label className={fromHintTextClassName}>Query</Label>
                        </div>
                        <div className={formInputClassName}>
                            <SearchBox 
                                needHistoryBtn={false} needSearchBtn={false}
                                query={searchQuery.query}
                                setQuery={query => setSearchQuery((prev) => ({ ...prev, query: query }))}
                            />
                        </div>
                    </div>
                    <div className="flex flex-row">
                        <div className={formHintClassName}>
                            <Label className={fromHintTextClassName}>Date Range</Label>
                        </div>
                        <div className={formInputClassName}>
                            <DatePicker 
                                className="w-full"
                                setDateString={setSearchQuery}
                                dateString={searchQuery}
                            />
                        </div>
                    </div>
                    {
                        content.map(c => <div key={c}>
                            <Seperator />
                            {combineType.map(t => 
                                <div className="flex flex-row py-2" key={`${c}_${t}`}>
                                    <div className={formHintClassName}>
                                        <Label className={fromHintTextClassName}>
                                            {c === 'title' ? 'Title ' : c === 'body' ? 'Body ' : 'Webpage '} 
                                            {t === 'any' ? 'could contain ANY of these keywords' : t === 'all' ? 'must contain ALL of these keywords' : 'must NOT contain any of these keywords'}
                                        </Label>
                                    </div>
                                    <div className={formInputClassName}>
                                        <KeywordList 
                                            searchQuery={searchQuery} setSearchQuery={setSearchQuery}
                                            setOpen={setOpen}
                                            setEliminateWords={setEliminateWords}
                                            setOnCommandDialogKeywordClick={setOnCommandDialogKeywordClick}
                                            type={t} content={c}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>)
                    }
                </div>
            </CardContent>
            <CardFooter className="w-full flex flex-row gap-3">
                <SelectQueryHistoryDialog
                    isMultiple={false}
                    includeJoinedQuery={false}
                    onSelected={(q, setOpen) => {
                        if (q[0].type === 'single') {
                            setSearchQuery({ ...q[0] })
                            setOpen(false)
                        } else if (q[0].type === 'simple') {
                            setSearchQuery({
                                type: 'single', query: q[0].query
                            })
                            setOpen(false)
                        }
                    }}
                ><Button>Search from History</Button></SelectQueryHistoryDialog>
                {index !== 0 && <Button onClick={onDelete} variant={'outline'}>Delete</Button>}
            </CardFooter>
        </Card>
    )
}

export default AdvancedSearchCard