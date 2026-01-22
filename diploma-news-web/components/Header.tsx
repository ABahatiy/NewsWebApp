export default function Header() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="container-page flex items-center justify-between py-4">
        <div className="flex flex-col">
          <span className="text-lg font-semibold leading-tight">Diploma News</span>
          <span className="text-sm text-zinc-600">Стрічка новин (Vercel + Next.js)</span>
        </div>

        <div className="text-xs text-zinc-500">
          App Router • Tailwind • API /api/news
        </div>
      </div>
    </header>
  );
}
