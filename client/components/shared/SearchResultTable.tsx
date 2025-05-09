'use client'

import { ColumnDef } from "@tanstack/react-table"
import { DataTable } from "../ui/datatable"
import { Label } from "@radix-ui/react-label"
import { WebpageDetail } from "@/types"
import Link from "next/link"
import { Button } from "../ui/button"

export type SearchResultTableData = {
    score: number
    original_score: number
    detail: WebpageDetail & {
        clicked: boolean
        setClicked: (click: boolean, detail: WebpageDetail) => void
        likeState: 'liked' | 'none' | 'disliked'
        setLikeState: (likeState: 'liked' | 'none' | 'disliked', detail: WebpageDetail) => void
        getSimilarPage: (detail: WebpageDetail) => void
        similarPageLink: string
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
        header: "Modified Score",
        cell: ({ row }) => 
            <div className="w-full flex">
                <Label className="text-center text-2xl font-bold flex-1">
                    {(parseFloat(row.getValue("score")) * 100).toPrecision(4)}
                </Label>
            </div>
            ,
    },
    {
        accessorKey: "original_score",
        header: "Original Score",
        cell: ({ row }) => 
            <div className="w-full flex">
                <Label className="text-center text-2xl font-bold flex-1">
                    {(parseFloat(row.getValue("original_score")) * 100).toPrecision(4)}
                </Label>
            </div>
            ,
    },
    {
        accessorKey: "detail",
        header: "Webpage Detail",
        cell: ({ row }) => {
            const detail: WebpageDetail & {
                clicked: boolean
                setClicked: (click: boolean, detail: WebpageDetail) => void
                likeState: 'liked' | 'none' | 'disliked'
                setLikeState: (likeState: 'liked' | 'none' | 'disliked', detail: WebpageDetail) => void
                getSimilarPage: (detail: WebpageDetail) => void
                similarPageLink: string
            } = row.getValue("detail")

            return (
                <div className="flex flex-col gap-3">
                    <Label className="font-bold text-lg">
                        <Link 
                            href={detail.url} 
                            target="_blank"
                            rel="noreferrer noopener"
                            onClick={() => detail.setClicked(true, detail)}>
                            <u>{detail.title}</u>
                        </Link>
                    </Label>
                    <Label className="text-gray-500">
                        <p>
                            URL: <Link 
                                href={detail.url} 
                                rel="noreferrer noopener"
                                onClick={() => detail.setClicked(true, detail)} 
                                target="_blank"><u>{detail.url}</u></Link><br/>
                            Size: {detail.size} bytes<br/>
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
                                                href={parent} 
                                                target="_blank"
                                                rel="noreferrer noopener"
                                                key={parent}
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
                                            <Link 
                                                href={child} 
                                                key={child}
                                                target="_blank"
                                                rel="noreferrer noopener"
                                            >{child}</Link><br/>
                                        </u>
                                    ))}
                                </p>
                            </Label>
                        </>
                    )}
                    <div className="flex flex-row gap-3 pt-3 pb-3">
                        <Button
                            onClick={() => detail.getSimilarPage(detail)}>
                            <Link
                                href={detail.similarPageLink}
                                target="_blank"
                                rel="noreferrer noopener"
                            >
                                Get Similar Pages
                            </Link>
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