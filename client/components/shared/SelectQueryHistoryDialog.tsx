'use client'

import { SearchHistory, SearchQuery } from '@/types'
import React, { useEffect, useMemo, useState } from 'react'
import { DialogTrigger, Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog'
import { ColumnDef } from '@tanstack/react-table'
import { Button } from '../ui/button'
import QueryLabel from './QueryLabel'
import { Checkbox } from '../ui/checkbox'
import { getCookies } from '@/utils/cookie'
import { DataTable } from '../ui/datatable'
import { castHistoryToQuery } from '@/utils'

const columns = (
    isMultiple: boolean,
    onSelected: (queries: SearchQuery[]) => void
): ColumnDef<{
    query: SearchHistory
    str: string
}>[] => {
    return [
        {
            id: 'select',
            header: isMultiple ? 
                ({ table }) => (
                    <Checkbox 
                        checked={
                            table.getIsAllPageRowsSelected() ||
                            (table.getIsSomePageRowsSelected() && "indeterminate")
                        }
                        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                        aria-label="Select all"
                        className='items-center'
                    />
                ) : 'Selection',
            cell: ({ row }) => 
                isMultiple ? 
                <Checkbox 
                    checked={row.getIsSelected()} 
                    onCheckedChange={(value) => row.toggleSelected(!!value)}
                    aria-label="Select row"
                    className='items-center'
                />
                :
                <Button 
                    className='w-full' 
                    onClick={() => onSelected(
                        [castHistoryToQuery(row.getValue('query'))]
                    )}>Select</Button>
        }, {
            accessorKey: 'query',
            header: 'Query History',
            cell: ({ row }) => (
                <div className='w-full min-w-100'>
                    <QueryLabel 
                        biggerTitle={false} 
                        searchQuery={row.getValue('query')} 
                        time={(row.getValue('query') as SearchHistory).date} />
                </div>
            )
        }, {
            accessorKey: 'str',
            header: 'String',
            cell: ({row}) => row.getValue('str') as string
        }
    ]
}

const includesSearchHistory = (target: SearchHistory, source: SearchQuery[]): boolean => {
    const t = JSON.stringify(target)
    let s = source.filter(v => v.type === target.type).filter(v => t.includes(JSON.stringify(v)))
    return s.length > 0
}

const getIndexSearchHistory = (target: SearchHistory, source: SearchQuery[]): number => {
    const t = JSON.stringify(target)
    let i = 0
    for (let a of source) {
        if (t.includes(JSON.stringify(a))) {
            return i
        }
        i += 1
    }
    return -1
}

const SelectQueryHistoryDialog: React.FC<{
    eliminateQuery?: SearchQuery[]
    selectedQuery?: SearchQuery[]
    includeJoinedQuery?: boolean
    isMultiple?: boolean
    onSelected: (queries: SearchQuery[], setOpen: (o: boolean) => void) => void
} & React.PropsWithChildren> = ({
    onSelected,
    isMultiple = false,
    eliminateQuery = [],
    selectedQuery = [],
    includeJoinedQuery = true,
    children
}) => {
    const [open, setOpen] = useState(false)
    const [history, setHistory] = useState<SearchHistory[] | undefined>(undefined)
    useEffect(() => {
        getCookies().then(v => {
            setHistory(v.filter(a => (includeJoinedQuery || a.type === 'simple' || a.type === 'single') && !includesSearchHistory(a, eliminateQuery)))
        })
    }, [])
    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>{children}</DialogTrigger>
            <DialogContent className='w-full p-10 min-w-[70%]'>
                <DialogHeader>
                    <DialogTitle>Query History Selection</DialogTitle>
                    <DialogDescription>Select the query for searching.</DialogDescription>
                </DialogHeader>
                
                <DataTable 
                    columns={columns(isMultiple, (v) => onSelected(v, setOpen))} 
                    data={history === undefined ? [] : history.map(v => ({
                        query: v,
                        str: JSON.stringify(v).toLowerCase()
                    }))}
                    emptyStateText={history === undefined ? 'Loading...' : 'No Result.'}
                    pageSize={5}
                    searchable
                    invisibleCol={['str']}
                    searchCol='str'
                    selectable={isMultiple}
                    onSelect={v => onSelected(v.map(a => castHistoryToQuery(a.query)), setOpen)}
                    selectedCol={history === undefined || selectedQuery.length <= 0 ? [] : history.map(v => getIndexSearchHistory(v, selectedQuery)).filter(v => v != -1)}
                />
            </DialogContent>
        </Dialog>
    )
}

export default SelectQueryHistoryDialog