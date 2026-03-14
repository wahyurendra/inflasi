import { NextResponse } from "next/server";

const MOCK_RECOMMENDATIONS = [
  {
    commodity: "Cabai Rawit",
    from_region: "Garut",
    from_kode: "32",
    from_harga: 72000,
    to_region: "Jakarta",
    to_kode: "31",
    to_harga: 95000,
    price_gap: 23000,
    distance_km: 280,
    estimated_tonnage: 20,
    urgency: "tinggi",
  },
  {
    commodity: "Bawang Merah",
    from_region: "Brebes",
    from_kode: "33",
    from_harga: 35000,
    to_region: "Papua",
    to_kode: "91",
    to_harga: 58000,
    price_gap: 23000,
    distance_km: 3200,
    estimated_tonnage: 15,
    urgency: "tinggi",
  },
  {
    commodity: "Beras",
    from_region: "Jawa Timur",
    from_kode: "35",
    from_harga: 13500,
    to_region: "Maluku",
    to_kode: "81",
    to_harga: 18500,
    price_gap: 5000,
    distance_km: 2100,
    estimated_tonnage: 50,
    urgency: "sedang",
  },
  {
    commodity: "Telur Ayam",
    from_region: "Jawa Barat",
    from_kode: "32",
    from_harga: 26000,
    to_region: "NTT",
    to_kode: "53",
    to_harga: 34000,
    price_gap: 8000,
    distance_km: 1800,
    estimated_tonnage: 10,
    urgency: "sedang",
  },
];

export async function GET() {
  try {
    const analyticsUrl = process.env.ANALYTICS_API_URL || "http://localhost:8000";
    const resp = await fetch(`${analyticsUrl}/api/recommendations`, {
      next: { revalidate: 600 },
    });

    if (resp.ok) {
      const data = await resp.json();
      return NextResponse.json({ recommendations: data });
    }
  } catch {
    // Fall through to mock
  }

  return NextResponse.json({ recommendations: MOCK_RECOMMENDATIONS });
}
