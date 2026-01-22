import { NextResponse } from "next/server";
import type { NewsApiResponse } from "@/lib/types";

export const runtime = "nodejs";
export const revalidate = 0;

function getBaseUrl() {
  return process.env.PY_API_BASE_URL || "http://127.0.0.1:8000";
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);

  const q = searchParams.get("q") ?? "";
  const topic = searchParams.get("topic") ?? "all";
  const limit = searchParams.get("limit") ?? "30";

  const base = getBaseUrl();

  const newsUrl = new URL("/news", base);
  newsUrl.searchParams.set("q", q);
  newsUrl.searchParams.set("topic", topic);
  newsUrl.searchParams.set("limit", limit);

  const pyNewsRes = await fetch(newsUrl.toString(), { cache: "no-store" });
  const pyNews = await pyNewsRes.json();

  const topicsUrl = new URL("/topics", base);
  const pyTopicsRes = await fetch(topicsUrl.toString(), { cache: "no-store" });
  const pyTopics = await pyTopicsRes.json();

  const payload: NewsApiResponse = {
    items: (pyNews.items ?? []).map((it: any) => ({
      id: String(it.id ?? ""),
      title: String(it.title ?? ""),
      link: String(it.link ?? ""),
      source: String(it.source ?? ""),
      summary: String(it.summary ?? ""),
      publishedAt: String(it.publishedAt ?? ""),
      topic: String(it.topic ?? ""),
    })),
    topics: (pyTopics.topics ?? []).map((t: any) => ({
      id: String(t.key ?? "all"),
      title: String(t.label ?? "Усі"),
      keywords: [],
    })),
    meta: {
      fetchedAt: new Date().toISOString(),
      total: Number(pyNews.meta?.total ?? 0),
      query: q || undefined,
      topic: topic || "all",
    },
  };

  if (pyNews?.meta?.error) {
    return NextResponse.json(
      {
        ...payload,
        meta: {
          ...payload.meta,
          total: 0,
        },
      },
      { status: 500 }
    );
  }

  return NextResponse.json(payload);
}
