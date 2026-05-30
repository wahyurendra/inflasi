import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";
import { toBpsCode } from "@/lib/region-mapping";

// BFF is a thin proxy over live analytics — disable Next.js route-handler
// caching so backend/data fixes propagate without dev restarts.
export const dynamic = "force-dynamic";
export const revalidate = 0;

interface BackendRegion {
  kodeWilayah: string;
  namaProvinsi: string;
  avgPriceChange: number;
  alertCount: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
}

export async function GET() {
  return runBff(async () => {
    const result = await apiClient.get<{ data: BackendRegion[] }>(
      "/regions/heatmap",
    );
    return {
      data: (result.data ?? []).map((r) => ({
        ...r,
        kodeWilayah: toBpsCode(r.kodeWilayah, r.namaProvinsi),
      })),
    };
  });
}
