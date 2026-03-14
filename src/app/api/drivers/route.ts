import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const commodity = searchParams.get("commodity") || "CABAI_RAWIT";
  const region = searchParams.get("region") || "00";

  try {
    const analyticsUrl = process.env.ANALYTICS_API_URL || "http://localhost:8000";
    const resp = await fetch(
      `${analyticsUrl}/api/drivers/analysis?commodity=${commodity}&region=${region}`,
      { next: { revalidate: 300 } }
    );

    if (resp.ok) {
      const data = await resp.json();
      return NextResponse.json(data);
    }

    return NextResponse.json({
      commodity_code: commodity,
      region_code: region,
      drivers: [],
      message: "Analytics service tidak tersedia",
    });
  } catch (error) {
    console.error("Drivers error:", error);
    return NextResponse.json({
      commodity_code: commodity,
      region_code: region,
      drivers: [],
      error: "Analytics service error",
    }, { status: 503 });
  }
}
