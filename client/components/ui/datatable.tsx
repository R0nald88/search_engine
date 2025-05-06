'use client'

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

import { ColumnDef, ColumnFiltersState, flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, RowSelectionState, useReactTable, VisibilityState } from "@tanstack/react-table"
import { Button } from "./button"
import { useEffect } from "react"
import React from "react"
import { Input } from "./input"

export type DataTableProps<TData, TValue> = {
    columns: ColumnDef<TData, TValue>[]
    data: TData[]
    emptyStateText?: string
    invisibleCol?: string[]
    pageSize?: number
    selectable?: boolean
    searchable?: boolean
    searchCol?: string
    selectedCol?: number[]
    onSelect?: (data: TData[]) => void
}

const toDict = (invisibleCol: string[]) => {
    let result: { [id: string]: boolean } = {}
    for (let a of invisibleCol) result[a] = false
    return result
}

export function DataTable<TData, TValue>({
    columns,
    data,
    emptyStateText = 'No results.',
    pageSize = 10,
    selectable = false,
    searchable = false,
    searchCol = '',
    selectedCol = [],
    invisibleCol = [],
    onSelect = () => {}
}: DataTableProps<TData, TValue>) {
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
    const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>(toDict(invisibleCol))
    const [rowSelection, setRowSelection] = React.useState<RowSelectionState>({})

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        onColumnFiltersChange: setColumnFilters,
        onColumnVisibilityChange: setColumnVisibility,
        onRowSelectionChange: setRowSelection,
        state: {
            columnFilters,
            columnVisibility,
            rowSelection,
        }
    })

    useEffect(() => { 
        table.setPageSize(pageSize)
        setRowSelection(() => {
            let a: RowSelectionState = {}
            for (let v of selectedCol) {
                a[v + ''] = true
            }
            return a
        })
    }, [])

    return (
        <div className="w-full gap-4">
            {
                searchable && 
                <Input
                    placeholder="Input to search query history..."
                    value={(table.getColumn(searchCol)?.getFilterValue() as string) ?? ""}
                    onChange={(event) =>
                        table.getColumn(searchCol)?.setFilterValue(event.target.value.toLowerCase())
                    }
                    className="w-full mb-5"
                />
            }
            <div className="rounded-md border w-full">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => {
                                    return (
                                        <TableHead key={header.id}>
                                            {header.isPlaceholder
                                                ? null
                                                : flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )}
                                        </TableHead>
                                    )
                                })}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow
                                    key={row.id}
                                    data-state={row.getIsSelected() && "selected"}
                                >
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(
                                                cell.column.columnDef.cell,
                                                cell.getContext()
                                            )}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell
                                    colSpan={columns.length}
                                    className="h-24 text-center"
                                >
                                    {emptyStateText}
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
            <div className="flex items-center justify-end space-x-2 py-4">
                {
                    selectable ?
                    <div className="flex-1 text-sm text-muted-foreground">
                        {table.getFilteredSelectedRowModel().rows.length} of{" "}
                        {table.getFilteredRowModel().rows.length} row(s) selected.
                    </div> :
                    <div className="flex-1 text-sm text-muted-foreground">
                        Total {table.getPageCount()} page(s)
                    </div>
                }
                <div className="space-x-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                    >
                        Previous
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                    >
                        Next
                    </Button>
                    {
                        selectable &&
                        <Button
                            size="sm"
                            onClick={() => onSelect(
                                table.getFilteredSelectedRowModel().rows.map(v => v.original)
                            )}
                            disabled={table.getFilteredSelectedRowModel().rows.length <= 0}
                        >
                            Select
                        </Button>
                    }
                </div>
            </div>
        </div>
    )
}