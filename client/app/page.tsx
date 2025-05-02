import SearchBox from "@/components/shared/SearchBox"

export default function Home() {
    return (
        <div 
            className="flex flex-col items-center justify-items-center min-h-screen p-8 pb-20 gap-7 sm:p-17 sm:pr-45 sm:pl-45 font-[family-name:var(--font-geist-sans)]">
            <SearchBox alignment="vertical" needSearchBtn needHistoryBtn={false}/>
        </div>
    );
}
