import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export async function PATCH(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { oldPassword, newPassword } = body;

    if (!oldPassword || !newPassword) {
      return NextResponse.json({ error: "Password lama dan baru harus diisi" }, { status: 400 });
    }

    if (newPassword.length < 6) {
      return NextResponse.json({ error: "Password baru minimal 6 karakter" }, { status: 400 });
    }

    const opts = { userId: session.user.id, userRole: session.user.role };
    await apiClient.patch("/users/" + session.user.id + "/password", { oldPassword, newPassword }, opts);

    return NextResponse.json({ message: "Password berhasil diperbarui" });
  } catch (error) {
    const message =
      error instanceof Error && error.message.includes("400")
        ? "Password lama salah"
        : "Internal server error";
    const status = error instanceof Error && error.message.includes("400") ? 400 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
