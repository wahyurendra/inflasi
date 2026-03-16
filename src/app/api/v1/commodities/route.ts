import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";
import { MVP_COMMODITIES } from "@/lib/constants";

export async function GET() {
  try {
    const result = await apiClient.get("/commodities/");
    return NextResponse.json({ data: result });
  } catch {
    const data = MVP_COMMODITIES.map((c, i) => ({
      id: i + 1,
      namaDisplay: c.display,
      satuan: c.satuan,
      kategori: c.kategori,
    }));
    return NextResponse.json({ data, source: "mock" });
  }
}
