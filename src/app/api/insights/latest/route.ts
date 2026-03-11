import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const tipe = request.nextUrl.searchParams.get("type") || "harian";

  try {
    const insight = await prisma.analyticsInsight.findFirst({
      where: { tipe },
      orderBy: { tanggal: "desc" },
    });

    if (!insight) {
      return NextResponse.json({
        data: null,
        message: "Belum ada insight tersedia",
      });
    }

    return NextResponse.json({
      data: {
        id: insight.id,
        tanggal: insight.tanggal.toISOString().slice(0, 10),
        tipe: insight.tipe,
        judul: insight.judul,
        konten: insight.konten,
        dataSnapshot: insight.dataSnapshot,
      },
    });
  } catch {
    return NextResponse.json({ data: null, source: "mock" });
  }
}
