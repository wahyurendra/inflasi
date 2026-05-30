import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  return runBff(() => {
    const authToken = withAuth(request);
    const { searchParams } = new URL(request.url);
    const params: Record<string, string> = {
      page: searchParams.get("page") || "1",
      limit: searchParams.get("limit") || "20",
    };
    return apiClient.get("/reports/my", params, { authToken });
  });
}
