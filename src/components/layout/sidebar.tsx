"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Map,
  AlertTriangle,
  MessageSquare,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/komoditas", label: "Harga Komoditas", icon: TrendingUp },
  { href: "/wilayah", label: "Peta Wilayah", icon: Map },
  { href: "/alerts", label: "Alert Center", icon: AlertTriangle },
  { href: "/ai", label: "AI Assistant", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-white">
      <div className="p-6">
        <h1 className="text-xl font-bold text-gray-900">INFLASI</h1>
        <p className="text-xs text-gray-500 mt-1">
          Pemantauan Inflasi Pangan
        </p>
      </div>
      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t">
        <p className="text-xs text-gray-400">MVP v0.1.0</p>
      </div>
    </aside>
  );
}
