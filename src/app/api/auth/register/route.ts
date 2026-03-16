import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, email, password, role } = body;

    if (!name || !email || !password) {
      return NextResponse.json(
        { error: "Nama, email, dan password wajib diisi" },
        { status: 400 }
      );
    }

    if (password.length < 6) {
      return NextResponse.json(
        { error: "Password minimal 6 karakter" },
        { status: 400 }
      );
    }

    const user = await apiClient.post<{
      id: string;
      name: string;
      email: string;
      role: string;
    }>("/auth/register", { name, email, password, role });

    return NextResponse.json({ user }, { status: 201 });
  } catch (error) {
    console.error("Registration error:", error);

    const message =
      error instanceof Error && error.message.includes("409")
        ? "Email sudah terdaftar"
        : "Gagal mendaftarkan akun. Silakan coba lagi.";
    const status =
      error instanceof Error && error.message.includes("409") ? 409 : 500;

    return NextResponse.json({ error: message }, { status });
  }
}
