"use client";

import { ReactNode, useEffect } from "react";
import { cn } from "@/lib/utils";

/* Wrapper transisi halaman: memainkan animasi enter saat mount dan
   membersihkan state exit yang ditinggalkan TransitionLink dari halaman
   sebelumnya. Pasangan dari .page-transition / .page-exiting di globals.css. */
export function PageTransition({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  useEffect(() => {
    document.documentElement.classList.remove("page-exiting");
  }, []);

  return <div className={cn("page-transition", className)}>{children}</div>;
}
