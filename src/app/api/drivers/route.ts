import { NextRequest, NextResponse } from "next/server";

const MOCK_DRIVERS = {
  commodity: "Cabai Rawit",
  tanggal: "2026-03-10",
  drivers: [
    { name: "cuaca", contribution_pct: 35.2, magnitude: 70, direction: "naik", detail: "Curah hujan 85mm, level waspada" },
    { name: "musiman", contribution_pct: 25.0, magnitude: 60, direction: "naik", detail: "Musim: mendekati Ramadan" },
    { name: "stok", contribution_pct: 18.5, magnitude: 50, direction: "naik", detail: "Status stok: waspada" },
    { name: "global", contribution_pct: 10.3, magnitude: 25, direction: "naik", detail: "palm_oil: $850 (+3.2%)" },
    { name: "kurs", contribution_pct: 6.5, magnitude: 15, direction: "neutral", detail: "USD/IDR Rp 16,250 (+0.3%)" },
    { name: "logistik", contribution_pct: 4.5, magnitude: 10, direction: "neutral", detail: "GSCPI: 0.35 std dev" },
  ],
};

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";

  try {
    // Try calling Python analytics API
    const analyticsUrl = process.env.ANALYTICS_API_URL || "http://localhost:8000";
    const resp = await fetch(
      `${analyticsUrl}/api/drivers/analysis?commodity=${commodity}&region=${region}`,
      { next: { revalidate: 300 } }
    );

    if (resp.ok) {
      const data = await resp.json();
      return NextResponse.json(data);
    }
  } catch {
    // Fall through to mock
  }

  return NextResponse.json({
    ...MOCK_DRIVERS,
    commodity_code: commodity,
    region_code: region,
  });
}
