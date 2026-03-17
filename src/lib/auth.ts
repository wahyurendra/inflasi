import NextAuth from "next-auth";
import type { NextAuthConfig } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { apiClient } from "@/lib/api-client";

type UserRoleType = "ADMIN" | "GOVERNMENT_ANALYST" | "REGIONAL_OFFICER" | "REPORTER";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      role: UserRoleType;
      regionId?: number | null;
    };
  }
  interface User {
    role: UserRoleType;
    regionId?: number | null;
  }
}

export const authConfig: NextAuthConfig = {
  secret: process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET,
  trustHost: true,
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
  },
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        console.log("[AUTH] Login attempt:", credentials?.email);

        if (!credentials?.email || !credentials?.password) {
          console.log("[AUTH] Missing email or password");
          return null;
        }

        // Demo login — selalu tersedia
        if (
          credentials.email === "demo@inflasi.id" &&
          credentials.password === "demo123"
        ) {
          console.log("[AUTH] Demo reporter login success");
          return {
            id: "demo-reporter",
            name: "Reporter Demo",
            email: "demo@inflasi.id",
            role: "REPORTER" as const,
            regionId: null,
          };
        }

        // Database login via FastAPI backend
        try {
          console.log("[AUTH] Verifying credentials via API for:", credentials.email);
          const result = await apiClient.post<{
            authenticated: boolean;
            user: {
              id: string;
              name: string | null;
              email: string;
              image: string | null;
              role: UserRoleType;
              regionId: number | null;
            } | null;
          }>("/auth/verify-credentials", {
            email: credentials.email,
            password: credentials.password,
          });

          if (!result.authenticated || !result.user) {
            console.log("[AUTH] User not found or invalid:", credentials.email);
            return null;
          }

          console.log("[AUTH] API login success:", credentials.email, "role:", result.user.role);
          return {
            id: result.user.id,
            name: result.user.name,
            email: result.user.email,
            image: result.user.image,
            role: result.user.role,
            regionId: result.user.regionId,
          };
        } catch (error) {
          console.error("[AUTH] API error:", error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as { role: UserRoleType }).role;
        token.regionId = (user as { regionId?: number | null }).regionId;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub!;
        session.user.role = token.role as UserRoleType;
        session.user.regionId = token.regionId as number | null | undefined;
      }
      return session;
    },
  },
};

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);
