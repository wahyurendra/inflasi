import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const params: Record<string, string> = {};

  const status = searchParams.get("status");
  const commodityId = searchParams.get("commodityId");
  const regionId = searchParams.get("regionId");
  const page = searchParams.get("page") || "1";
  const limit = searchParams.get("limit") || "20";

  params.page = page;
  params.limit = limit;
  if (status) params.status = status;
  if (commodityId) params.commodityId = commodityId;
  if (regionId) params.regionId = regionId;

  try {
    const data = await apiClient.get("/reports/", params);
    return NextResponse.json(data);
  } catch (error) {
    console.error("Reports GET error:", error);
    return NextResponse.json({
      data: [],
      total: 0,
      page: 1,
      totalPages: 0,
      error: "Database error",
    }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body = await request.json();
    const {
      commodityId,
      regionId,
      harga,
      satuan,
      namaPasar,
      kota,
      kecamatan,
      tanggal,
      catatan,
      photoUrls,
    } = body;

    if (!commodityId || !regionId || !harga || !satuan || !namaPasar || !tanggal) {
      return NextResponse.json(
        { error: "Data tidak lengkap" },
        { status: 400 }
      );
    }

    const opts = { userId: session.user.id, userRole: session.user.role };
    const report = await apiClient.post("/reports/", {
      commodityId,
      regionId,
      harga,
      satuan,
      namaPasar,
      kota,
      kecamatan,
      tanggal,
      catatan,
      photoUrls,
    }, opts);

    return NextResponse.json({ data: report }, { status: 201 });
  } catch (error) {
    console.error("Create report error:", error);
    return NextResponse.json(
      { error: "Gagal membuat laporan. Silakan coba lagi." },
      { status: 500 }
    );
  }
}
