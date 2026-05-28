import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

// Returns the current user's app profile (role/region) from the api-gateway,
// which derives identity from the forwarded Firebase ID token. Called by the
// AuthProvider right after sign-in.
export async function GET(request: NextRequest) {
  const authToken = request.headers.get("authorization") ?? undefined;
  if (!authToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const me = await apiClient.get("/auth/me", undefined, { authToken });
    return NextResponse.json(me);
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}
