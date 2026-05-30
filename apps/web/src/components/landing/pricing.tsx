import Link from "next/link";
import { Check } from "lucide-react";

const SECTION_TITLE = "{PRICING_SECTION_TITLE}";
const SECTION_SUBTITLE = "{PRICING_SECTION_SUBTITLE}";

const TIERS = [
  {
    name: "{TIER_1_NAME}",
    price: "{TIER_1_PRICE}",
    period: "{TIER_1_PERIOD}",
    description: "{TIER_1_DESC}",
    features: ["{TIER_1_F1}", "{TIER_1_F2}", "{TIER_1_F3}", "{TIER_1_F4}"],
    cta: "Mulai Gratis",
    href: "/register",
    highlight: false,
  },
  {
    name: "{TIER_2_NAME}",
    price: "{TIER_2_PRICE}",
    period: "{TIER_2_PERIOD}",
    description: "{TIER_2_DESC}",
    features: ["{TIER_2_F1}", "{TIER_2_F2}", "{TIER_2_F3}", "{TIER_2_F4}", "{TIER_2_F5}"],
    cta: "Coba Pro",
    href: "/register",
    highlight: true, // recommended
  },
  {
    name: "{TIER_3_NAME}",
    price: "{TIER_3_PRICE}",
    period: "{TIER_3_PERIOD}",
    description: "{TIER_3_DESC}",
    features: ["{TIER_3_F1}", "{TIER_3_F2}", "{TIER_3_F3}", "{TIER_3_F4}", "{TIER_3_F5}"],
    cta: "Hubungi Sales",
    href: "#contact",
    highlight: false,
  },
];

export function LandingPricing() {
  return (
    <section id="pricing" className="py-20 px-4 bg-muted/30 border-y">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-3 tracking-tight">{SECTION_TITLE}</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">{SECTION_SUBTITLE}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={
                tier.highlight
                  ? "relative bg-card border-2 border-primary rounded-xl p-6 shadow-lg flex flex-col"
                  : "bg-card border rounded-xl p-6 flex flex-col"
              }
            >
              {tier.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold text-gold-foreground text-xs font-semibold px-3 py-1 rounded-full">
                  Recommended
                </span>
              )}
              <h3 className="font-bold text-lg">{tier.name}</h3>
              <p className="text-sm text-muted-foreground mt-1 mb-4">{tier.description}</p>
              <div className="mb-5">
                <span className="text-4xl font-bold">{tier.price}</span>
                {tier.period && (
                  <span className="text-sm text-muted-foreground ml-1">/{tier.period}</span>
                )}
              </div>
              <ul className="space-y-2.5 mb-6 flex-1">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={tier.href}
                className={
                  tier.highlight
                    ? "bg-primary text-primary-foreground px-4 py-2.5 rounded-lg font-medium hover:bg-primary/90 transition-colors text-center text-sm"
                    : "border border-border px-4 py-2.5 rounded-lg font-medium hover:bg-muted transition-colors text-center text-sm"
                }
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
