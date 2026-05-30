"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Providers } from "@/components/providers";
import { useAuth } from "@/hooks/use-auth";

function RootGateway() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (isAuthenticated) {
      router.replace("/beranda");
    } else {
      router.replace("/welcome");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex h-screen items-center justify-center text-muted-foreground text-sm">
      Memuat...
    </div>
  );
}

export default function RootPage() {
  return (
    <Providers>
      <RootGateway />
    </Providers>
  );
}
