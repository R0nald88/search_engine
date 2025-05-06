import { SearchQuery, SingleSearchQuery } from "@/types"
import { Label } from "../ui/label"
import React from "react"

const KeywordList = ({hint, keywords}: {hint: string, keywords?: [string, number][]}) => {
    if (keywords === undefined) return <></>
    return <>
        - {hint}: {keywords.map(v => v[0]).join(', ')}<br/>
    </>
}

const SearchQueryDetail: React.FC<SingleSearchQuery> = (searchQuery) => (
    <>
        {
            searchQuery.from_date ? searchQuery.to_date ? 
            <>Date Range: From {searchQuery.from_date} to {searchQuery.to_date}<br/></> :
            <>Date Range: Starting from {searchQuery.from_date}<br/></> : 
            searchQuery.to_date ? <>Date Range: Until {searchQuery.to_date}<br/></> : <></>
        }
        <KeywordList keywords={searchQuery.title_any} hint='Title could conatain ANY of these'/>
        <KeywordList keywords={searchQuery.title_all} hint='Title must conatain ALL of these'/>
        <KeywordList keywords={searchQuery.title_not} hint='Title must NOT conatain any of these'/>
        <KeywordList keywords={searchQuery.body_any} hint='Body could conatain ANY of these'/>
        <KeywordList keywords={searchQuery.body_all} hint='Body must conatain ALL of these'/>
        <KeywordList keywords={searchQuery.body_not} hint='Body must NOT conatain any of these'/>
        <KeywordList keywords={searchQuery.page_any} hint='Webpage could conatain ANY of these'/>
        <KeywordList keywords={searchQuery.page_all} hint='Webpage must conatain ALL of these'/>
        <KeywordList keywords={searchQuery.page_not} hint='Webpage must NOT conatain any of these'/>
    </>
)

const QueryLabel: React.FC<{
    searchQuery: SearchQuery,
    time?: string,
    biggerTitle?: boolean
}> = ({searchQuery, time, biggerTitle = false}) => {
    if (searchQuery.type === 'simple' || searchQuery.type === 'single') {
        return (
            <div className="w-full flex flex-col gap-3">
                <Label className={`w-full ${biggerTitle ? 'text-2xl' : 'text-xl'} font-bold text-left`}>
                    {
                        searchQuery.query && searchQuery.query.trim().length > 0 ?
                        `Query: ${searchQuery.query}` :
                        'Keyword-based Query'
                    }
                </Label>
                <Label className="text-gray-500 w-full text-left">
                    <p>
                        { time && <>- Time: {time}<br/></> }
                        {  searchQuery.type === 'single' && <SearchQueryDetail {...searchQuery}/> }
                    </p>
                </Label>
            </div>
        )
    }

    return (
        <div className="w-full flex flex-col gap-3">
            <Label className={`w-full ${biggerTitle ? 'text-2xl' : 'text-xl'} font-bold text-left`}>
                {searchQuery.type === 'merged' ? `Merged Query` : `Subquery Searching`}
            </Label>
            {time && <Label className="text-gray-500 w-full text-left">Time: {time}</Label>}
            {
                searchQuery.queries.map((v, i) => (
                    <div key={i}>
                        <Label className="w-full font-bold text-left">
                            {
                                i === 0 ? 'Original Query' :
                                searchQuery.type === 'merged' ? `Merged Query ${i}` : `Subquery`
                            }
                        </Label>
                        <Label className="text-gray-500 w-full text-left">
                            <p>
                                <SearchQueryDetail {...v}/>
                            </p>
                        </Label>
                    </div>
                ))
            }
        </div>
    )
}

export default QueryLabel