import {
  BarChart3,
  MapPin,
  Users,
  Bell,
  Brain,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

const SECTION_TITLE = "{FEATURES_SECTION_TITLE}";
const SECTION_SUBTITLE = "{FEATURES_SECTION_SUBTITLE}";

const FEATURES: { icon: LucideIcon; title: string; desc: string }[] = [
  { icon: BarChart3, title: "{FEATURE_1_TITLE}", desc: "{FEATURE_1_DESC}" },
  { icon: MapPin,    title: "{FEATURE_2_TITLE}", desc: "{FEATURE_2_DESC}" },
  { icon: Users,     title: "{FEATURE_3_TITLE}", desc: "{FEATURE_3_DESC}" },
  { icon: Bell,      title: "{FEATURE_4_TITLE}", desc: "{FEATURE_4_DESC}" },
  { icon: Brain,     title: "{FEATURE_5_TITLE}", desc: "{FEATURE_5_DESC}" },
  { icon: TrendingUp,title: "{FEATURE_6_TITLE}", desc: "{FEATURE_6_DESC}" },
];

export function LandingFeatures() {
  return (
    <section id="features" className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-3 tracking-tight">{SECTION_TITLE}</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">{SECTION_SUBTITLE}</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-card rounded-xl border p-6 hover:shadow-md hover:border-primary/40 transition-all"
            >
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <f.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-1.5">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
