"use client";

// Client-side route protection. With pure Firebase auth there's no server session
// cookie, so guarding moves here (replaces the old NextAuth middleware). Requires a
// signed-in user for the dashboard, plus role checks for admin/officer/analyst areas.
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

const ADMIN_ROUTES = ["/admin"];
const OFFICER_ROUTES = ["/validasi"];
const ANALYST_ROUTES = ["/intelligence"];

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, role } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.replace(`/login?callbackUrl=${encodeURIComponent(pathname)}`);
      return;
    }
    const r = role ?? "";
    if (ADMIN_ROUTES.some((x) => pathname.startsWith(x)) && r !== "ADMIN") {
      router.replace("/");
    } else if (OFFICER_ROUTES.some((x) => pathname.startsWith(x)) && !["ADMIN", "REGIONAL_OFFICER"].includes(r)) {
      router.replace("/");
    } else if (ANALYST_ROUTES.some((x) => pathname.startsWith(x)) && !["ADMIN", "GOVERNMENT_ANALYST"].includes(r)) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, role, pathname, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center text-muted-foreground">
        Memuat...
      </div>
    );
  }
  return <>{children}</>;
}
