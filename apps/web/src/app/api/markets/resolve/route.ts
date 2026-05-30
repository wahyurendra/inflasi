import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const regionId = searchParams.get("region_id");
  const namaPasar = searchParams.get("nama_pasar");
  if (!regionId || !namaPasar) {
    return NextResponse.json(
      { detail: "region_id and nama_pasar required" },
      { status: 400 },
    );
  }
  return runBff(() =>
    apiClient.get("/markets/resolve", { region_id: regionId, nama_pasar: namaPasar }),
  );
}
