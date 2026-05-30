import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "";
  const params: Record<string, string> = {};
  if (commodity) params.commodity = commodity;
  return runBff(() => apiClient.get("/intelligence/comparison", params));
}
