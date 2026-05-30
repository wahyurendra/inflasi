import { type NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { optionalAuth, runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  const authToken = optionalAuth(request);
  return runBff(() => apiClient.get(`/reports/${params.id}`, undefined, { authToken }));
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  return runBff(async () => {
    const authToken = withAuth(request);
    const body = await request.json();
    const { status, rejectionNote } = body;
    if (!["APPROVED", "REJECTED", "FLAGGED", "PENDING"].includes(status)) {
      throw new Error("Status tidak valid (400)");
    }
    return apiClient.patch(`/reports/${params.id}`, { status, rejectionNote }, { authToken });
  });
}
