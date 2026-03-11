"use client";

import Link from "next/link";
import { MessageSquare, Menu } from "lucide-react";
import { useState } from "react";
import {
  LayoutDashboard,
  TrendingUp,
  Map,
  AlertTriangle,
} from "lucide-react";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/komoditas", label: "Komoditas", icon: TrendingUp },
  { href: "/wilayah", label: "Wilayah", icon: Map },
  { href: "/alerts", label: "Alerts", icon: AlertTriangle },
  { href: "/ai", label: "AI", icon: MessageSquare },
];

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="border-b bg-white">
      <div className="flex items-center justify-between px-4 py-3 md:px-6">
        <div className="flex items-center gap-4">
          <button
            className="md:hidden p-1"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="md:hidden font-bold text-gray-900">INFLASI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/ai"
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            <MessageSquare className="h-4 w-4" />
            <span className="hidden sm:inline">AI Assistant</span>
          </Link>
        </div>
      </div>
      {/* Mobile nav */}
      {mobileMenuOpen && (
        <nav className="md:hidden border-t px-4 py-2 space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-medium"
                    : "text-gray-600"
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
