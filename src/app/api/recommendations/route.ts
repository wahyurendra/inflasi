import { NextResponse } from "next/server";

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

    return NextResponse.json({
      recommendations: [],
      message: "Analytics service tidak tersedia",
    });
  } catch (error) {
    console.error("Recommendations error:", error);
    return NextResponse.json({
      recommendations: [],
      error: "Analytics service error",
    }, { status: 503 });
  }
}
