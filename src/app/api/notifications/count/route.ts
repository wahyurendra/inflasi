import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ count: 0 });
  }

  try {
    const opts = { userId: session.user.id, userRole: session.user.role };
    const data = await apiClient.get<{ count: number }>("/notifications/count", undefined, opts);
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ count: 0 });
  }
}
