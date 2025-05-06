'use client'

import QueryLabel from "@/components/shared/QueryLabel"
import SearchBox from "@/components/shared/SearchBox"
import SearchResultTable, { SearchResultTableData } from "@/components/shared/SearchResultTable"
import Seperator from "@/components/shared/Seperator"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { SearchHistory, SearchQuery, SingleSearchQuery } from "@/types"
import { objToUrl, urlToObj } from "@/utils"
import { search } from "@/utils/api"
import { addCookies, setSingleCookie } from "@/utils/cookie"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

const SearchResultPage: React.FC<{}> = () => {
    const searchParams = useSearchParams()
    const router = useRouter()
    const [data, setData] = useState<SearchResultTableData[] | undefined>(undefined)
    const [index, setIndex] = useState<number>(-1)
    const [history, setHistory] = useState<SearchHistory | undefined>(undefined)
    const searchQuery: SearchQuery | undefined = urlToObj(searchParams.get('query') ?? undefined)

    useEffect(() => {
        if (searchQuery === undefined) return
        search(searchQuery).then((v) => {
            const d: SearchResultTableData[] = v.webpages.map((w, i) => ({
                detail: {
                    ...w[0],
                    clicked: false,
                    setClicked: (c) => setData(prev => {
                        if (prev === undefined) return undefined
                        prev[i].detail = { ...prev[i].detail, clicked: c }
                        return [...prev]
                    }),
                    likeState: 'none',
                    setLikeState: (likeState, detail) => setData(prev => {
                        if (prev === undefined) return undefined
                        prev[i].detail = { ...prev[i].detail, likeState: likeState }
                        return [...prev]
                    }),
                    getSimilarPage: (detail) => {
                        const query: SingleSearchQuery = {
                            type: 'single',
                            page_any: detail.top_tfs.map(v => [v[0], v[1]]),
                        }
                        router.push('/search?query=' + objToUrl(query))
                    }
                },
                score: w[1],
                original_score: w[0].original_score
            }))
            setData(d)

            const history: SearchHistory = {
                ...searchQuery,
                original_query_vector: v.original_query_vector,
                modified_query_vector: v.modified_query_vector,
                date: new Date().toUTCString(),
                webpages: []
            }

            setHistory(history)
            addCookies(history).then(v => setIndex(v))
        })
    }, [])

    useEffect(() => {
        if (data === undefined || index < 0 || history === undefined) return
        const id = setTimeout(() => setSingleCookie({
            ...history,
            webpages: data.filter(
                d => d.detail.likeState === 'liked' || d.detail.clicked
            ).map(d => ({
                ...d.detail,
                setClicked: undefined,
                setLikeState: undefined,
                getSimilarPage: undefined,
                relevance: d.detail.likeState === 'liked' || d.detail.clicked ? 1 : 0
            }))
        }, index), 500)
        return () => clearTimeout(id)
    }, [data])

    return (
        <div 
            className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-7 sm:p-17 sm:pr-45 sm:pl-45 font-[family-name:var(--font-geist-sans)]">
            {
                searchQuery?.type === 'simple' || searchQuery === undefined ?
                <>
                    <Label className="text-2xl font-bold text-start w-full">Query</Label>
                    <SearchBox alignment="horizontal" needSearchBtn query={searchQuery?.query} needHistoryBtn/>
                </> :
                <div className="w-full flex flex-row gap-5">
                    <div className="flex-7"><QueryLabel searchQuery={searchQuery} biggerTitle/></div>
                    <div className="flex flex-3 flex-col gap-3">
                        <Button className="w-full">
                            <Link href={'/advanced_search_form?query=' + searchParams.get('query')}>Advanced Search</Link>
                        </Button>
                        <Button className="w-full" variant={'outline'}>
                            <Link href={'/'}>Go to Search</Link>
                        </Button>
                        <Button className="w-full" variant={'outline'}>
                            <Link href={'/history'}>Search History</Link>
                        </Button>
                    </div>
                </div>
            }
            
            <Seperator />
            <Label className="text-xl font-bold text-start w-full">Search Result</Label>
            <SearchResultTable data={data ?? []} isLoading={data === undefined} />
        </div>
    )
}

export default SearchResultPage