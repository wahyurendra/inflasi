import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff, withAuth } from "@/lib/api-auth";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  return runBff(async () => {
    const authToken = withAuth(request);
    return apiClient.get("/gamification/user-badges", undefined, { authToken });
  });
}
