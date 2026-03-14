import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const report = await prisma.priceReport.findUnique({
      where: { id: params.id },
      include: {
        commodity: true,
        region: true,
        user: { select: { name: true, email: true } },
        photos: true,
      },
    });

    if (!report) {
      return NextResponse.json({ error: "Laporan tidak ditemukan" }, { status: 404 });
    }

    return NextResponse.json({ data: report });
  } catch {
    return NextResponse.json({ error: "Gagal mengambil data laporan" }, { status: 500 });
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } }
) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const role = session.user.role;
  if (!["ADMIN", "REGIONAL_OFFICER"].includes(role)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    const body = await request.json();
    const { status, rejectionNote } = body;

    if (!["APPROVED", "REJECTED", "FLAGGED", "PENDING"].includes(status)) {
      return NextResponse.json({ error: "Status tidak valid" }, { status: 400 });
    }

    const report = await prisma.priceReport.update({
      where: { id: params.id },
      data: {
        status,
        rejectionNote: status === "REJECTED" ? rejectionNote : undefined,
        reviewedBy: session.user.id,
        reviewedAt: new Date(),
      },
      include: {
        commodity: { select: { namaDisplay: true } },
        region: { select: { namaProvinsi: true } },
      },
    });

    return NextResponse.json({ data: report });
  } catch (error) {
    console.error("Update report error:", error);
    return NextResponse.json(
      { error: "Gagal memperbarui laporan" },
      { status: 500 }
    );
  }
}
