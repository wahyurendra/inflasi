"use client";

// Thin adapter over the Firebase AuthProvider. Keeps the same shape the app's
// components already consume (user / role / isAuthenticated / isAdmin / ...).
import { useAuthContext } from "@/lib/auth-context";

export function useAuth() {
  const { firebaseUser, profile, loading } = useAuthContext();
  const isAuthenticated = !!firebaseUser;
  const role = profile?.role;

  const user = profile
    ? {
        id: profile.id,
        name: profile.name ?? firebaseUser?.displayName ?? null,
        email: profile.email ?? firebaseUser?.email ?? null,
        image: profile.image ?? firebaseUser?.photoURL ?? null,
        role: profile.role,
        regionId: profile.regionId,
      }
    : undefined;

  return {
    user,
    role,
    status: loading ? "loading" : isAuthenticated ? "authenticated" : "unauthenticated",
    isLoading: loading,
    isAuthenticated,
    isAdmin: role === "ADMIN",
    isAnalyst: role === "GOVERNMENT_ANALYST",
    isOfficer: role === "REGIONAL_OFFICER",
    isReporter: role === "REPORTER",
  };
}
