import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

const protectedRoutes = ["/lapor", "/laporan", "/profil", "/pengaturan"];
const adminRoutes = ["/admin"];
const officerRoutes = ["/validasi"];
const analystRoutes = ["/intelligence"];

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const user = req.auth?.user;

  // Redirect unauthenticated root visitors to landing page
  if (pathname === "/" && !user) {
    return NextResponse.redirect(new URL("/welcome", req.nextUrl.origin));
  }

  // Redirect authenticated users away from landing/auth pages
  if ((pathname === "/welcome" || pathname === "/login" || pathname === "/register") && user) {
    return NextResponse.redirect(new URL("/", req.nextUrl.origin));
  }

  // Check protected routes that require any auth
  const isProtected = protectedRoutes.some((route) => pathname.startsWith(route));
  const isAdmin = adminRoutes.some((route) => pathname.startsWith(route));
  const isOfficer = officerRoutes.some((route) => pathname.startsWith(route));
  const isAnalyst = analystRoutes.some((route) => pathname.startsWith(route));

  if (isProtected || isAdmin || isOfficer || isAnalyst) {
    if (!user) {
      const loginUrl = new URL("/login", req.nextUrl.origin);
      loginUrl.searchParams.set("callbackUrl", pathname);
      return NextResponse.redirect(loginUrl);
    }

    if (isAdmin && user.role !== "ADMIN") {
      return NextResponse.redirect(new URL("/", req.nextUrl.origin));
    }

    if (isOfficer && !["ADMIN", "REGIONAL_OFFICER"].includes(user.role)) {
      return NextResponse.redirect(new URL("/", req.nextUrl.origin));
    }

    if (isAnalyst && !["ADMIN", "GOVERNMENT_ANALYST"].includes(user.role)) {
      return NextResponse.redirect(new URL("/", req.nextUrl.origin));
    }
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|uploads).*)",
  ],
};
