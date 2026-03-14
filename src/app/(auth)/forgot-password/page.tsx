"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // TODO: Implement actual password reset email
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSent(true);
    setLoading(false);
  };

  return (
    <div className="bg-card rounded-xl border shadow-sm p-6">
      <h2 className="text-xl font-semibold text-center mb-2">Lupa Password</h2>
      <p className="text-sm text-muted-foreground text-center mb-6">
        Masukkan email Anda untuk menerima link reset password
      </p>

      {sent ? (
        <div className="text-center space-y-4">
          <div className="bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300 p-4 rounded-lg text-sm">
            Jika email terdaftar, link reset password telah dikirim ke <strong>{email}</strong>.
            Silakan periksa inbox Anda.
          </div>
          <Link href="/login">
            <Button variant="outline" className="w-full">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Kembali ke Halaman Masuk
            </Button>
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="nama@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            <Mail className="h-4 w-4 mr-2" />
            {loading ? "Mengirim..." : "Kirim Link Reset"}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            <Link href="/login" className="text-primary hover:underline">
              Kembali ke halaman masuk
            </Link>
          </p>
        </form>
      )}
    </div>
  );
}
