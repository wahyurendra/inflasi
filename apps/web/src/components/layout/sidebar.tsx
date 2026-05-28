"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import {
  LayoutDashboard,
  TrendingUp,
  Map,
  AlertTriangle,
  MessageSquare,
  Globe,
  Truck,
  PlusCircle,
  FileText,
  CheckSquare,
  BarChart3,
  Trophy,
  Shield,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  roles?: string[];
  section?: string;
}

const navItems: NavItem[] = [
  // Dashboard
  { href: "/", label: "Overview", icon: LayoutDashboard, section: "Dashboard" },
  { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp, section: "Dashboard" },
  { href: "/wilayah", label: "Peta Wilayah", icon: Map, section: "Dashboard" },
  { href: "/global", label: "Global Signals", icon: Globe, section: "Dashboard" },
  { href: "/alerts", label: "Alert Center", icon: AlertTriangle, section: "Dashboard" },
  // Reporting
  { href: "/lapor", label: "Lapor Harga", icon: PlusCircle, roles: ["ADMIN", "REGIONAL_OFFICER", "REPORTER"], section: "Pelaporan" },
  { href: "/laporan", label: "Laporan Saya", icon: FileText, roles: ["REPORTER"], section: "Pelaporan" },
  // Intelligence
  { href: "/intelligence", label: "Price Intelligence", icon: BarChart3, roles: ["ADMIN", "GOVERNMENT_ANALYST"], section: "Analisis" },
  { href: "/recommendations", label: "Rekomendasi", icon: Truck, roles: ["ADMIN", "GOVERNMENT_ANALYST"], section: "Analisis" },
  // Validation
  { href: "/validasi", label: "Validasi Laporan", icon: CheckSquare, roles: ["ADMIN", "REGIONAL_OFFICER"], section: "Validasi" },
  // Community
  { href: "/leaderboard", label: "Leaderboard", icon: Trophy, section: "Komunitas" },
  { href: "/ai", label: "AI Assistant", icon: MessageSquare, section: "Komunitas" },
  // Admin
  { href: "/admin", label: "Admin Panel", icon: Shield, roles: ["ADMIN"], section: "Admin" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { role, isAuthenticated } = useAuth();

  const filteredItems = navItems.filter((item) => {
    if (!item.roles) return true;
    if (!isAuthenticated) return false;
    return item.roles.includes(role || "");
  });

  let lastSection = "";

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-card">
      <div className="p-6">
        <h1 className="text-xl font-bold text-primary">Inflasi.id</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Pemantauan Harga Pangan
        </p>
      </div>
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        {filteredItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;

          const showSection = item.section && item.section !== lastSection;
          if (item.section) lastSection = item.section;

          return (
            <div key={item.href}>
              {showSection && (
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold px-3 pt-4 pb-1">
                  {item.section}
                </p>
              )}
              <Link
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            </div>
          );
        })}
      </nav>
      <div className="p-4 border-t">
        <p className="text-xs text-muted-foreground">Inflasi.id v1.0.0</p>
      </div>
    </aside>
  );
}
