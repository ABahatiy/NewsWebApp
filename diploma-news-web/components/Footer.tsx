export default function Footer() {
  return (
    <footer className="mt-10 border-t border-zinc-200 bg-white">
      <div className="container-page py-6 text-sm text-zinc-600">
        <div className="flex flex-col gap-1">
          <span>© {new Date().getFullYear()} Diploma News</span>
          <span className="text-xs text-zinc-500">
            Демо-каркас. Далі підключимо теми/збереження/агента та ваші джерела з проєкту.
          </span>
        </div>
      </div>
    </footer>
  );
}
