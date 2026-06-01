import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { optionalAuth, runBff, withAuth } from "@/lib/api-auth";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const params: Record<string, string> = {
    page: searchParams.get("page") || "1",
    limit: searchParams.get("limit") || "20",
  };
  const status = searchParams.get("status");
  const commodityId = searchParams.get("commodityId");
  const regionId = searchParams.get("regionId");
  if (status) params.status = status;
  if (commodityId) params.commodityId = commodityId;
  if (regionId) params.regionId = regionId;

  const authToken = optionalAuth(request);
  return runBff(() => apiClient.get("/reports/", params, { authToken }));
}

export async function POST(request: NextRequest) {
  return runBff(async () => {
    const authToken = withAuth(request);
    const body = await request.json();
    const { commodityKode, regionKode, harga, satuan, namaPasar, tanggal } = body;
    if (!commodityKode || !regionKode || !harga || !satuan || !namaPasar || !tanggal) {
      throw new Error("Data tidak lengkap (400)");
    }
    return apiClient.post("/reports/", body, { authToken });
  });
}
