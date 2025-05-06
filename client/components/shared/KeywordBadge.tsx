'use client'

import { Badge } from "../ui/badge"
import { Label } from "../ui/label"
import { X } from 'lucide-react'

const KeywordBadge: React.FC<{
    keyword: string
    onDelete: () => void
}> = ({ keyword, onDelete }) => (
    <Badge variant={'outline'} className="py-2 px-3">
        <div className="gap-2 flex flex-row items-center justify-center">
            <Label>{keyword}</Label>
            <X size={16} onClick={onDelete} className="cursor-pointer"/>
        </div>
    </Badge>
)

export default KeywordBadge