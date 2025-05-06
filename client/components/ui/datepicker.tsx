"use client"

import * as React from "react"
import { addDays, format } from "date-fns"
import { CalendarIcon } from "lucide-react"
import { DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { SingleSearchQuery } from "@/types"

const toDateString = (date?: Date | undefined) => {
    if (date == undefined) return undefined
    return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
}

const toDateRange = (searchQuery: SingleSearchQuery): DateRange | undefined => {
    return searchQuery.from_date && searchQuery.to_date ?
    {
        from: searchQuery.from_date ? new Date(searchQuery.from_date) : undefined,
        to: searchQuery.to_date ? new Date(searchQuery.to_date) : undefined
    }: undefined
} 

export function DatePicker({
    className, dateString, setDateString
}: React.HTMLAttributes<HTMLDivElement> & {
    dateString?: SingleSearchQuery,
    setDateString?: React.Dispatch<React.SetStateAction<SingleSearchQuery>>
}) {
    const [date, setDate] = React.useState<DateRange | undefined>(dateString ? toDateRange(dateString) : undefined)

    React.useEffect(() => {
        console.log(toDateString(date?.from), toDateString(date?.to))
        setDateString?.((prev) => ({
            ...prev,
            from_date: toDateString(date?.from),
            to_date: toDateString(date?.to)
        }))
    }, [date])
    return (
        <div className={cn("grid gap-2", className)}>
            <Popover>
                <PopoverTrigger asChild>
                    <Button
                        id="date"
                        variant={"outline"}
                        className={cn(
                            "w-[300px] justify-start text-left font-normal",
                            !date && "text-muted-foreground"
                        )}
                    >
                        <CalendarIcon />
                        {date?.from ? (
                            date.to ? (
                                <>
                                    {format(date.from, "LLL dd, y")} -{" "}
                                    {format(date.to, "LLL dd, y")}
                                </>
                            ) : (
                                format(date.from, "LLL dd, y")
                            )
                        ) : (
                            <span>Pick a date</span>
                        )}
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                        initialFocus
                        mode="range"
                        defaultMonth={date?.from}
                        selected={date}
                        onSelect={setDate}
                        numberOfMonths={2}
                    />
                </PopoverContent>
            </Popover>
        </div>
    )
}
