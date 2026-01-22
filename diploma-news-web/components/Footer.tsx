export default function Footer() {
  return (
    <footer className="mt-10 border-t border-zinc-200 bg-white">
      <div className="container-page py-6 text-sm text-zinc-600">
        <div className="flex flex-col gap-1">
          <span>© {new Date().getFullYear()} News</span>
          <span className="text-xs text-zinc-500">
          </span>
        </div>
      </div>
    </footer>
  );
}
