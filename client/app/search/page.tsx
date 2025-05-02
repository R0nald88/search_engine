'use client'

import SearchBox from "@/components/shared/SearchBox"
import SearchResultTable, { SearchResultTableData } from "@/components/shared/SearchResultTable"
import { Label } from "@/components/ui/label"
import { useSearchParams } from "next/navigation"

const eSearchTableData: SearchResultTableData[] = [
    {
        score: 40,
        detail: {
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            likeState: 'none',
            getSimilarPage: (detail) => {},
            setLikeState: (likeState, detail) => {}
        }
    },
    {
        score: 40,
        detail: {
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            likeState: 'none',
            getSimilarPage: (detail) => {},
            setLikeState: (likeState, detail) => {}
        }
    },
    {
        score: 40,
        detail: {
            webpage_id: 0,
            url: 'www.google.com',
            title: 'Google',
            last_modified_date: 'fgdsd',
            size: 213,
            top_tfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            top_tfidfs: [['as', 30, 30], ['bs', 30, 30], ['cs', 80, 50]],
            parents: ['gdg', 'trb', 'fdss'],
            children: ['gdg', 'trb', 'fdss'],
            likeState: 'none',
            getSimilarPage: (detail) => {},
            setLikeState: (likeState, detail) => {}
        }
    },
] 

const SearchResultPage: React.FC<{}> = () => {
    const searchParams = useSearchParams()
    const query = searchParams.get('query')?.replaceAll('_', ' ')
    return (
        <div 
            className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-7 sm:p-17 sm:pr-45 sm:pl-45 font-[family-name:var(--font-geist-sans)]">
            <Label className="text-xl font-bold text-start w-full">Query</Label>
            <SearchBox alignment="horizontal" needSearchBtn query={query} needHistoryBtn/>
            <hr className='border-gray-300 w-full' />
            <Label className="text-xl font-bold text-start w-full">Search Result</Label>
            <SearchResultTable data={eSearchTableData} />
        </div>
    )
}

export default SearchResultPage