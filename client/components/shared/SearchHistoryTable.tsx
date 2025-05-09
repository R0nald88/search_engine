'use client'

import { JoinedSearchQuery, SearchHistory, SearchQuery, SimpleSearchHistory, SimpleSearchQuery, SingleSearchQuery, WebpageHistory } from "@/types"
import { ColumnDef } from "@tanstack/react-table"
import { Button } from "../ui/button"
import { Label } from "../ui/label"
import Link from "next/link"
import { Badge } from "../ui/badge"
import { DataTable } from "../ui/datatable"
import Seperator from "./Seperator"
import QueryLabel from "./QueryLabel"
import { castHistoryToQuery, objToUrl } from "@/utils"

export type SearchHistoryTableProps = {
    data: SearchHistory
    startPageNumber: number
}

export type SearchHistoryData = {
    itemNumber: number
    webpages: WebpageHistory
}

const columns: ColumnDef<SearchHistoryData>[] = [
    {
        accessorKey: "itemNumber",
        header: "Item Number",
        cell: ({ row }) => 
            <div className="w-full flex">
                <Label key={row.id} className="text-center text-2xl font-bold flex-1 items-center justify-center">
                    {row.getValue("itemNumber")}
                </Label>
            </div>
    },
    {
        accessorKey: 'webpages',
        header: 'Searched Webpage',
        cell: ({ row }) => {
            const detail: WebpageHistory = row.getValue('webpages')
            const similarPageQuery: SingleSearchQuery = {
                type: 'single',
                page_any: detail.top_tfs.map(v => [v[0], v[1]])
            }
            return (
                <div className="flex flex-col gap-3" key={row.id}>
                    <Label className="font-bold text-lg">
                        <Link 
                            href={detail.url}
                            target="_blank"
                            rel="noreferrer noopener"
                        ><u>{detail.title}</u></Link>
                    </Label>
                    <Label className="text-gray-500">
                        <p>
                            URL: <u><Link 
                                href={detail.url}
                                target="_blank"
                                rel="noreferrer noopener"
                            >{detail.url}</Link></u>
                            <br/>
                            Size: {detail.size} bytes
                            <br/>
                            Top Term Frequencies: {detail.top_tfs.map(([term, _, freq]) => `${term} (${freq.toPrecision(4)})`).join(', ')}
                        </p>
                    </Label>
                    {detail.parents.length > 0 && (
                        <>
                            <Label className="font-bold">Parents:</Label>
                            <Label className="text-gray-500">
                                <p>
                                    {detail.parents.map((parent) => (
                                        <u key={parent}>
                                            <Link 
                                                href={parent} key={parent}
                                                target="_blank"
                                                rel="noreferrer noopener"
                                            >{parent}</Link><br/>
                                        </u>
                                    ))}
                                </p>
                            </Label>
                        </>
                    )}
                    {detail.children.length > 0 && (
                        <>
                            <Label className="font-bold">Children:</Label>
                            <Label className="text-gray-500">
                                <p>
                                    {detail.children.map((child) => (
                                        <u key={child}>
                                            <Link href={child} key={child}
                                                target="_blank"
                                                rel="noreferrer noopener"
                                            >{child}</Link><br/>
                                        </u>
                                    ))}
                                </p>
                            </Label>
                        </>
                    )}
                    {
                        (detail.clicked || detail.likeState === 'liked') &&
                        <div className="flex flex-row gap-3 pt-3">
                            {detail.likeState === 'liked' && <Badge variant={'outline'}>Liked</Badge>}
                            {detail.clicked && <Badge variant={'outline'}>Viewed</Badge>}
                        </div>
                    }
                    <Button className="mb-3 w-[25%]">
                        <Link
                            href={'/search?query=' + objToUrl(similarPageQuery)}
                            target="_blank"
                            rel="noreferrer noopener"
                        >
                            Get Similar Page
                        </Link>
                    </Button>
                </div>
            )
        }
    }
]

const SearchHistoryTable: React.FC<SearchHistoryTableProps> = ({
    data, startPageNumber
}) => {
    return (
        <div className="w-full flex flex-col gap-6">
            <div className="w-full flex flex-row gap-3">
                <div className="w-full flex-6">
                    <QueryLabel searchQuery={data} time={data.date}/>
                </div>

                <Button className="flex-1">
                    <Link href={'/search?query=' + objToUrl(castHistoryToQuery(data))}>Search</Link>
                </Button>
                <Button className="flex-1" variant={'outline'}><Link
                    href={'/advanced_search_form?query=' + objToUrl(castHistoryToQuery(data))}
                >Advanced Search</Link></Button>
                
            </div>
            
            <DataTable columns={columns} pageSize={3} 
                data={data.webpages.map((w, i) => ({ webpages: w, itemNumber: i + 1 + startPageNumber }))}
            />

            <Seperator />
        </div>
    )
}

export default SearchHistoryTable