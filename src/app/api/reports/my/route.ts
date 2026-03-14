import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get("page") || "1");
  const limit = parseInt(searchParams.get("limit") || "20");

  try {
    const [reports, total] = await Promise.all([
      prisma.priceReport.findMany({
        where: { userId: session.user.id },
        include: {
          commodity: { select: { namaDisplay: true, kodeKomoditas: true } },
          region: { select: { namaProvinsi: true, kodeWilayah: true } },
          photos: true,
        },
        orderBy: { createdAt: "desc" },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.priceReport.count({ where: { userId: session.user.id } }),
    ]);

    return NextResponse.json({
      data: reports,
      total,
      page,
      totalPages: Math.ceil(total / limit),
    });
  } catch {
    return NextResponse.json({
      data: [],
      total: 0,
      page: 1,
      totalPages: 0,
      source: "mock",
    });
  }
}
