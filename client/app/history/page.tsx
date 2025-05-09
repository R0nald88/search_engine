import SearchHistoryTable from "@/components/shared/SearchHistoryTable";
import Seperator from "@/components/shared/Seperator";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label"
import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination";
import { SearchHistory } from "@/types";
import { getCookies } from "@/utils/cookie";
import Link from "next/link";

const historyPageSize = 5

const HistoryPage: React.FC<{
    searchParams: { page?: string }
}> = async ({ searchParams }) => {
    const page = parseInt((await searchParams).page ?? '0')
    const queryHistory: SearchHistory[] = (await getCookies()).reverse()
    const displayedQuery: SearchHistory[] = queryHistory.slice(
        historyPageSize * page,
        historyPageSize * (page + 1)
    )
    const maxPage = Math.ceil(queryHistory.length / (0.0 + historyPageSize))

    return (
        <div 
            className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-7 sm:p-17 sm:pr-45 sm:pl-45 font-[family-name:var(--font-geist-sans)]">
            <div className="w-full flex flex-row gap-3">
                <Label className="text-2xl font-bold text-start flex-3">Search History</Label>
                <Button className="flex-1"><Link href='/'>Go to Search</Link></Button>
                <Button className="flex-1" variant={'outline'}>
                    <Link href='/advanced_search_form'>Go to Advanced Search</Link>
                </Button>
            </div>
            <Seperator />
            {
                displayedQuery && displayedQuery.length > 0 ?
                displayedQuery.map(a => <SearchHistoryTable key={a.date} data={a} startPageNumber={historyPageSize * page}/>) :
                <div className="w-full">
                    <Label className="text-center text-gray-500">No Search History. Go to Search Some.</Label>
                </div>
            }
            {
                displayedQuery && displayedQuery.length > 0 && queryHistory.length > historyPageSize &&
                <Pagination>
                    <PaginationContent>
                        {
                            page > 0 &&
                            <PaginationItem>
                                <PaginationPrevious href={`/history?page=${page - 1}`} />
                            </PaginationItem>
                        }
                        {
                            page > 1 &&
                            <PaginationItem>
                                <PaginationLink href='/history'>1</PaginationLink>
                            </PaginationItem>
                        }
                        {
                            page > 2 &&
                            <PaginationItem>
                                <PaginationEllipsis/>
                            </PaginationItem>
                        }
                        {
                            page > 0 &&
                            <PaginationItem>
                                <PaginationLink href={`/history?page=${page - 1}`}>{page}</PaginationLink>
                            </PaginationItem>
                        }
                        {
                            page >= 0 &&
                            <PaginationItem>
                                <PaginationLink href={`/history?page=${page}`} isActive>{page + 1}</PaginationLink>
                            </PaginationItem>
                        }
                        {
                            page < maxPage - 1 &&
                            <PaginationItem>
                                <PaginationLink href={`/history?page=${page + 1}`}>{page + 2}</PaginationLink>
                            </PaginationItem>
                        }
                        {
                            page < maxPage - 3 &&
                            <PaginationItem>
                                <PaginationEllipsis/>
                            </PaginationItem>
                        }
                        {
                            page < maxPage - 2 &&
                            <PaginationItem>
                                <PaginationLink href={`/history?page=${maxPage - 1}`}>{maxPage}</PaginationLink>
                            </PaginationItem>
                        }
                        {
                            page < maxPage - 1 &&
                            <PaginationItem>
                                <PaginationNext href={`/history?page=${page + 1}`} />
                            </PaginationItem>
                        }
                    </PaginationContent>
                </Pagination>
            }
        </div>
    )
}

export default HistoryPage