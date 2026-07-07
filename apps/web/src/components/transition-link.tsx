"use client";

import { ComponentProps, MouseEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const EXIT_MS = 200;

/* Link yang memainkan animasi exit halaman sebelum navigasi. Halaman tujuan
   harus dibungkus PageTransition agar state exit dibersihkan dan animasi
   enter dimainkan. Klik termodifikasi (tab baru dsb.), anchor hash, dan
   preferensi reduced-motion tetap berperilaku seperti Link biasa. */
export function TransitionLink({ href, onClick, ...props }: ComponentProps<typeof Link>) {
  const router = useRouter();

  const handleClick = (e: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (e.defaultPrevented) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || props.target === "_blank") return;

    const url = typeof href === "string" ? href : href.pathname ?? "";
    if (!url || url.startsWith("#")) return;

    e.preventDefault();

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      router.push(url);
      return;
    }

    document.documentElement.classList.add("page-exiting");
    window.setTimeout(() => {
      router.push(url);
      // Jaring pengaman: bila navigasi gagal / halaman tujuan tidak memakai
      // PageTransition, jangan biarkan halaman lama tersembunyi selamanya.
      window.setTimeout(() => {
        document.documentElement.classList.remove("page-exiting");
      }, 1500);
    }, EXIT_MS);
  };

  return <Link href={href} {...props} onClick={handleClick} />;
}
