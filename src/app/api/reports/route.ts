import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");
  const commodityId = searchParams.get("commodityId");
  const regionId = searchParams.get("regionId");
  const page = parseInt(searchParams.get("page") || "1");
  const limit = parseInt(searchParams.get("limit") || "20");

  try {
    const where: Record<string, unknown> = {};
    if (status) where.status = status;
    if (commodityId) where.commodityId = parseInt(commodityId);
    if (regionId) where.regionId = parseInt(regionId);

    const [reports, total] = await Promise.all([
      prisma.priceReport.findMany({
        where,
        include: {
          commodity: { select: { namaDisplay: true, kodeKomoditas: true } },
          region: { select: { namaProvinsi: true, kodeWilayah: true } },
          user: { select: { name: true } },
          photos: true,
        },
        orderBy: { createdAt: "desc" },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.priceReport.count({ where }),
    ]);

    return NextResponse.json({
      data: reports,
      total,
      page,
      totalPages: Math.ceil(total / limit),
    });
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

    const report = await prisma.priceReport.create({
      data: {
        userId: session.user.id,
        commodityId: parseInt(commodityId),
        regionId: parseInt(regionId),
        harga,
        satuan,
        namaPasar,
        kota,
        kecamatan,
        tanggal: new Date(tanggal),
        catatan,
        photos: photoUrls?.length
          ? {
              create: photoUrls.map((url: string) => ({
                url,
                filename: url.split("/").pop() || "photo",
              })),
            }
          : undefined,
      },
      include: {
        commodity: { select: { namaDisplay: true } },
        region: { select: { namaProvinsi: true } },
        photos: true,
      },
    });

    return NextResponse.json({ data: report }, { status: 201 });
  } catch (error) {
    console.error("Create report error:", error);
    return NextResponse.json(
      { error: "Gagal membuat laporan. Silakan coba lagi." },
      { status: 500 }
    );
  }
}
