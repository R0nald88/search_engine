'use client'

import { SearchHistory, WebpageHistory } from "@/types"
import { ColumnDef } from "@tanstack/react-table"
import { Button } from "../ui/button"
import { Label } from "../ui/label"
import Link from "next/link"
import { Badge } from "../ui/badge"
import { DataTable } from "../ui/datatable"

export type SearchHistoryTableProps = {
    data: SearchHistory
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
                <Label className="text-center text-lg font-bold flex-1">
                    {row.getValue("itemNumber")}
                </Label>
            </div>
    },
    {
        accessorKey: 'webpages',
        header: 'Searched Webpage',
        cell: ({ row }) => {
            const detail: WebpageHistory = row.getValue('webpages')
            return <div className="flex flex-col gap-3">
                <Label className="font-bold text-lg">{detail.title}</Label>
                <Label className="text-gray-500">
                    URL: <Link href={detail.url}>{detail.url}</Link><br/>
                    Size: {detail.size} bytes<br/>
                    Top Term Frequencies: {detail.top_tfs.map(([term, freq]) => `${term} (${freq})`).join(', ')}
                </Label>
                {detail.parents.length > 0 && (
                    <>
                        <Label className="font-bold">Parents:</Label>
                        <Label className="text-gray-500">
                            {detail.parents.map((parent) => (
                                <u>
                                    <Link href={parent} key={parent}>{parent}</Link><br/>
                                </u>
                            ))}
                        </Label>
                    </>
                )}
                {detail.children.length > 0 && (
                    <>
                        <Label className="font-bold">Children:</Label>
                        <Label className="text-gray-500">
                            {detail.children.map((child) => (
                                <u>
                                    <Link href={child} key={child}>{child}</Link><br/>
                                </u>
                            ))}
                        </Label>
                    </>
                )}
                {
                    (detail.clicked || detail.likeState === 'liked') &&
                    <div className="flex flex-row gap-3 pt-3 pb-3">
                        {detail.likeState === 'liked' && <Badge variant={'outline'}>Liked</Badge>}
                        {detail.clicked && <Badge variant={'outline'}>Viewed</Badge>}
                    </div>
                }
            </div>
        }
    }
]

const SearchHistoryTable: React.FC<SearchHistoryTableProps> = ({
    data
}) => {
    return (
        <div className="w-full flex flex-col gap-7">
            <div className="w-full flex flex-row gap-3">
                <div className="w-full flex flex-col flex-6 gap-3">
                    <Label className="w-full text-lg font-bold text-left">
                        Query: {data.query}
                    </Label>
                    <Label className="text-gray-400 w-full text-left">
                        Date: {data.date}
                    </Label>
                </div>

                <Button className="flex-1">Search</Button>
                <Button className="flex-1" variant={'outline'}>Search Within</Button>
                <Button className="flex-1" variant={'outline'}>Merged Search</Button>
            </div>
            
            <DataTable columns={columns} pageSize={5} 
                data={data.webpages.map((w, i) => ({ webpages: w, itemNumber: i }))}
            />

            <hr className='border-gray-300 w-full' />
        </div>
    )
}

export default SearchHistoryTable