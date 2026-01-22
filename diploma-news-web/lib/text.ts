export function stripHtml(input: string): string {
  if (!input) return "";

  // 1) прибрати скрипти/стилі
  let s = input
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, "");

  // 2) замінити <br>, <p> на перенос рядка
  s = s.replace(/<\s*br\s*\/?\s*>/gi, "\n");
  s = s.replace(/<\/p\s*>/gi, "\n");

  // 3) прибрати всі теги
  s = s.replace(/<[^>]+>/g, "");

  // 4) декодувати basic HTML entities
  s = decodeHtmlEntities(s);

  // 5) нормалізувати пробіли/переноси
  s = s.replace(/\u00A0/g, " "); // NBSP
  s = s.replace(/[ \t]+\n/g, "\n");
  s = s.replace(/\n{3,}/g, "\n\n");
  s = s.replace(/[ \t]{2,}/g, " ").trim();

  return s;
}

function decodeHtmlEntities(str: string): string {
  // Працює і в браузері, і на сервері без DOMParser
  const map: Record<string, string> = {
    "&nbsp;": " ",
    "&amp;": "&",
    "&quot;": '"',
    "&#39;": "'",
    "&lt;": "<",
    "&gt;": ">",
  };

  return str.replace(/&nbsp;|&amp;|&quot;|&#39;|&lt;|&gt;/g, (m) => map[m] ?? m);
}
