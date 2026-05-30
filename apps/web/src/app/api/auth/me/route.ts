import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

// Returns the current user's app profile (role/region) from the api-gateway,
// which derives identity from the forwarded Firebase ID token.
export async function GET(request: NextRequest) {
  return runBff(() => {
    const authToken = withAuth(request);
    return apiClient.get("/auth/me", undefined, { authToken });
  });
}
