import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

// Role enforcement (ADMIN/GOVERNMENT_ANALYST) happens in the api-gateway.
export async function GET(request: NextRequest) {
  return runBff(() => {
    const authToken = withAuth(request);
    const sp = request.nextUrl.searchParams;
    const params: Record<string, string> = {};
    for (const key of ["model_type", "target_type", "horizon", "active_only"]) {
      const v = sp.get(key);
      if (v) params[key] = v;
    }
    return apiClient.get("/admin/models", params, { authToken });
  });
}

export async function POST(request: NextRequest) {
  return runBff(async () => {
    const authToken = withAuth(request);
    const body = await request.json();
    return apiClient.post("/admin/models", body, { authToken });
  });
}
