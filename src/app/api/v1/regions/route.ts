import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";
import { REGIONS } from "@/lib/constants";

export async function GET() {
  try {
    const result = await apiClient.get("/regions/");
    return NextResponse.json({ data: result });
  } catch {
    const data = REGIONS.map((r, i) => ({
      id: i + 1,
      namaProvinsi: r.provinsi,
      kodeProvinsi: r.kode,
      pulau: "Indonesia",
    }));
    return NextResponse.json({ data, source: "mock" });
  }
}
