import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  return runBff(() => {
    const authToken = withAuth(request);
    return apiClient.post(`/admin/models/${params.id}/promote`, undefined, { authToken });
  });
}
