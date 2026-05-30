import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

// Lightweight RAG search endpoint. Delegates to FastAPI /ai/context/search.
export async function POST(request: NextRequest) {
  const { query } = await request.json();
  if (!query) {
    return NextResponse.json({ detail: "query is required" }, { status: 400 });
  }
  return runBff(() =>
    apiClient.post<{ context: Record<string, unknown>; query: string }>(
      "/ai/context/search",
      { query },
    ),
  );
}
