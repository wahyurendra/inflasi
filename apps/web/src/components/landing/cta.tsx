import Link from "next/link";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

const BRAND_NAME = "{BRAND_NAME}";
const TITLE = "{CTA_TITLE}";
const SUBTITLE = "{CTA_SUBTITLE}";

export function LandingCta() {
  return (
    <section className="relative overflow-hidden py-16 px-4 bg-primary text-primary-foreground">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-30"
        style={{
          background:
            "radial-gradient(60% 80% at 90% 50%, hsl(var(--brand-gold) / 0.35), transparent 70%)",
        }}
      />
      <div className="relative max-w-3xl mx-auto text-center">
        <Image
          src="/logo.svg"
          alt={BRAND_NAME}
          width={64}
          height={64}
          className="mx-auto mb-5 drop-shadow"
        />
        <h2 className="text-3xl font-bold mb-3 tracking-tight">{TITLE}</h2>
        <p className="text-primary-foreground/80 mb-8 max-w-xl mx-auto">{SUBTITLE}</p>
        <Link
          href="/register"
          className="inline-flex items-center gap-2 bg-gold text-gold-foreground px-6 py-3 rounded-lg font-semibold hover:bg-gold/90 transition-colors"
        >
          Daftar Sekarang
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
