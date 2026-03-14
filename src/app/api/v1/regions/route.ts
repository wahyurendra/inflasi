import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { REGIONS } from "@/lib/constants";

export async function GET() {
  try {
    const regions = await prisma.dimRegion.findMany({
      select: {
        id: true,
        namaProvinsi: true,
        kodeWilayah: true,
        levelWilayah: true,
      },
      orderBy: { namaProvinsi: "asc" },
    });

    return NextResponse.json({ data: regions });
  } catch {
    const data = REGIONS.map((r, i) => ({
      id: i + 1,
      namaProvinsi: r.provinsi,
      kodeProvinsi: r.kode,
      pulau: "Indonesia",
    }));
    return NextResponse.json({ data, source: "mock" });
  }
}
