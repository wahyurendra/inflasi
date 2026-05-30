"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthContext } from "@/lib/auth-context";
import { useAuth } from "@/hooks/use-auth";
import { useUnreadCount } from "@/hooks/use-notifications";
import {
  LayoutDashboard,
  TrendingUp,
  Map,
  AlertTriangle,
  MessageSquare,
  Menu,
  Moon,
  Sun,
  LogIn,
  LogOut,
  User,
  Settings,
  Bell,
  ChevronRight,
  PlusCircle,
  FileText,
  CheckSquare,
  BarChart3,
  Trophy,
  Shield,
  Database,
  Globe,
  Truck,
  Home,
  LineChart,
  type LucideIcon,
} from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

// Route → page metadata for breadcrumb. Keep keys aligned with sidebar.
const ROUTE_META: Record<string, { label: string; icon: LucideIcon }> = {
  "/beranda": { label: "Beranda", icon: Home },
  "/lapor": { label: "Lapor Harga", icon: PlusCircle },
  "/laporan": { label: "Laporan Saya", icon: FileText },
  "/validasi": { label: "Validasi Laporan", icon: CheckSquare },
  "/komoditas": { label: "Harga Komoditas", icon: TrendingUp },
  "/wilayah": { label: "Peta Wilayah", icon: Map },
  "/alerts": { label: "Alert Center", icon: AlertTriangle },
  "/intelligence": { label: "Price Intelligence", icon: BarChart3 },
  "/recommendations": { label: "Rekomendasi", icon: Truck },
  "/global": { label: "Global Signals", icon: Globe },
  "/leaderboard": { label: "Leaderboard", icon: Trophy },
  "/ai": { label: "AI Assistant", icon: MessageSquare },
  "/admin": { label: "Admin Panel", icon: Shield },
  "/admin/models": { label: "Model Registry", icon: Database },
  "/profil": { label: "Profil", icon: User },
  "/pengaturan": { label: "Pengaturan", icon: Settings },
  "/notifications": { label: "Notifikasi", icon: Bell },
};

function resolveRouteMeta(pathname: string): { label: string; icon: LucideIcon } {
  // Exact match first
  if (ROUTE_META[pathname]) return ROUTE_META[pathname];
  // Longest prefix match
  const candidates = Object.keys(ROUTE_META)
    .filter((p) => pathname.startsWith(p + "/"))
    .sort((a, b) => b.length - a.length);
  if (candidates[0]) return ROUTE_META[candidates[0]];
  return { label: "Dashboard", icon: LayoutDashboard };
}

const ROLE_LABEL: Record<string, string> = {
  ADMIN: "Administrator",
  GOVERNMENT_ANALYST: "Analis Pemerintah",
  REGIONAL_OFFICER: "Petugas Wilayah",
  REPORTER: "Reporter",
};

const ROLE_BADGE: Record<string, string> = {
  ADMIN: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/30 dark:text-purple-300 dark:border-purple-900",
  GOVERNMENT_ANALYST: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-300 dark:border-blue-900",
  REGIONAL_OFFICER: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900",
  REPORTER: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/30 dark:text-orange-300 dark:border-orange-900",
};

const mobileNav = [
  { href: "/beranda", label: "Beranda", icon: Home },
  { href: "/komoditas", label: "Komoditas", icon: TrendingUp },
  { href: "/wilayah", label: "Wilayah", icon: Map },
  { href: "/alerts", label: "Alerts", icon: AlertTriangle },
  { href: "/ai", label: "AI", icon: MessageSquare },
];

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { user, isAuthenticated, role } = useAuth();
  const { logout } = useAuthContext();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.count || 0;

  const meta = resolveRouteMeta(pathname);
  const MetaIcon = meta.icon;

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?";
  const firstName = user?.name?.split(" ")[0] ?? "";

  return (
    <header className="border-b bg-card h-14 flex items-center px-4 md:px-6 shrink-0">
      {/* Left: mobile menu + breadcrumb */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <button
          type="button"
          className="md:hidden p-1.5 -ml-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Buka menu"
        >
          <Menu className="h-4 w-4" />
        </button>

        {/* Mobile brand */}
        <Link
          href="/beranda"
          className="md:hidden flex items-center gap-1.5 font-semibold text-foreground text-sm"
        >
          <LineChart className="h-4 w-4 text-primary" />
          Inflasi.id
        </Link>

        {/* Desktop breadcrumb */}
        <nav
          aria-label="Breadcrumb"
          className="hidden md:flex items-center gap-1.5 text-[13px] min-w-0"
        >
          <Link
            href="/beranda"
            className="text-muted-foreground hover:text-foreground transition-colors flex items-center"
          >
            <Home className="h-3.5 w-3.5" />
          </Link>
          <ChevronRight className="h-3 w-3 text-muted-foreground/40 shrink-0" />
          <span className="inline-flex items-center gap-1.5 font-semibold text-foreground truncate">
            <MetaIcon className="h-3.5 w-3.5 text-primary shrink-0" />
            <span className="truncate">{meta.label}</span>
          </span>
        </nav>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-1.5 shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Ubah tema"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        {isAuthenticated && (
          <Link href="/notifications">
            <Button
              variant="ghost"
              size="icon"
              className="relative h-8 w-8"
              aria-label={`Notifikasi${unreadCount > 0 ? ` (${unreadCount} belum dibaca)` : ""}`}
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 h-3.5 w-3.5 rounded-full bg-risk-critical text-[9px] font-bold text-white flex items-center justify-center ring-2 ring-card">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Button>
          </Link>
        )}

        {isAuthenticated ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex items-center gap-2 pl-1.5 pr-2 py-1 rounded-full border border-transparent hover:bg-accent hover:border-border transition-colors"
                aria-label="Menu pengguna"
              >
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="bg-primary text-primary-foreground text-[11px] font-semibold">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden sm:flex flex-col items-start leading-tight">
                  <span className="text-[12px] font-semibold text-foreground max-w-[120px] truncate">
                    {firstName}
                  </span>
                  {role && (
                    <span
                      className={`text-[9px] font-medium px-1.5 rounded-full border ${ROLE_BADGE[role] ?? "bg-muted text-muted-foreground border-border"}`}
                    >
                      {ROLE_LABEL[role] ?? role}
                    </span>
                  )}
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-semibold">{user?.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                  {role && (
                    <span
                      className={`mt-1 inline-flex w-fit text-[10px] font-medium px-1.5 py-0.5 rounded-full border ${ROLE_BADGE[role] ?? "bg-muted text-muted-foreground border-border"}`}
                    >
                      {ROLE_LABEL[role] ?? role}
                    </span>
                  )}
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/profil" className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Profil
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/pengaturan" className="cursor-pointer">
                  <Settings className="mr-2 h-4 w-4" />
                  Pengaturan
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={async () => {
                  await logout();
                  router.push("/login");
                }}
                className="cursor-pointer text-risk-critical focus:text-risk-critical"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Keluar
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Link href="/login">
            <Button size="sm" variant="outline" className="h-8">
              <LogIn className="h-3.5 w-3.5 mr-1.5" />
              Masuk
            </Button>
          </Link>
        )}
      </div>

      {/* Mobile menu drawer */}
      {mobileMenuOpen && (
        <nav className="md:hidden absolute top-14 inset-x-0 z-40 border-b border-t bg-card px-4 py-2 space-y-1 shadow-md">
          {mobileNav.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm ${
                  isActive
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
}
