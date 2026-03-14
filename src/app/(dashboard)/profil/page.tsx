"use client";

import { useAuth } from "@/hooks/use-auth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { User, Mail, Shield, MapPin, Award, Flame, FileText } from "lucide-react";

const roleLabels: Record<string, string> = {
  ADMIN: "Administrator",
  GOVERNMENT_ANALYST: "Analis Pemerintah",
  REGIONAL_OFFICER: "Petugas Wilayah",
  REPORTER: "Reporter Masyarakat",
};

export default function ProfilPage() {
  const { user } = useAuth();

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "?";

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-foreground">Profil Saya</h1>

      <div className="bg-card rounded-xl border p-6">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="bg-primary text-primary-foreground text-lg">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div>
            <h2 className="text-lg font-semibold">{user?.name || "Pengguna"}</h2>
            <Badge variant="outline">{roleLabels[user?.role || ""] || "Reporter"}</Badge>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-center gap-3 text-sm">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span>{user?.email || "-"}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span>{roleLabels[user?.role || ""]}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            <span>{user?.regionId ? `Region ${user.regionId}` : "Semua wilayah"}</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-card rounded-xl border p-4 text-center">
          <FileText className="h-5 w-5 mx-auto text-primary mb-1" />
          <p className="text-2xl font-bold">0</p>
          <p className="text-xs text-muted-foreground">Laporan</p>
        </div>
        <div className="bg-card rounded-xl border p-4 text-center">
          <Award className="h-5 w-5 mx-auto text-yellow-500 mb-1" />
          <p className="text-2xl font-bold">0</p>
          <p className="text-xs text-muted-foreground">Poin</p>
        </div>
        <div className="bg-card rounded-xl border p-4 text-center">
          <Flame className="h-5 w-5 mx-auto text-orange-500 mb-1" />
          <p className="text-2xl font-bold">0</p>
          <p className="text-xs text-muted-foreground">Streak</p>
        </div>
        <div className="bg-card rounded-xl border p-4 text-center">
          <User className="h-5 w-5 mx-auto text-blue-500 mb-1" />
          <p className="text-2xl font-bold">0</p>
          <p className="text-xs text-muted-foreground">Badge</p>
        </div>
      </div>
    </div>
  );
}
