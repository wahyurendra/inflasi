"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Save } from "lucide-react";

export default function PengaturanPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [name, setName] = useState(user?.name || "");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch("/api/user/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (res.ok) {
        toast({ title: "Profil diperbarui", variant: "success" });
      } else {
        toast({ title: "Gagal memperbarui profil", variant: "destructive" });
      }
    } catch {
      toast({ title: "Terjadi kesalahan", variant: "destructive" });
    }
    setSaving(false);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast({ title: "Password minimal 6 karakter", variant: "destructive" });
      return;
    }
    setSaving(true);
    try {
      const res = await fetch("/api/user/password", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ oldPassword, newPassword }),
      });
      if (res.ok) {
        toast({ title: "Password diperbarui", variant: "success" });
        setOldPassword("");
        setNewPassword("");
      } else {
        const data = await res.json();
        toast({ title: data.error || "Gagal", variant: "destructive" });
      }
    } catch {
      toast({ title: "Terjadi kesalahan", variant: "destructive" });
    }
    setSaving(false);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-foreground">Pengaturan</h1>

      {/* Profile */}
      <div className="bg-card rounded-xl border p-6">
        <h2 className="text-sm font-semibold mb-4">Informasi Profil</h2>
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="space-y-2">
            <Label>Nama</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input value={user?.email || ""} disabled className="bg-muted" />
          </div>
          <Button type="submit" disabled={saving} size="sm">
            <Save className="h-4 w-4 mr-2" />
            Simpan
          </Button>
        </form>
      </div>

      {/* Password */}
      <div className="bg-card rounded-xl border p-6">
        <h2 className="text-sm font-semibold mb-4">Ubah Password</h2>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div className="space-y-2">
            <Label>Password Lama</Label>
            <Input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Password Baru</Label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimal 6 karakter"
              required
            />
          </div>
          <Button type="submit" disabled={saving} size="sm" variant="outline">
            Ubah Password
          </Button>
        </form>
      </div>
    </div>
  );
}
