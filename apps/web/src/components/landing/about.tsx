import Image from "next/image";
import { CheckCircle2 } from "lucide-react";

const BRAND_NAME = "{BRAND_NAME}";
const TITLE = "{ABOUT_TITLE}";
const PARAGRAPH_1 = "{ABOUT_PARAGRAPH_1}";
const PARAGRAPH_2 = "{ABOUT_PARAGRAPH_2}";
const BULLETS = [
  "{ABOUT_BULLET_1}",
  "{ABOUT_BULLET_2}",
  "{ABOUT_BULLET_3}",
];

export function LandingAbout() {
  return (
    <section id="about" className="py-20 px-4 bg-muted/30 border-y">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-16 items-center">
        <div>
          <p className="text-sm font-semibold text-gold mb-3 uppercase tracking-wider">
            Tentang Kami
          </p>
          <h2 className="text-3xl font-bold mb-5 tracking-tight">{TITLE}</h2>
          <p className="text-muted-foreground mb-4 leading-relaxed">{PARAGRAPH_1}</p>
          <p className="text-muted-foreground mb-6 leading-relaxed">{PARAGRAPH_2}</p>
          <ul className="space-y-3">
            {BULLETS.map((b) => (
              <li key={b} className="flex items-start gap-3 text-sm">
                <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="relative flex items-center justify-center">
          <div
            aria-hidden
            className="absolute inset-0 -z-10 rounded-full blur-3xl opacity-30"
            style={{
              background:
                "radial-gradient(closest-side, hsl(var(--primary) / 0.35), transparent), radial-gradient(closest-side at 70% 70%, hsl(var(--brand-gold) / 0.30), transparent)",
            }}
          />
          <Image
            src="/logo.svg"
            alt={BRAND_NAME}
            width={280}
            height={280}
            className="drop-shadow-xl"
          />
        </div>
      </div>
    </section>
  );
}
