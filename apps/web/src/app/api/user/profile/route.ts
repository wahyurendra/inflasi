import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: Request) {
  try {
    const authToken = request.headers.get("authorization") ?? undefined;
    if (!authToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const opts = { authToken };
    const user = await apiClient.get("/users/me/profile", undefined, opts);

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
    const authToken = request.headers.get("authorization") ?? undefined;
    if (!authToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { name } = body;

    if (!name || typeof name !== "string" || name.trim().length < 2) {
      return NextResponse.json({ error: "Nama minimal 2 karakter" }, { status: 400 });
    }

    const opts = { authToken };
    const user = await apiClient.patch("/users/me/profile", { name: name.trim() }, opts);

    return NextResponse.json({ data: user });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
