import { NextResponse, type NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { optionalAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

// Special: returns { count: 0 } when unauthenticated so the bell badge stays quiet
// instead of flashing a 401 toast.
export async function GET(request: NextRequest) {
  const authToken = optionalAuth(request);
  if (!authToken) return NextResponse.json({ count: 0 });
  try {
    const data = await apiClient.get<{ count: number }>(
      "/notifications/count",
      undefined,
      { authToken },
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Upstream error";
    return NextResponse.json({ detail: message, count: 0 }, { status: 502 });
  }
}
