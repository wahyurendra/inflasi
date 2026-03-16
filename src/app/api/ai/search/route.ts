import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

/**
 * Lightweight RAG search endpoint.
 * Delegates keyword extraction and data retrieval to the FastAPI backend.
 */

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json();
    if (!query) {
      return NextResponse.json({ error: "query is required" }, { status: 400 });
    }

    const data = await apiClient.post<{ context: Record<string, unknown>; query: string }>(
      "/ai/context/search",
      { query }
    );

    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ context: {}, query: "" });
  }
}
