import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const session = await auth();
    if (!session?.user || session.user.role !== "ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const opts = { userId: session.user.id, userRole: session.user.role };
    const data = await apiClient.get("/users/admin/stats", undefined, opts);

    return NextResponse.json(data);
  } catch (error) {
    console.error("Admin stats error:", error);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
