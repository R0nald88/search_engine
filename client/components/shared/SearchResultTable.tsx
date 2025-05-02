'use client'

import { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "../ui/datatable"
import { Label } from "@radix-ui/react-label"
import { WebpageDetail } from "@/types"
import Link from "next/link"
import { Button } from "../ui/button"

export type SearchResultTableData = {
    score: number
    detail: WebpageDetail & {
        likeState: 'liked' | 'none' | 'disliked'
        setLikeState: (likeState: 'liked' | 'none' | 'disliked', detail: WebpageDetail) => void
        getSimilarPage: (detail: WebpageDetail) => void
    }
}

export type SearchResultTableProps = {
    data: SearchResultTableData[]
    isLoading?: boolean
    error?: string | null
}

const columns: ColumnDef<SearchResultTableData>[] = [
    {
        accessorKey: "score",
        header: "Score",
        cell: ({ row }) => 
            <div className="w-full flex">
                <Label className="text-center text-lg font-bold flex-1">
                    {row.getValue("score")}
                </Label>
            </div>
            ,
    },
    {
        accessorKey: "detail",
        header: "Webpage Detail",
        cell: ({ row }) => {
            const detail: WebpageDetail & {
                likeState: 'liked' | 'none' | 'disliked'
                setLikeState: (likeState: 'liked' | 'none' | 'disliked', detail: WebpageDetail) => void
                getSimilarPage: (detail: WebpageDetail) => void
            } = row.getValue("detail")

            return (
                <div className="flex flex-col gap-3">
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
                    <div className="flex flex-row gap-3 pt-3 pb-3">
                        <Button
                            onClick={() => detail.getSimilarPage(detail)}>
                            Get Similar Pages
                        </Button>
                        <Button
                            disabled={detail.likeState == 'liked'}
                            variant={'outline'}
                            onClick={() => detail.setLikeState('liked', detail)}>
                            {detail.likeState == 'liked' ? 'Liked' : 'Like'}
                        </Button>
                        <Button
                            disabled={detail.likeState == 'disliked'}
                            variant={'outline'}
                            onClick={() => detail.setLikeState('disliked', detail)}>
                            {detail.likeState == 'disliked' ? 'Disliked' : 'Dislike'}
                        </Button>
                    </div>
                </div>
            )
        }
    },
]

const SearchResultTable: React.FC<SearchResultTableProps> = ({
    data, isLoading = false, error = null
}) => {
    return (
        <DataTable 
            columns={columns} 
            data={data} 
            emptyStateText={
                isLoading ? 'Loading from Server' :
                error ? error :
                'No Results'
            }
            pageSize={50}
        />
    )
}

export default SearchResultTable