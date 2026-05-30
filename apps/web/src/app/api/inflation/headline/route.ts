import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// Live analytics — no static optimisation, no route-handler cache.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  return runBff(() => apiClient.get("/inflation/headline"));
}
