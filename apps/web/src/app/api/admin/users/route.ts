import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  try {
    const authToken = request.headers.get("authorization") ?? undefined;
    if (!authToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    // ADMIN role is enforced by the api-gateway.

    const searchParams = request.nextUrl.searchParams;
    const params: Record<string, string> = {};
    const page = searchParams.get("page") || "1";
    const limit = searchParams.get("limit") || "20";
    const role = searchParams.get("role");

    params.page = page;
    params.limit = limit;
    if (role) params.role = role;

    const opts = { authToken };
    const data = await apiClient.get("/users/admin/list", params, opts);

    return NextResponse.json(data);
  } catch (error) {
    console.error("Admin users error:", error);
    return NextResponse.json({ data: [], total: 0, page: 1, limit: 20, error: "Database error" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const authToken = request.headers.get("authorization") ?? undefined;
    if (!authToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    // ADMIN role is enforced by the api-gateway.

    const body = await request.json();
    const { userId, role, isActive } = body;

    if (!userId) {
      return NextResponse.json({ error: "userId is required" }, { status: 400 });
    }

    const updateData: Record<string, unknown> = {};
    if (role) updateData.role = role;
    if (typeof isActive === "boolean") updateData.isActive = isActive;

    const opts = { authToken };
    const data = await apiClient.patch("/users/admin/" + userId, updateData, opts);

    return NextResponse.json({ data });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
