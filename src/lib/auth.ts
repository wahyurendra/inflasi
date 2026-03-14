import NextAuth from "next-auth";
import type { NextAuthConfig } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { PrismaAdapter } from "@auth/prisma-adapter";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/db";

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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  adapter: PrismaAdapter(prisma) as any,
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
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const user = await prisma.user.findUnique({
            where: { email: credentials.email as string },
          });

          if (!user || !user.hashedPassword || !user.isActive) return null;

          const passwordMatch = await bcrypt.compare(
            credentials.password as string,
            user.hashedPassword
          );

          if (!passwordMatch) return null;

          return {
            id: user.id,
            name: user.name,
            email: user.email,
            image: user.image,
            role: user.role,
            regionId: user.regionId,
          };
        } catch {
          // DB not available — allow demo login
          if (
            credentials.email === "admin@inflasi.id" &&
            credentials.password === "admin123"
          ) {
            return {
              id: "demo-admin",
              name: "Admin Demo",
              email: "admin@inflasi.id",
              role: "ADMIN" as const,
              regionId: null,
            };
          }
          if (
            credentials.email === "demo@inflasi.id" &&
            credentials.password === "demo123"
          ) {
            return {
              id: "demo-reporter",
              name: "Reporter Demo",
              email: "demo@inflasi.id",
              role: "REPORTER" as const,
              regionId: null,
            };
          }
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
