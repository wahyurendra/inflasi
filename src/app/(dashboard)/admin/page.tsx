"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Users,
  Shield,
  FileText,
  TrendingUp,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
} from "lucide-react";

const roleLabels: Record<string, string> = {
  ADMIN: "Admin",
  GOVERNMENT_ANALYST: "Analis",
  REGIONAL_OFFICER: "Petugas",
  REPORTER: "Reporter",
};

const roleVariants: Record<string, "default" | "secondary" | "outline"> = {
  ADMIN: "default",
  GOVERNMENT_ANALYST: "secondary",
  REGIONAL_OFFICER: "secondary",
  REPORTER: "outline",
};

interface AdminStats {
  totalUsers: number;
  activeUsers: number;
  totalReports: number;
  pendingReports: number;
  approvedReports: number;
  rejectedReports: number;
  flaggedReports: number;
  reportsToday: number;
  reportsThisWeek: number;
  reportsThisMonth: number;
  usersByRole: Record<string, number>;
}

interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  isActive: boolean;
  createdAt: string;
  _count: { priceReports: number };
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [roleFilter, setRoleFilter] = useState<string>("all");

  const { data: statsData } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: async () => {
      const res = await fetch("/api/admin/stats");
      if (!res.ok) throw new Error("Failed");
      return res.json();
    },
  });

  const { data: usersData } = useQuery({
    queryKey: ["admin-users", roleFilter],
    queryFn: async () => {
      const params = roleFilter !== "all" ? `?role=${roleFilter}` : "";
      const res = await fetch(`/api/admin/users${params}`);
      if (!res.ok) throw new Error("Failed");
      return res.json();
    },
  });

  const updateUser = useMutation({
    mutationFn: async (data: { userId: string; role?: string; isActive?: boolean }) => {
      const res = await fetch("/api/admin/users", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
    },
  });

  const stats: AdminStats = statsData?.data || {
    totalUsers: 0, activeUsers: 0, totalReports: 0,
    pendingReports: 0, approvedReports: 0, rejectedReports: 0,
    flaggedReports: 0, reportsToday: 0, reportsThisWeek: 0,
    reportsThisMonth: 0, usersByRole: {},
  };

  const users: AdminUser[] = usersData?.data || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Admin Panel
        </h1>
        <p className="text-sm text-muted-foreground">Kelola pengguna dan pantau sistem</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Users className="h-4 w-4" />
            Total Pengguna
          </div>
          <p className="text-2xl font-bold">{stats.totalUsers}</p>
          <p className="text-xs text-muted-foreground">{stats.activeUsers} aktif</p>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <FileText className="h-4 w-4" />
            Total Laporan
          </div>
          <p className="text-2xl font-bold">{stats.totalReports}</p>
          <p className="text-xs text-muted-foreground">{stats.reportsToday} hari ini</p>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Clock className="h-4 w-4 text-yellow-500" />
            Pending
          </div>
          <p className="text-2xl font-bold text-yellow-600">{stats.pendingReports}</p>
          <p className="text-xs text-muted-foreground">{stats.flaggedReports} flagged</p>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <TrendingUp className="h-4 w-4 text-primary" />
            Minggu Ini
          </div>
          <p className="text-2xl font-bold">{stats.reportsThisWeek}</p>
          <p className="text-xs text-muted-foreground">{stats.reportsThisMonth} bulan ini</p>
        </div>
      </div>

      {/* Report Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-card rounded-xl border p-4 flex items-center gap-3">
          <CheckCircle className="h-8 w-8 text-green-500" />
          <div>
            <p className="text-xl font-bold">{stats.approvedReports}</p>
            <p className="text-xs text-muted-foreground">Disetujui</p>
          </div>
        </div>
        <div className="bg-card rounded-xl border p-4 flex items-center gap-3">
          <XCircle className="h-8 w-8 text-red-500" />
          <div>
            <p className="text-xl font-bold">{stats.rejectedReports}</p>
            <p className="text-xs text-muted-foreground">Ditolak</p>
          </div>
        </div>
        <div className="bg-card rounded-xl border p-4 flex items-center gap-3">
          <AlertTriangle className="h-8 w-8 text-orange-500" />
          <div>
            <p className="text-xl font-bold">{stats.flaggedReports}</p>
            <p className="text-xs text-muted-foreground">Ditandai</p>
          </div>
        </div>
      </div>

      {/* User Management */}
      <div className="bg-card rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold">Manajemen Pengguna</h2>
          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Role</SelectItem>
              <SelectItem value="ADMIN">Admin</SelectItem>
              <SelectItem value="GOVERNMENT_ANALYST">Analis</SelectItem>
              <SelectItem value="REGIONAL_OFFICER">Petugas</SelectItem>
              <SelectItem value="REPORTER">Reporter</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2 font-medium text-muted-foreground">Nama</th>
                <th className="text-left p-2 font-medium text-muted-foreground">Email</th>
                <th className="text-left p-2 font-medium text-muted-foreground">Role</th>
                <th className="text-center p-2 font-medium text-muted-foreground">Laporan</th>
                <th className="text-center p-2 font-medium text-muted-foreground">Status</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="p-2 font-medium">{user.name}</td>
                  <td className="p-2 text-muted-foreground">{user.email}</td>
                  <td className="p-2">
                    <Badge variant={roleVariants[user.role] || "outline"}>
                      {roleLabels[user.role] || user.role}
                    </Badge>
                  </td>
                  <td className="p-2 text-center">{user._count.priceReports}</td>
                  <td className="p-2 text-center">
                    <Badge variant={user.isActive ? "default" : "secondary"}>
                      {user.isActive ? "Aktif" : "Nonaktif"}
                    </Badge>
                  </td>
                  <td className="p-2 text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        updateUser.mutate({
                          userId: user.id,
                          isActive: !user.isActive,
                        })
                      }
                    >
                      {user.isActive ? "Nonaktifkan" : "Aktifkan"}
                    </Button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-muted-foreground">
                    Tidak ada data pengguna
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
