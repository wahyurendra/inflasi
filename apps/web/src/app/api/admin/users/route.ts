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
    const searchParams = request.nextUrl.searchParams;
    const params: Record<string, string> = {
      page: searchParams.get("page") || "1",
      limit: searchParams.get("limit") || "20",
    };
    const role = searchParams.get("role");
    if (role) params.role = role;
    return apiClient.get("/users/admin/list", params, { authToken });
  });
}

export async function PATCH(request: NextRequest) {
  return runBff(async () => {
    const authToken = withAuth(request);
    const { userId, role, isActive } = await request.json();
    if (!userId) throw new Error("userId is required (400)");
    const updateData: Record<string, unknown> = {};
    if (role) updateData.role = role;
    if (typeof isActive === "boolean") updateData.isActive = isActive;
    return apiClient.patch(`/users/admin/${userId}`, updateData, { authToken });
  });
}
