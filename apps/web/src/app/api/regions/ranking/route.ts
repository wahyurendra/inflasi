import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";
import { toBpsCode } from "@/lib/region-mapping";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

interface BackendRow {
  kodeWilayah?: string;
  namaProvinsi?: string;
  [key: string]: unknown;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sort = searchParams.get("sort") || "pressure";
  const limit = searchParams.get("limit") || "10";
  return runBff(async () => {
    const result = await apiClient.get<{ data: BackendRow[] } | BackendRow[]>(
      "/analytics/regions/ranking",
      { sort, limit },
    );
    const raw = Array.isArray(result) ? result : (result.data ?? []);
    const normalised = raw.map((r) => ({
      ...r,
      kodeWilayah: r.kodeWilayah
        ? toBpsCode(r.kodeWilayah, r.namaProvinsi)
        : r.kodeWilayah,
    }));
    return Array.isArray(result)
      ? normalised
      : { ...result, data: normalised };
  });
}
