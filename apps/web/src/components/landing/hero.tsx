import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

const BRAND_NAME = "{BRAND_NAME}";
const HEADLINE = "{HEADLINE}";
const TAGLINE = "{TAGLINE}";
const BADGE = "{HERO_BADGE}";

export function LandingHero() {
  return (
    <section className="relative overflow-hidden py-20 md:py-28 px-4">
      {/* Subtle gold radial accent in background */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-30"
        style={{
          background:
            "radial-gradient(60% 50% at 80% 0%, hsl(var(--brand-gold) / 0.18), transparent 60%), radial-gradient(60% 50% at 20% 0%, hsl(var(--primary) / 0.12), transparent 60%)",
        }}
      />
      <div className="max-w-4xl mx-auto text-center">
        <Image
          src="/logo.svg"
          alt={BRAND_NAME}
          width={128}
          height={128}
          priority
          className="mx-auto mb-8 drop-shadow-sm"
        />

        <div className="inline-flex items-center gap-2 bg-gold/15 text-gold-foreground/90 px-3 py-1 rounded-full text-sm font-medium mb-6 border border-gold/20">
          <Sparkles className="h-4 w-4 text-gold" />
          {BADGE}
        </div>

        <h1 className="text-balance text-4xl sm:text-5xl md:text-6xl font-bold text-foreground mb-5 leading-tight tracking-tight">
          {HEADLINE}
        </h1>

        <p className="text-balance text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
          {TAGLINE}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors w-full sm:w-auto justify-center"
          >
            Mulai Sekarang
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 border border-border px-6 py-3 rounded-lg font-medium hover:bg-muted transition-colors w-full sm:w-auto justify-center"
          >
            Masuk Dashboard
          </Link>
        </div>
      </div>
    </section>
  );
}
