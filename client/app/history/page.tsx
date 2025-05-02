import SearchHistoryTable from "@/components/shared/SearchHistoryTable";
import SearchResultTable from "@/components/shared/SearchResultTable"
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label"
import { SearchHistory } from "@/types";
import { cookies } from "next/headers"
import { use } from 'react';

const HistoryPage: React.FC<{}> = () => {
    const cookieStore = use(cookies())
    const history = cookieStore.get('history')
    const queryHistory: SearchHistory[] = []

    return (
        <div 
            className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-7 sm:p-17 sm:pr-45 sm:pl-45 font-[family-name:var(--font-geist-sans)]">
            <Label className="text-xl font-bold text-start w-full">Search History</Label>
            <div className="w-full flex flex-row gap-3">
                <Label className="text-xl font-bold text-start flex-4">Search History</Label>
                <Button className="flex-1">Go to Search</Button>
                <Button className="flex-1" variant={'outline'}>Go to Advanced Search</Button>
            </div>
            <hr className='border-gray-300 w-full' />
            {queryHistory.map(a => <SearchHistoryTable data={a} />)}
        </div>
    )
}