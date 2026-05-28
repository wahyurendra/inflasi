import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: Request) {
  try {
    const authToken = request.headers.get("authorization") ?? undefined;
    if (!authToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // ADMIN role is enforced by the api-gateway.
    const opts = { authToken };
    const data = await apiClient.get("/users/admin/stats", undefined, opts);

    return NextResponse.json(data);
  } catch (error) {
    console.error("Admin stats error:", error);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
