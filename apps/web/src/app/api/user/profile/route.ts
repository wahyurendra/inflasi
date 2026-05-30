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
    return apiClient.get("/users/me/profile", undefined, { authToken });
  });
}

export async function PATCH(request: NextRequest) {
  return runBff(async () => {
    const authToken = withAuth(request);
    const { name } = await request.json();
    if (!name || typeof name !== "string" || name.trim().length < 2) {
      throw new Error("Nama minimal 2 karakter (400)");
    }
    return apiClient.patch("/users/me/profile", { name: name.trim() }, { authToken });
  });
}
