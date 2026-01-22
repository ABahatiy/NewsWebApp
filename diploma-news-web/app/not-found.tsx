export default function NotFound() {
  return (
    <div className="card p-6">
      <h1 className="text-lg font-semibold">Сторінку не знайдено</h1>
      <p className="mt-2 text-sm text-zinc-600">
        Перевір маршрут або наявність файлу <code>app/page.tsx</code>.
      </p>
    </div>
  );
}
