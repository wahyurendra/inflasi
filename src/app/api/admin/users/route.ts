import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

const mockUsers = [
  { id: "1", name: "Admin Demo", email: "admin@inflasi.id", role: "ADMIN", isActive: true, createdAt: "2024-01-01", _count: { priceReports: 0 } },
  { id: "2", name: "Budi Santoso", email: "budi@gov.id", role: "GOVERNMENT_ANALYST", isActive: true, createdAt: "2024-02-15", _count: { priceReports: 0 } },
  { id: "3", name: "Siti Rahayu", email: "siti@regional.id", role: "REGIONAL_OFFICER", isActive: true, createdAt: "2024-03-10", _count: { priceReports: 5 } },
  { id: "4", name: "Ahmad Rizki", email: "ahmad@email.com", role: "REPORTER", isActive: true, createdAt: "2024-04-20", _count: { priceReports: 42 } },
  { id: "5", name: "Dewi Lestari", email: "dewi@email.com", role: "REPORTER", isActive: true, createdAt: "2024-05-05", _count: { priceReports: 28 } },
  { id: "6", name: "Eko Prasetyo", email: "eko@email.com", role: "REPORTER", isActive: false, createdAt: "2024-06-12", _count: { priceReports: 3 } },
];

export async function GET(request: NextRequest) {
  try {
    const session = await auth();
    if (!session?.user || session.user.role !== "ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const searchParams = request.nextUrl.searchParams;
    const page = parseInt(searchParams.get("page") || "1");
    const limit = parseInt(searchParams.get("limit") || "20");
    const role = searchParams.get("role");

    const where = role ? { role: role as "ADMIN" | "GOVERNMENT_ANALYST" | "REGIONAL_OFFICER" | "REPORTER" } : {};

    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        select: {
          id: true,
          name: true,
          email: true,
          role: true,
          isActive: true,
          createdAt: true,
          _count: { select: { priceReports: true } },
        },
        orderBy: { createdAt: "desc" },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.user.count({ where }),
    ]);

    return NextResponse.json({ data: users, total, page, limit });
  } catch {
    return NextResponse.json({ data: mockUsers, total: mockUsers.length, page: 1, limit: 20, source: "mock" });
  }
}

export async function PATCH(request: Request) {
  try {
    const session = await auth();
    if (!session?.user || session.user.role !== "ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const body = await request.json();
    const { userId, role, isActive } = body;

    if (!userId) {
      return NextResponse.json({ error: "userId is required" }, { status: 400 });
    }

    const updateData: Record<string, unknown> = {};
    if (role) updateData.role = role;
    if (typeof isActive === "boolean") updateData.isActive = isActive;

    const user = await prisma.user.update({
      where: { id: userId },
      data: updateData,
      select: { id: true, name: true, email: true, role: true, isActive: true },
    });

    return NextResponse.json({ data: user });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
