import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { MVP_COMMODITIES } from "@/lib/constants";

export async function GET() {
  try {
    const commodities = await prisma.dimCommodity.findMany({
      where: { isMvp: true },
      select: {
        id: true,
        namaDisplay: true,
        satuan: true,
        kategori: true,
      },
      orderBy: { namaDisplay: "asc" },
    });

    return NextResponse.json({ data: commodities });
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
