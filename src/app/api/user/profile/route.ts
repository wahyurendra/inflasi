import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const opts = { userId: session.user.id, userRole: session.user.role };
    const user = await apiClient.get("/users/" + session.user.id + "/profile", undefined, opts);

    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    return NextResponse.json({ data: user });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { name } = body;

    if (!name || typeof name !== "string" || name.trim().length < 2) {
      return NextResponse.json({ error: "Nama minimal 2 karakter" }, { status: 400 });
    }

    const opts = { userId: session.user.id, userRole: session.user.role };
    const user = await apiClient.patch("/users/" + session.user.id + "/profile", { name: name.trim() }, opts);

    return NextResponse.json({ data: user });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
