import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const baseUrl =
    process.env.PY_API_BASE_URL ||
    process.env.NEXT_PUBLIC_PY_API_BASE_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL;

  if (!baseUrl) {
    return NextResponse.json(
      { error: "Missing PY_API_BASE_URL env var" },
      { status: 500 }
    );
  }

  const body = await req.json().catch(() => ({}));

  const r = await fetch(`${baseUrl.replace(/\/$/, "")}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const text = await r.text();
  try {
    const data = JSON.parse(text);
    return NextResponse.json(data, { status: r.status });
  } catch {
    return new NextResponse(text, { status: r.status });
  }
}
