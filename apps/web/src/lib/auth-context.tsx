"use client";

// Firebase-based auth context. Replaces NextAuth. Provides the signed-in user, the
// app profile (role/region come from the api-gateway, not the token), and auth actions.
//
// Token threading: we wrap window.fetch so every same-origin /api/* request carries
// `Authorization: Bearer <Firebase ID token>` while signed in. The Next.js BFF routes
// forward that header to the api-gateway, which verifies it. This avoids touching
// every data hook.

import {
  createContext, useContext, useEffect, useMemo, useRef, useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged, signInWithEmailAndPassword, signInWithPopup,
  createUserWithEmailAndPassword, sendPasswordResetEmail, updateProfile, signOut,
  type User as FirebaseUser,
} from "firebase/auth";
import { auth, googleProvider } from "@/lib/firebase";

export type UserRole = "ADMIN" | "GOVERNMENT_ANALYST" | "REGIONAL_OFFICER" | "REPORTER";

export interface AppProfile {
  id: string;
  name: string | null;
  email: string | null;
  image: string | null;
  role: UserRole;
  regionId: number | null;
}

interface AuthContextValue {
  firebaseUser: FirebaseUser | null;
  profile: AppProfile | null;
  loading: boolean;
  signInEmail: (email: string, password: string) => Promise<void>;
  signUpEmail: (name: string, email: string, password: string) => Promise<void>;
  signInGoogle: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [profile, setProfile] = useState<AppProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const patched = useRef(false);

  // Patch fetch once so /api/* calls carry the current ID token.
  useEffect(() => {
    if (patched.current) return;
    patched.current = true;
    const original = window.fetch.bind(window);
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      if (url.startsWith("/api") && auth.currentUser) {
        const token = await auth.currentUser.getIdToken();
        const headers = new Headers(init?.headers);
        headers.set("Authorization", `Bearer ${token}`);
        init = { ...init, headers };
      }
      return original(input, init);
    };
  }, []);

  useEffect(() => {
    return onAuthStateChanged(auth, async (user) => {
      setFirebaseUser(user);
      if (!user) {
        setProfile(null);
        setLoading(false);
        return;
      }
      try {
        // getIdToken ensures the fetch patch has a token; /api/auth/me -> api-gateway /auth/me
        await user.getIdToken();
        const res = await fetch("/api/auth/me");
        setProfile(res.ok ? ((await res.json()) as AppProfile) : null);
      } catch {
        setProfile(null);
      } finally {
        setLoading(false);
      }
    });
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    firebaseUser,
    profile,
    loading,
    signInEmail: async (email, password) => {
      await signInWithEmailAndPassword(auth, email, password);
    },
    signUpEmail: async (name, email, password) => {
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      try {
        if (name) await updateProfile(cred.user, { displayName: name });
        // Explicitly provision the Postgres profile and WAIT for it — don't rely on
        // the onAuthStateChanged side-effect, which is fire-and-forget and would leave
        // a Firebase account with no DB row if it failed. Force-refresh so the token
        // carries the freshly-set displayName as the `name` claim.
        const token = await cred.user.getIdToken(true);
        const res = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error(`profile provisioning failed (${res.status})`);
        }
      } catch (err) {
        // Roll back the orphaned Firebase account so the email is free to retry,
        // instead of getting stuck on "email-already-in-use" with no DB profile.
        await cred.user.delete().catch(() => signOut(auth));
        throw err;
      }
    },
    signInGoogle: async () => {
      try {
        await signInWithPopup(auth, googleProvider);
      } catch (error) {
        console.error("Google login error:", error);
        alert(`${error.code}\n${error.message}`);
      }
    },
    resetPassword: async (email) => {
      await sendPasswordResetEmail(auth, email);
    },
    logout: async () => {
      await signOut(auth);
    },
  }), [firebaseUser, profile, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within <AuthProvider>");
  return ctx;
}
