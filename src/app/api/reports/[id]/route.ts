import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const report = await apiClient.get("/reports/" + params.id);

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

    const opts = { userId: session.user.id, userRole: session.user.role };
    const report = await apiClient.patch("/reports/" + params.id, { status, rejectionNote }, opts);

    return NextResponse.json({ data: report });
  } catch (error) {
    console.error("Update report error:", error);
    return NextResponse.json(
      { error: "Gagal memperbarui laporan" },
      { status: 500 }
    );
  }
}
