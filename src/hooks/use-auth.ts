"use client";

import { useSession } from "next-auth/react";

export function useAuth() {
  const { data: session, status } = useSession();
  const user = session?.user;
  const role = user?.role;

  return {
    user,
    role,
    status,
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
    isAdmin: role === "ADMIN",
    isAnalyst: role === "GOVERNMENT_ANALYST",
    isOfficer: role === "REGIONAL_OFFICER",
    isReporter: role === "REPORTER",
  };
}
