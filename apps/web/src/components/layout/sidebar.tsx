"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import type { UserRole } from "@/lib/auth-context";
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
  LineChart,
  Database,
  PanelLeftClose,
  PanelLeftOpen,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

// Per-persona navigation map. Order is task-flow-optimized for each role —
// not a single filtered list.
const NAV_BY_ROLE: Record<UserRole | "PUBLIC", NavSection[]> = {
  REPORTER: [
    {
      title: "Beranda",
      items: [
        { href: "/beranda", label: "Beranda", icon: LayoutDashboard },
        { href: "/lapor", label: "Lapor Harga", icon: PlusCircle },
        { href: "/laporan", label: "Laporan Saya", icon: FileText },
      ],
    },
    {
      title: "Pasar",
      items: [
        { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp },
        { href: "/wilayah", label: "Peta Wilayah", icon: Map },
        { href: "/alerts", label: "Alert Center", icon: AlertTriangle },
      ],
    },
    {
      title: "Komunitas",
      items: [
        { href: "/leaderboard", label: "Leaderboard", icon: Trophy },
        { href: "/ai", label: "AI Assistant", icon: MessageSquare },
      ],
    },
  ],

  REGIONAL_OFFICER: [
    {
      title: "Operasional",
      items: [
        { href: "/beranda", label: "Beranda", icon: LayoutDashboard },
        { href: "/validasi", label: "Validasi Laporan", icon: CheckSquare },
        { href: "/alerts", label: "Alert Center", icon: AlertTriangle },
        { href: "/wilayah", label: "Peta Wilayah", icon: Map },
      ],
    },
    {
      title: "Pelaporan",
      items: [
        { href: "/lapor", label: "Lapor Harga", icon: PlusCircle },
        { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp },
      ],
    },
    {
      title: "Asisten",
      items: [{ href: "/ai", label: "AI Assistant", icon: MessageSquare }],
    },
  ],

  GOVERNMENT_ANALYST: [
    {
      title: "Analisis",
      items: [
        { href: "/beranda", label: "Beranda", icon: LayoutDashboard },
        { href: "/intelligence", label: "Price Intelligence", icon: BarChart3 },
        { href: "/recommendations", label: "Rekomendasi", icon: Truck },
        { href: "/alerts", label: "Alert Center", icon: AlertTriangle },
      ],
    },
    {
      title: "Data Pasar",
      items: [
        { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp },
        { href: "/wilayah", label: "Peta Wilayah", icon: Map },
        { href: "/global", label: "Global Signals", icon: Globe },
      ],
    },
    {
      title: "Asisten",
      items: [{ href: "/ai", label: "AI Assistant", icon: MessageSquare }],
    },
  ],

  ADMIN: [
    {
      title: "Admin",
      items: [
        { href: "/beranda", label: "Beranda", icon: LayoutDashboard },
        { href: "/admin", label: "Admin Panel", icon: Shield },
        { href: "/admin/models", label: "Model Registry", icon: Database },
        { href: "/validasi", label: "Validasi Laporan", icon: CheckSquare },
      ],
    },
    {
      title: "Analisis",
      items: [
        { href: "/intelligence", label: "Price Intelligence", icon: BarChart3 },
        { href: "/recommendations", label: "Rekomendasi", icon: Truck },
        { href: "/alerts", label: "Alert Center", icon: AlertTriangle },
      ],
    },
    {
      title: "Data Pasar",
      items: [
        { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp },
        { href: "/wilayah", label: "Peta Wilayah", icon: Map },
        { href: "/global", label: "Global Signals", icon: Globe },
        { href: "/leaderboard", label: "Leaderboard", icon: Trophy },
      ],
    },
    {
      title: "Asisten",
      items: [{ href: "/ai", label: "AI Assistant", icon: MessageSquare }],
    },
  ],

  PUBLIC: [
    {
      title: "Dashboard",
      items: [
        { href: "/beranda", label: "Beranda", icon: LayoutDashboard },
        { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp },
        { href: "/wilayah", label: "Peta Wilayah", icon: Map },
        { href: "/global", label: "Global Signals", icon: Globe },
        { href: "/alerts", label: "Alert Center", icon: AlertTriangle },
      ],
    },
    {
      title: "Komunitas",
      items: [
        { href: "/leaderboard", label: "Leaderboard", icon: Trophy },
        { href: "/ai", label: "AI Assistant", icon: MessageSquare },
      ],
    },
  ],
};

const STORAGE_KEY = "inflasi:sidebar:collapsed";

function useSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === "1") setCollapsed(true);
    } catch {
      // ignore
    }
    setHydrated(true);
  }, []);

  const toggle = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
      } catch {
        // ignore
      }
      return next;
    });
  };

  return { collapsed, toggle, hydrated };
}

export function Sidebar() {
  const pathname = usePathname();
  const { role, isAuthenticated } = useAuth();
  const { collapsed, toggle, hydrated } = useSidebarCollapsed();

  const sections =
    NAV_BY_ROLE[(isAuthenticated && role ? role : "PUBLIC") as keyof typeof NAV_BY_ROLE] ??
    NAV_BY_ROLE.PUBLIC;

  // Avoid layout flash before hydration reads the persisted value.
  const widthClass = !hydrated || !collapsed ? "w-60" : "w-14";

  return (
    <aside
      className={`hidden md:flex ${widthClass} flex-col border-r bg-card transition-[width] duration-150`}
    >
      <div
        className={`flex items-center border-b ${
          collapsed ? "justify-center px-2 py-3" : "justify-between px-5 py-5"
        }`}
      >
        {collapsed ? (
          <button
            type="button"
            onClick={toggle}
            aria-label="Perluas sidebar"
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
          >
            <PanelLeftOpen className="h-4 w-4" />
          </button>
        ) : (
          <>
            <div>
              <div className="flex items-baseline gap-1.5">
                <LineChart className="h-4 w-4 text-primary" />
                <h1 className="text-base font-semibold tracking-tight">Inflasi.id</h1>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Pemantauan Harga Pangan
              </p>
            </div>
            <button
              type="button"
              onClick={toggle}
              aria-label="Sembunyikan sidebar"
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </>
        )}
      </div>

      <nav
        className={`flex-1 overflow-y-auto overflow-x-hidden ${
          collapsed ? "px-1.5 py-3 space-y-3" : "px-2 py-3 space-y-4"
        }`}
      >
        {sections.map((section) => (
          <div key={section.title}>
            {!collapsed && (
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold px-3 pb-1.5">
                {section.title}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(item.href + "/"));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    aria-label={item.label}
                    className={`flex items-center rounded-md text-[13px] font-medium transition-colors ${
                      collapsed
                        ? "justify-center h-9 w-9 mx-auto"
                        : "gap-2.5 px-3 py-1.5"
                    } ${
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5 shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {!collapsed && (
        <div className="px-5 py-3 border-t">
          <p className="text-[10px] text-muted-foreground">
            {role ? `Mode: ${roleLabel(role)}` : "Mode: Publik"}
          </p>
          <p className="text-[10px] text-muted-foreground/70 mt-0.5">v1.0.0</p>
        </div>
      )}
    </aside>
  );
}

function roleLabel(role: UserRole): string {
  switch (role) {
    case "ADMIN":
      return "Administrator";
    case "GOVERNMENT_ANALYST":
      return "Analis Pemerintah";
    case "REGIONAL_OFFICER":
      return "Petugas Wilayah";
    case "REPORTER":
      return "Reporter";
    default:
      return role;
  }
}
