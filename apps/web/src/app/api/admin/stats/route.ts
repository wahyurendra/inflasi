import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ADMIN role enforced server-side by the api-gateway.
export async function GET(request: NextRequest) {
  return runBff(() => {
    const authToken = withAuth(request);
    return apiClient.get("/users/admin/stats", undefined, { authToken });
  });
}
